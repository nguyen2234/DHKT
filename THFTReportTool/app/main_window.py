"""
Main Window for THFT Report Tool.
Provides a modern Windows GUI using PySide6 with multi-threading, interactive preview,
manual tag toggling, and fast clipboard/export capabilities.
"""

import os
import sys
import datetime
import subprocess
import logging
from typing import Dict, Any, Optional, List

from PySide6.QtCore import Qt, QThread, Signal, Slot, QDate
from PySide6.QtGui import QIcon, QFont, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QFileDialog, QMessageBox, QProgressBar, QGroupBox, QSplitter,
    QFrame, QCheckBox, QAbstractItemView, QDateEdit
)

from .config import load_config, save_config, get_base_dir
from .models import ReportDataset, CenterReport, EmployeeFT
from .excel_reader import ExcelReader, ExcelValidationError, ExcelUncalculatedError
from .report_processor import ReportProcessor
from .report_exporter import ReportExporter
from .clipboard_manager import ClipboardManager

logger = logging.getLogger(__name__)


class ExcelLoadWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, reader: ExcelReader, file_path: str):
        super().__init__()
        self.reader = reader
        self.file_path = file_path

    def run(self):
        try:
            dataset = self.reader.read_report_file(
                self.file_path,
                progress_callback=lambda pct, msg: self.progress.emit(pct, msg)
            )
            self.finished.emit(dataset)
        except ExcelValidationError as e:
            self.error.emit(str(e))
        except ExcelUncalculatedError as e:
            self.error.emit(str(e))
        except Exception as e:
            logger.exception("Unexpected error reading Excel")
            self.error.emit(f"Lỗi không xác định khi đọc file: {str(e)}")


class ExcelExportWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, exporter: ReportExporter, dataset: ReportDataset, notifications: Dict[str, str], output_dir: str, position_filter: str = "ALL"):
        super().__init__()
        self.exporter = exporter
        self.dataset = dataset
        self.notifications = notifications
        self.output_dir = output_dir
        self.position_filter = position_filter

    def run(self):
        try:
            out_file = self.exporter.export_excel(
                self.dataset,
                self.notifications,
                output_dir=self.output_dir,
                position_filter=self.position_filter,
                progress_callback=lambda pct, msg: self.progress.emit(pct, msg)
            )
            self.finished.emit(out_file)
        except Exception as e:
            logger.exception("Export error")
            self.error.emit(f"Lỗi khi xuất file Excel: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.reader = ExcelReader(self.config)
        self.processor = ReportProcessor(self.config)
        self.exporter = ReportExporter(self.config)

        self.dataset: Optional[ReportDataset] = None
        self.last_exported_file: Optional[str] = None
        self.current_center_code: Optional[str] = None

        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        self.setWindowTitle("CÔNG CỤ TẠO BÁO CÁO THFT")
        self.resize(1200, 820)
        self.setMinimumSize(1000, 700)

        # Set window icon
        icon_path = os.path.join(get_base_dir(), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # 1. HEADER TITLE
        header_layout = QHBoxLayout()
        title_label = QLabel("CÔNG CỤ TẠO BÁO CÁO THFT")
        title_label.setObjectName("appTitle")
        subtitle_label = QLabel("Hệ thống tự động hóa báo cáo điều hành WO UT1 & Tag tên FT")
        subtitle_label.setObjectName("appSubtitle")
        title_box = QVBoxLayout()
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # 2. TOP SECTION: FILE DỮ LIỆU
        file_group = QGroupBox("FILE DỮ LIỆU BÁO CÁO")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(8)

        file_row = QHBoxLayout()
        self.txt_file_path = QLineEdit()
        self.txt_file_path.setPlaceholderText("Chọn file Excel ĐH WO UT1 (*.xlsx)...")
        self.txt_file_path.setReadOnly(True)

        self.btn_browse = QPushButton("📁 CHỌN FILE")
        self.btn_browse.setObjectName("btnPrimary")
        self.btn_browse.clicked.connect(self._browse_file)

        self.btn_load = QPushButton("🚀 ĐỌC DỮ LIỆU")
        self.btn_load.setObjectName("btnSuccess")
        self.btn_load.setEnabled(False)
        self.btn_load.clicked.connect(self._load_file)

        file_row.addWidget(self.txt_file_path, stretch=1)
        file_row.addWidget(self.btn_browse)
        file_row.addWidget(self.btn_load)
        file_layout.addLayout(file_row)

        # Metadata cards row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(10)
        self.lbl_meta_name = QLabel("Tên file: -")
        self.lbl_meta_sheet = QLabel("Sheet: -")
        self.lbl_meta_ft = QLabel("Số FT: 0")
        self.lbl_meta_centers = QLabel("Số Trung tâm: 0")
        self.lbl_meta_date = QLabel("Ngày dữ liệu: -")
        self.lbl_meta_tagged = QLabel("Tổng Tag: 0")
        self.lbl_meta_tagged.setObjectName("lblMetaTagged")

        for lbl in (self.lbl_meta_name, self.lbl_meta_sheet, self.lbl_meta_ft,
                    self.lbl_meta_centers, self.lbl_meta_date, self.lbl_meta_tagged):
            lbl.setObjectName("metaBadge")
            meta_row.addWidget(lbl)
        meta_row.addStretch()
        file_layout.addLayout(meta_row)

        main_layout.addWidget(file_group)

        # 3. MIDDLE SECTION: CÀI ĐẶT THÔNG BÁO & DANH SÁCH HUYỆN
        config_group = QGroupBox("CÀI ĐẶT THÔNG BÁO VÀ CHỌN TRUNG TÂM HUYỆN")
        config_layout = QGridLayout(config_group)
        config_layout.setSpacing(10)

        # Col 0, 1: Controls
        config_layout.addWidget(QLabel("Ngày báo cáo:"), 0, 0)
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("dd/MM/yyyy")
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.dateChanged.connect(self._on_date_changed)
        config_layout.addWidget(self.date_picker, 0, 1)

        config_layout.addWidget(QLabel("Hạn hoàn thành:"), 1, 0)
        self.txt_deadline = QLineEdit("05/10")
        self.txt_deadline.textChanged.connect(self._update_preview)
        config_layout.addWidget(self.txt_deadline, 1, 1)

        config_layout.addWidget(QLabel("Giờ họp ngày mai:"), 2, 0)
        self.txt_meeting = QLineEdit("06:30")
        self.txt_meeting.textChanged.connect(self._update_preview)
        config_layout.addWidget(self.txt_meeting, 2, 1)

        config_layout.addWidget(QLabel("Định dạng Tag:"), 3, 0)
        self.cmb_tag_format = QComboBox()
        self.cmb_tag_format.addItem("@Họ và tên", "name")
        self.cmb_tag_format.addItem("@HỌ VÀ TÊN (In hoa)", "name_upper")
        self.cmb_tag_format.addItem("@Username", "username")
        self.cmb_tag_format.addItem("@FT Username", "ft_username")
        self.cmb_tag_format.addItem("@Username VịTrí MãHuyện", "user_pos_center")
        self.cmb_tag_format.currentIndexChanged.connect(self._update_preview)
        config_layout.addWidget(self.cmb_tag_format, 3, 1)

        # Position filter (Cột D)
        config_layout.addWidget(QLabel("Lọc vị trí (Cột D):"), 4, 0)
        self.cmb_position_filter = QComboBox()
        self.cmb_position_filter.addItem("Tất cả vị trí (Tất cả)", "ALL")
        self.cmb_position_filter.addItem("Nhân viên DM (NV DM)", "NV DM")
        self.cmb_position_filter.addItem("Nhân viên nhà trạm (NV NHÀ TRẠM)", "NV NHÀ TRẠM")
        self.cmb_position_filter.currentIndexChanged.connect(self._on_position_filter_changed)
        config_layout.addWidget(self.cmb_position_filter, 4, 1)

        # Center selector
        config_layout.addWidget(QLabel("Trung tâm / Huyện:"), 5, 0)
        self.cmb_center = QComboBox()
        self.cmb_center.addItem("--- Chọn trung tâm huyện ---", "")
        self.cmb_center.currentIndexChanged.connect(self._on_center_changed)
        config_layout.addWidget(self.cmb_center, 5, 1)

        # Col 2: Notification Template & Editor
        editor_layout = QVBoxLayout()
        editor_header = QHBoxLayout()
        editor_header.addWidget(QLabel("Mẫu nội dung thông báo (cho phép sửa trực tiếp):"))
        self.btn_refresh_preview = QPushButton("🔄 CẬP NHẬT PREVIEW")
        self.btn_refresh_preview.setObjectName("btnSecondary")
        self.btn_refresh_preview.clicked.connect(self._update_preview)
        editor_header.addWidget(self.btn_refresh_preview)
        editor_layout.addLayout(editor_header)

        self.txt_notice_template = QTextEdit()
        default_tpl = self.config.get("notification", {}).get(
            "template",
            "FT tồn quá hạn wo đến ngày hôm nay {NGAY_THANG}, khẩn trương hoàn thành trước {HAN_HOAN_THANH}. FT không có tiến độ ngày sẽ triệu tập họp vào {GIO_HOP} ngày mai\n\n{DANH_SACH_TAG}"
        )
        self.txt_notice_template.setPlainText(default_tpl)
        self.txt_notice_template.setMaximumHeight(115)
        self.txt_notice_template.textChanged.connect(self._update_preview)
        editor_layout.addWidget(self.txt_notice_template)

        config_layout.addLayout(editor_layout, 0, 2, 6, 1)
        config_layout.setColumnStretch(2, 1)

        main_layout.addWidget(config_group)

        # 4. BOTTOM SECTION: TABS (PREVIEW BÁO CÁO & DANH SÁCH KIỂM TRA TAG)
        self.tabs = QTabWidget()

        # Tab 1: Preview Báo Cáo
        tab_preview = QWidget()
        preview_layout = QVBoxLayout(tab_preview)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        preview_layout.setSpacing(8)

        # Preview Notification Box
        self.lbl_preview_notice = QLabel("Nội dung thông báo và danh sách TAG sẽ hiển thị tại đây sau khi chọn huyện.")
        self.lbl_preview_notice.setWordWrap(True)
        self.lbl_preview_notice.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_preview_notice.setObjectName("noticePreviewCard")
        preview_layout.addWidget(self.lbl_preview_notice)

        # Preview Table
        self.table_preview = QTableWidget()
        self.table_preview.setAlternatingRowColors(True)
        self.table_preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_preview.setSelectionBehavior(QAbstractItemView.SelectRows)
        preview_layout.addWidget(self.table_preview)

        self.tabs.addTab(tab_preview, "📄 Xem trước Báo Cáo Huyện")

        # Tab 2: Danh Sách Kiểm Tra Nhân Viên Bị Tag
        tab_tag_audit = QWidget()
        audit_layout = QVBoxLayout(tab_tag_audit)
        audit_layout.setContentsMargins(8, 8, 8, 8)
        audit_layout.setSpacing(8)

        audit_bar = QHBoxLayout()
        self.chk_filter_tagged = QCheckBox("Chỉ hiển thị nhân viên được TAG (Q > 0 và T ≤ 0)")
        self.chk_filter_tagged.setChecked(False)
        self.chk_filter_tagged.toggled.connect(self._render_tag_audit_table)
        audit_bar.addWidget(self.chk_filter_tagged)

        self.chk_filter_current_center = QCheckBox("Chỉ hiển thị huyện đang chọn")
        self.chk_filter_current_center.setChecked(False)
        self.chk_filter_current_center.toggled.connect(self._render_tag_audit_table)
        audit_bar.addWidget(self.chk_filter_current_center)

        audit_bar.addStretch()
        self.btn_reset_tags = QPushButton("↺ Khôi phục Tag tự động")
        self.btn_reset_tags.setObjectName("btnSecondary")
        self.btn_reset_tags.clicked.connect(self._reset_tags)
        audit_bar.addWidget(self.btn_reset_tags)

        audit_layout.addLayout(audit_bar)

        self.table_tag_audit = QTableWidget()
        self.table_tag_audit.setAlternatingRowColors(True)
        self.table_tag_audit.setSelectionBehavior(QAbstractItemView.SelectRows)
        audit_layout.addWidget(self.table_tag_audit)

        self.tabs.addTab(tab_tag_audit, "👥 Bảng Kiểm Tra & Tùy Chọn TAG Nhân Viên")

        # Tab 3: Danh Sách WO Quá Hạn Theo Huyện
        tab_wo = QWidget()
        wo_layout = QVBoxLayout(tab_wo)
        wo_layout.setContentsMargins(8, 8, 8, 8)
        wo_layout.setSpacing(8)

        wo_bar = QHBoxLayout()
        self.lbl_wo_info = QLabel("Chọn một huyện để xem danh sách WO quá hạn tương ứng.")
        self.lbl_wo_info.setStyleSheet("font-weight: bold; color: #1F4E78; font-size: 13px;")
        wo_bar.addWidget(self.lbl_wo_info)
        wo_bar.addStretch()

        self.btn_copy_wo_tab = QPushButton("📋 COPY WO QUÁ HẠN")
        self.btn_copy_wo_tab.setObjectName("btnActionWarning")
        self.btn_copy_wo_tab.setEnabled(False)
        self.btn_copy_wo_tab.clicked.connect(self._copy_wo_only)
        wo_bar.addWidget(self.btn_copy_wo_tab)

        wo_layout.addLayout(wo_bar)

        self.table_wo = QTableWidget()
        self.table_wo.setAlternatingRowColors(True)
        self.table_wo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_wo.setSelectionBehavior(QAbstractItemView.SelectRows)
        wo_layout.addWidget(self.table_wo)

        self.tabs.addTab(tab_wo, "⚠️ Danh Sách WO Quá Hạn")

        # Tab 4: Danh Sách WO Tồn Chưa Quá Hạn Theo Huyện
        tab_pending_wo = QWidget()
        pending_wo_layout = QVBoxLayout(tab_pending_wo)
        pending_wo_layout.setContentsMargins(8, 8, 8, 8)
        pending_wo_layout.setSpacing(8)

        pending_wo_bar = QHBoxLayout()
        self.lbl_pending_wo_info = QLabel("Chọn một huyện để xem danh sách WO tồn chưa quá hạn tương ứng.")
        self.lbl_pending_wo_info.setStyleSheet("font-weight: bold; color: #135E48; font-size: 13px;")
        pending_wo_bar.addWidget(self.lbl_pending_wo_info)
        pending_wo_bar.addStretch()

        self.btn_copy_pending_wo_tab = QPushButton("📋 COPY WO CHƯA QUÁ HẠN")
        self.btn_copy_pending_wo_tab.setObjectName("btnActionSuccess")
        self.btn_copy_pending_wo_tab.setEnabled(False)
        self.btn_copy_pending_wo_tab.clicked.connect(self._copy_pending_wo_only)
        pending_wo_bar.addWidget(self.btn_copy_pending_wo_tab)

        pending_wo_layout.addLayout(pending_wo_bar)

        self.table_pending_wo = QTableWidget()
        self.table_pending_wo.setAlternatingRowColors(True)
        self.table_pending_wo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_pending_wo.setSelectionBehavior(QAbstractItemView.SelectRows)
        pending_wo_layout.addWidget(self.table_pending_wo)

        self.tabs.addTab(tab_pending_wo, "⏳ WO Tồn Chưa Quá Hạn")

        main_layout.addWidget(self.tabs, stretch=1)

        # 5. ACTION BAR & PROGRESS
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)

        self.btn_copy_full = QPushButton("📋 COPY BÁO CÁO HUYỆN")
        self.btn_copy_full.setObjectName("btnActionPrimary")
        self.btn_copy_full.setEnabled(False)
        self.btn_copy_full.clicked.connect(self._copy_full_report)

        self.btn_copy_notice = QPushButton("💬 COPY THÔNG BÁO + TAG")
        self.btn_copy_notice.setObjectName("btnActionSecondary")
        self.btn_copy_notice.setEnabled(False)
        self.btn_copy_notice.clicked.connect(self._copy_notice_only)

        self.btn_copy_wo = QPushButton("⚠️ COPY WO QUÁ HẠN")
        self.btn_copy_wo.setObjectName("btnActionWarning")
        self.btn_copy_wo.setEnabled(False)
        self.btn_copy_wo.clicked.connect(self._copy_wo_only)

        self.btn_copy_pending_wo = QPushButton("⏳ COPY WO CHƯA QUÁ HẠN")
        self.btn_copy_pending_wo.setObjectName("btnActionSuccess")
        self.btn_copy_pending_wo.setEnabled(False)
        self.btn_copy_pending_wo.clicked.connect(self._copy_pending_wo_only)

        self.btn_export = QPushButton("📊 XUẤT EXCEL TẤT CẢ HUYỆN")
        self.btn_export.setObjectName("btnExport")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._export_excel)

        self.btn_open_folder = QPushButton("📂 MỞ THƯ MỤC XUẤT")
        self.btn_open_folder.setObjectName("btnSecondary")
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.clicked.connect(self._open_export_folder)

        action_layout.addWidget(self.btn_copy_full)
        action_layout.addWidget(self.btn_copy_notice)
        action_layout.addWidget(self.btn_copy_wo)
        action_layout.addWidget(self.btn_copy_pending_wo)
        action_layout.addWidget(self.btn_export)
        action_layout.addWidget(self.btn_open_folder)
        main_layout.addLayout(action_layout)

        # Progress bar & Status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        main_layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Sẵn sàng. Vui lòng chọn file Excel ĐH WO UT1.")
        self.lbl_status.setObjectName("statusLabel")
        main_layout.addWidget(self.lbl_status)

        # Auto-detect sample file if present
        self._check_default_sample()

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                color: #2D3748;
            }
            #appTitle {
                font-size: 19px;
                font-weight: bold;
                color: #1A365D;
            }
            #appSubtitle {
                font-size: 12px;
                color: #718096;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #CBD5E0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 14px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: #2B6CB0;
            }
            QLineEdit, QDateEdit, QComboBox, QTextEdit {
                border: 1px solid #CBD5E0;
                border-radius: 4px;
                padding: 5px 8px;
                background-color: #FFFFFF;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 1px solid #3182CE;
            }
            #metaBadge {
                background-color: #EDF2F7;
                padding: 4px 10px;
                border-radius: 4px;
                font-weight: 500;
                color: #4A5568;
            }
            #lblMetaTagged {
                background-color: #FED7D7;
                color: #C53030;
                font-weight: bold;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QPushButton {
                border-radius: 4px;
                padding: 7px 16px;
                font-weight: bold;
            }
            #btnPrimary {
                background-color: #3182CE;
                color: white;
                border: none;
            }
            #btnPrimary:hover {
                background-color: #2B6CB0;
            }
            #btnSuccess {
                background-color: #38A169;
                color: white;
                border: none;
            }
            #btnSuccess:hover {
                background-color: #2F855A;
            }
            #btnSecondary {
                background-color: #EDF2F7;
                color: #4A5568;
                border: 1px solid #CBD5E0;
            }
            #btnSecondary:hover {
                background-color: #E2E8F0;
            }
            #btnActionPrimary {
                background-color: #2B6CB0;
                color: white;
                padding: 10px 18px;
                font-size: 13px;
                border: none;
            }
            #btnActionPrimary:hover {
                background-color: #2C5282;
            }
            #btnActionSecondary {
                background-color: #319795;
                color: white;
                padding: 10px 18px;
                font-size: 13px;
                border: none;
            }
            #btnActionSecondary:hover {
                background-color: #285E61;
            }
            #btnActionWarning {
                background-color: #DD6B20;
                color: white;
                padding: 10px 18px;
                font-size: 13px;
                border: none;
            }
            #btnActionWarning:hover {
                background-color: #C05621;
            }
            #btnActionSuccess {
                background-color: #2F855A;
                color: white;
                padding: 10px 18px;
                font-size: 13px;
                border: none;
            }
            #btnActionSuccess:hover {
                background-color: #22543D;
            }
            #btnExport {
                background-color: #D69E2E;
                color: white;
                padding: 10px 18px;
                font-size: 13px;
                border: none;
            }
            #btnExport:hover {
                background-color: #B7791F;
            }
            #noticePreviewCard {
                background-color: #FFFBEB;
                border: 1px solid #F6E05E;
                border-radius: 6px;
                padding: 12px 14px;
                color: #744210;
                font-size: 13px;
                line-height: 1.4;
            }
            QTableWidget {
                border: 1px solid #E2E8F0;
                gridline-color: #EDF2F7;
                border-radius: 4px;
                background-color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #F7FAFC;
                color: #4A5568;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #E2E8F0;
            }
            QProgressBar {
                border: 1px solid #CBD5E0;
                border-radius: 4px;
                text-align: center;
                height: 16px;
            }
            QProgressBar::chunk {
                background-color: #38A169;
                border-radius: 3px;
            }
            #statusLabel {
                font-size: 12px;
                color: #718096;
            }
        """)

    def _check_default_sample(self):
        """Checks if sample file exists in workspace to conveniently pre-populate."""
        base_dir = get_base_dir()
        sample_path = os.path.join(base_dir, "samples", "ĐH WO UT1 (05102026) (1).xlsx")
        if not os.path.exists(sample_path):
            sample_path = os.path.join(os.path.dirname(base_dir), "ĐH WO UT1 (05102026) (1).xlsx")

        if os.path.exists(sample_path):
            self.txt_file_path.setText(sample_path)
            self.btn_load.setEnabled(True)
            self.lbl_status.setText("Đã tìm thấy file mẫu. Bấm 'ĐỌC DỮ LIỆU' để bắt đầu.")

    def _browse_file(self):
        start_dir = os.path.dirname(self.txt_file_path.text()) if self.txt_file_path.text() else get_base_dir()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file Excel ĐH WO UT1",
            start_dir,
            "Excel Files (*.xlsx *.xlsm);;All Files (*.*)"
        )
        if file_path:
            self.txt_file_path.setText(file_path)
            self.btn_load.setEnabled(True)
            self.lbl_status.setText(f"Đã chọn: {os.path.basename(file_path)}")

    def _load_file(self):
        file_path = self.txt_file_path.text()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file Excel hợp lệ.")
            return

        self.btn_load.setEnabled(False)
        self.btn_browse.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Đang đọc dữ liệu Excel...")

        self.worker = ExcelLoadWorker(self.reader, file_path)
        self.worker.progress.connect(self._on_load_progress)
        self.worker.finished.connect(self._on_load_finished)
        self.worker.error.connect(self._on_load_error)
        self.worker.start()

    @Slot(int, str)
    def _on_load_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(msg)

    def _get_effective_dataset(self) -> Optional[ReportDataset]:
        """Returns the dataset filtered by the selected position in Column D."""
        if not self.dataset:
            return None
        pos_filter = self.cmb_position_filter.currentData() or "ALL"
        return self.dataset.get_filtered_dataset(pos_filter)

    def _update_meta_badges(self):
        eff_dataset = self._get_effective_dataset()
        if not eff_dataset:
            return
        pos_filter = self.cmb_position_filter.currentData() or "ALL"
        pos_label = ""
        if pos_filter == "NV DM":
            pos_label = " (NV DM)"
        elif pos_filter == "NV NHÀ TRẠM":
            pos_label = " (Nhà trạm)"
        fname = os.path.basename(eff_dataset.file_path)
        self.lbl_meta_name.setText(f"File: {fname}")
        self.lbl_meta_sheet.setText(f"Sheet: {eff_dataset.sheet_name}")
        self.lbl_meta_ft.setText(f"Số FT: {eff_dataset.total_employees}{pos_label}")
        self.lbl_meta_centers.setText(f"Số Trung tâm: {len(eff_dataset.centers)}")
        self.lbl_meta_date.setText(f"Ngày: {eff_dataset.report_date_str}")
        self.lbl_meta_tagged.setText(f"Tổng Tag: {eff_dataset.total_tagged}")

    def _update_center_list(self):
        eff_dataset = self._get_effective_dataset()
        if not eff_dataset:
            return
        prev_code = self.cmb_center.currentData()
        self.cmb_center.blockSignals(True)
        self.cmb_center.clear()
        self.cmb_center.addItem("--- Chọn trung tâm huyện ---", "")

        for code, center in sorted(eff_dataset.centers.items(), key=lambda x: x[0]):
            wo_badge = f", {len(center.work_orders)} WO QH" if len(center.work_orders) > 0 else ""
            p_badge = f", {len(center.pending_work_orders)} WO tồn" if len(center.pending_work_orders) > 0 else ""
            label = f"{code} - {center.center_name} ({center.total_count} FT, {center.tagged_count} Tag{wo_badge}{p_badge})"
            self.cmb_center.addItem(label, code)

        self.cmb_center.blockSignals(False)

        # Restore previous selection if possible, otherwise default to index 1
        index = self.cmb_center.findData(prev_code)
        if index > 0:
            self.cmb_center.setCurrentIndex(index)
        elif self.cmb_center.count() > 1:
            self.cmb_center.setCurrentIndex(1)

    def _on_position_filter_changed(self):
        self._update_meta_badges()
        self._update_center_list()
        self._update_preview()
        self._render_tag_audit_table()
        pos_name = self.cmb_position_filter.currentText()
        eff = self._get_effective_dataset()
        count = eff.total_employees if eff else 0
        self.lbl_status.setText(f"Đã lọc theo: {pos_name} ({count} nhân viên)")

    @Slot(object)
    def _on_load_finished(self, dataset: ReportDataset):
        self.dataset = dataset
        self.progress_bar.setVisible(False)
        self.btn_load.setEnabled(True)
        self.btn_browse.setEnabled(True)
        self.btn_export.setEnabled(True)

        # Update date picker
        try:
            d_parts = dataset.report_date_str.split("/")
            if len(d_parts) == 3:
                qdate = QDate(int(d_parts[2]), int(d_parts[1]), int(d_parts[0]))
                self.date_picker.setDate(qdate)
        except Exception:
            pass

        self._update_meta_badges()
        self._update_center_list()
        self._render_tag_audit_table()
        self.lbl_status.setText(f"Đọc thành công {dataset.total_employees} FT thuộc {len(dataset.centers)} trung tâm.")

    @Slot(str)
    def _on_load_error(self, err_msg: str):
        self.progress_bar.setVisible(False)
        self.btn_load.setEnabled(True)
        self.btn_browse.setEnabled(True)
        self.lbl_status.setText("Lỗi khi đọc file.")
        QMessageBox.critical(self, "Lỗi cấu trúc file Excel", err_msg)

    def _on_center_changed(self):
        code = self.cmb_center.currentData()
        self.current_center_code = code if code else None

        eff_dataset = self._get_effective_dataset()
        center = eff_dataset.centers.get(self.current_center_code) if eff_dataset and self.current_center_code else None
        has_wos = (center is not None and len(center.work_orders) > 0)
        has_pending_wos = (center is not None and len(center.pending_work_orders) > 0)

        if self.current_center_code and self.dataset:
            self.btn_copy_full.setEnabled(True)
            self.btn_copy_notice.setEnabled(True)
            self.btn_copy_wo.setEnabled(has_wos)
            self.btn_copy_wo_tab.setEnabled(has_wos)
            self.btn_copy_pending_wo.setEnabled(has_pending_wos)
            self.btn_copy_pending_wo_tab.setEnabled(has_pending_wos)
        else:
            self.btn_copy_full.setEnabled(False)
            self.btn_copy_notice.setEnabled(False)
            self.btn_copy_wo.setEnabled(False)
            self.btn_copy_wo_tab.setEnabled(False)
            self.btn_copy_pending_wo.setEnabled(False)
            self.btn_copy_pending_wo_tab.setEnabled(False)

        self._update_preview()
        if self.chk_filter_current_center.isChecked():
            self._render_tag_audit_table()

    def _on_date_changed(self, qdate: QDate):
        if self.dataset:
            self.dataset.report_date_str = qdate.toString("dd/MM/yyyy")
            self.dataset.day_month_str = f"{qdate.day()}/{qdate.month()}"
            self.lbl_meta_date.setText(f"Ngày: {self.dataset.report_date_str}")
            self._update_preview()

    def _update_preview(self):
        eff_dataset = self._get_effective_dataset()
        if not eff_dataset or not self.current_center_code:
            self.lbl_preview_notice.setText("Vui lòng chọn một trung tâm huyện để xem báo cáo.")
            self.table_preview.setRowCount(0)
            self._render_wo_table(None)
            self._render_pending_wo_table(None)
            return

        center = eff_dataset.centers.get(self.current_center_code)
        if not center or len(center.employees) == 0:
            pos_name = self.cmb_position_filter.currentText()
            self.lbl_preview_notice.setText(f"Trung tâm {self.current_center_code} không có nhân sự thuộc bộ lọc '{pos_name}'.")
            self.table_preview.setRowCount(0)
            self._render_wo_table(center)
            self._render_pending_wo_table(center)
            return

        tag_format = self.cmb_tag_format.currentData() or "name"
        deadline = self.txt_deadline.text().strip()
        meeting = self.txt_meeting.text().strip()
        template = self.txt_notice_template.toPlainText()

        # Generate notification for THIS CENTER ONLY
        notice_text = self.processor.generate_center_notification(
            center=center,
            template=template,
            report_date_str=eff_dataset.report_date_str,
            day_month_str=eff_dataset.day_month_str,
            deadline_str=deadline,
            meeting_time_str=meeting,
            tag_format=tag_format
        )
        self.lbl_preview_notice.setText(notice_text)

        # Render Table Preview
        self._render_preview_table(center)
        # Render WO Tables
        self._render_wo_table(center)
        self._render_pending_wo_table(center)

    def _render_preview_table(self, center: CenterReport):
        headers = [
            "FT", "Tên FT", "TTH", "Vị trí",
            "ICMS_BD_NT(Tồn)", "ICMS_BD_NT(QH)", "ICMS_BD_NT(QH30)",
            "ICMS_BD_THC(Tồn)", "ICMS_BD_THC(QH)", "ICMS_BD_THC(QH30)",
            "ICMS_TT_TC(Tồn)", "ICMS_TT_TC(QH)", "ICMS_TT_TC(QH30)",
            "Báo_Hỏng(Tồn)", "Báo_Hỏng(QH)", "Báo_Hỏng(QH30)",
            "Tổng Tồn (Q)", "Tổng QH (R)", "Tổng QH30 (S)", "Thực Hiện Ngày (T)"
        ]

        self.table_preview.clear()
        self.table_preview.setColumnCount(len(headers))
        self.table_preview.setHorizontalHeaderLabels(headers)
        self.table_preview.setRowCount(len(center.employees) + 1) # +1 for subtotal

        for r_idx, emp in enumerate(center.employees):
            is_tag = emp.is_tagged

            row_data = [
                emp.username,
                emp.full_name,
                emp.center_raw,
                emp.position,
                str(emp.icms_bd_nt_ton or ""),
                str(emp.icms_bd_nt_qh or ""),
                str(emp.icms_bd_nt_qh30 or ""),
                str(emp.icms_bd_thc_ton or ""),
                str(emp.icms_bd_thc_qh or ""),
                str(emp.icms_bd_thc_qh30 or ""),
                str(emp.icms_tt_tc_ton or ""),
                str(emp.icms_tt_tc_qh or ""),
                str(emp.icms_tt_tc_qh30 or ""),
                str(emp.bao_hong_ton or ""),
                str(emp.bao_hong_qh or ""),
                str(emp.bao_hong_qh30 or ""),
                str(emp.ton or ""),
                str(emp.qua_han or ""),
                str(emp.qua_han_30 or ""),
                str(emp.thuc_hien_ngay or "")
            ]

            for c_idx, val in enumerate(row_data):
                item = QTableWidgetItem(val)

                # Alignment
                if c_idx in (0, 1, 2):
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

                # Highlight tagged rows/cells
                if is_tag and c_idx == 16: # Col Q
                    item.setForeground(QColor("#C00000"))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                elif c_idx == 0:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                self.table_preview.setItem(r_idx, c_idx, item)

        # Total row at bottom
        sub = center.get_subtotal()
        tot_idx = len(center.employees)
        tot_label = f"Tổng cộng ({center.total_count} FT - {center.tagged_count} Tag)"
        item_tot = QTableWidgetItem(tot_label)
        font = item_tot.font()
        font.setBold(True)
        item_tot.setFont(font)
        item_tot.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table_preview.setItem(tot_idx, 0, item_tot)

        tot_vals = [
            (4, sub["icms_bd_nt_ton"]), (5, sub["icms_bd_nt_qh"]), (6, sub["icms_bd_nt_qh30"]),
            (7, sub["icms_bd_thc_ton"]), (8, sub["icms_bd_thc_qh"]), (9, sub["icms_bd_thc_qh30"]),
            (10, sub["icms_tt_tc_ton"]), (11, sub["icms_tt_tc_qh"]), (12, sub["icms_tt_tc_qh30"]),
            (13, sub["bao_hong_ton"]), (14, sub["bao_hong_qh"]), (15, sub["bao_hong_qh30"]),
            (16, sub["ton"]), (17, sub["qua_han"]), (18, sub["qua_han_30"]), (19, sub["thuc_hien_ngay"])
        ]
        for col, val in tot_vals:
            item = QTableWidgetItem(str(val if val > 0 else ""))
            item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            f = item.font()
            f.setBold(True)
            item.setFont(f)
            self.table_preview.setItem(tot_idx, col, item)

        self.table_preview.resizeColumnsToContents()

    def _render_wo_table(self, center: Optional[CenterReport]):
        """Renders the table of overdue Work Orders for the selected center in Tab 3."""
        if not center or not center.work_orders:
            self.table_wo.setRowCount(0)
            c_name = center.center_name if center else "huyện này"
            self.lbl_wo_info.setText(f"Trung tâm {c_name} hiện không có WO nào quá hạn (Cột L có giá trị âm < 0).")
            self.btn_copy_wo_tab.setEnabled(False)
            self.btn_copy_wo.setEnabled(False)
            self.tabs.setTabText(2, "⚠️ WO Quá Hạn (0)")
            return

        wos = center.work_orders
        self.lbl_wo_info.setText(f"Danh sách {len(wos)} WO quá hạn thuộc trung tâm {center.center_name} ({center.center_code}):")
        self.btn_copy_wo_tab.setEnabled(True)
        self.btn_copy_wo.setEnabled(True)
        self.tabs.setTabText(2, f"⚠️ WO Quá Hạn ({len(wos)})")

        headers = [
            "STT", "Mã công việc", "Loại công việc", "Nội dung công việc",
            "Thời điểm kết thúc", "Trạng thái", "Nhân viên thực hiện",
            "Mã trạm", "FT comment", "FT mobile", "Ngày hoàn thành",
            "Ngày quá hạn", "TTH", "BKK", "Lý do BKK"
        ]

        self.table_wo.clear()
        self.table_wo.setColumnCount(len(headers))
        self.table_wo.setHorizontalHeaderLabels(headers)
        self.table_wo.setRowCount(len(wos))

        for r_idx, wo in enumerate(wos):
            overdue_str = str(round(wo.overdue_days, 1)) if isinstance(wo.overdue_days, float) else str(wo.overdue_days or "")
            row_data = [
                str(r_idx + 1),
                wo.code,
                wo.job_type,
                wo.content,
                wo.deadline,
                wo.status,
                wo.performer,
                wo.station_code,
                wo.ft_comment or "",
                wo.ft_mobile or "",
                str(wo.completed_date or ""),
                overdue_str,
                wo.center_raw,
                wo.bkk or "",
                wo.bkk_reason or ""
            ]

            for c_idx, val in enumerate(row_data):
                item = QTableWidgetItem(val)
                if c_idx in (0, 4, 5, 7, 9, 10, 11, 13):
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                if c_idx in (1, 6): # Mã WO & Performer
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)

                if c_idx == 11: # Overdue days
                    item.setForeground(QColor("#C00000"))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)

                self.table_wo.setItem(r_idx, c_idx, item)

        self.table_wo.resizeColumnsToContents()

    def _render_pending_wo_table(self, center: Optional[CenterReport]):
        """Renders the table of pending Work Orders (column L > 0) for the selected center in Tab 4."""
        if not center or not center.pending_work_orders:
            self.table_pending_wo.setRowCount(0)
            c_name = center.center_name if center else "huyện này"
            self.lbl_pending_wo_info.setText(f"Trung tâm {c_name} hiện không có WO tồn chưa quá hạn (Cột L có giá trị > 0).")
            self.btn_copy_pending_wo_tab.setEnabled(False)
            self.btn_copy_pending_wo.setEnabled(False)
            self.tabs.setTabText(3, "⏳ WO Tồn Chưa Quá Hạn (0)")
            return

        pwos = center.pending_work_orders
        self.lbl_pending_wo_info.setText(f"Danh sách {len(pwos)} WO tồn chưa quá hạn thuộc trung tâm {center.center_name} ({center.center_code}):")
        self.btn_copy_pending_wo_tab.setEnabled(True)
        self.btn_copy_pending_wo.setEnabled(True)
        self.tabs.setTabText(3, f"⏳ WO Tồn Chưa Quá Hạn ({len(pwos)})")

        headers = [
            "STT", "Mã công việc", "Loại công việc", "Nội dung công việc",
            "Thời điểm kết thúc", "Trạng thái", "Nhân viên thực hiện",
            "Mã trạm", "FT comment", "FT mobile", "Ngày hoàn thành",
            "Ngày quá hạn", "TTH", "BKK", "Lý do BKK"
        ]

        self.table_pending_wo.clear()
        self.table_pending_wo.setColumnCount(len(headers))
        self.table_pending_wo.setHorizontalHeaderLabels(headers)
        self.table_pending_wo.setRowCount(len(pwos))

        for r_idx, wo in enumerate(pwos):
            overdue_str = str(round(wo.overdue_days, 1)) if isinstance(wo.overdue_days, float) else str(wo.overdue_days or "")
            row_data = [
                str(r_idx + 1),
                wo.code,
                wo.job_type,
                wo.content,
                wo.deadline,
                wo.status,
                wo.performer,
                wo.station_code,
                wo.ft_comment or "",
                wo.ft_mobile or "",
                str(wo.completed_date or ""),
                overdue_str,
                wo.center_raw,
                wo.bkk or "",
                wo.bkk_reason or ""
            ]

            for c_idx, val in enumerate(row_data):
                item = QTableWidgetItem(val)
                if c_idx in (0, 4, 5, 7, 9, 10, 11, 13):
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                if c_idx in (1, 6): # Mã WO & Performer
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)

                if c_idx == 11: # Days remaining/not overdue (>0)
                    item.setForeground(QColor("#135E48"))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)

                self.table_pending_wo.setItem(r_idx, c_idx, item)

        self.table_pending_wo.resizeColumnsToContents()

    def _render_tag_audit_table(self):
        """Renders the interactive Tag Audit table where user can view and toggle tags."""
        eff_dataset = self._get_effective_dataset()
        if not eff_dataset:
            self.table_tag_audit.setRowCount(0)
            return

        headers = ["Tag", "Tài khoản FT", "Họ và tên", "Huyện", "Vị trí", "Tồn (Cột Q)", "TH Ngày (Cột T)", "Tình trạng"]
        self.table_tag_audit.clear()
        self.table_tag_audit.setColumnCount(len(headers))
        self.table_tag_audit.setHorizontalHeaderLabels(headers)

        # Collect employees to show
        emps_to_show: List[EmployeeFT] = []
        for code, center in eff_dataset.centers.items():
            if self.chk_filter_current_center.isChecked() and self.current_center_code and code != self.current_center_code:
                continue
            for emp in center.employees:
                if self.chk_filter_tagged.isChecked() and not emp.is_tagged:
                    continue
                emps_to_show.append(emp)

        self.table_tag_audit.setRowCount(len(emps_to_show))

        for r_idx, emp in enumerate(emps_to_show):
            is_tag = emp.is_tagged

            # Checkbox item for Tag
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Checked if is_tag else Qt.Unchecked)
            # Store reference to emp in item
            chk_item.setData(Qt.UserRole, emp)
            self.table_tag_audit.setItem(r_idx, 0, chk_item)

            item_user = QTableWidgetItem(emp.username)
            item_name = QTableWidgetItem(emp.full_name)
            item_center = QTableWidgetItem(f"{emp.center_code} - {emp.center_name}")
            item_pos = QTableWidgetItem(emp.position)

            item_q = QTableWidgetItem(str(emp.ton))
            item_q.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            if emp.ton > 0:
                item_q.setForeground(QColor("#C00000"))
                f = item_q.font()
                f.setBold(True)
                item_q.setFont(f)

            item_t = QTableWidgetItem(str(emp.thuc_hien_ngay))
            item_t.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

            # Status description
            if emp.ton > 0 and emp.thuc_hien_ngay <= 0:
                status_str = "⚠ Tồn > 0, Chưa có tiến độ ngày"
                color = QColor("#C53030")
            elif emp.ton > 0 and emp.thuc_hien_ngay > 0:
                status_str = "✓ Đã có tiến độ thực hiện ngày"
                color = QColor("#2F855A")
            else:
                status_str = "✓ Không có WO tồn"
                color = QColor("#4A5568")

            item_status = QTableWidgetItem(status_str)
            item_status.setForeground(color)

            self.table_tag_audit.setItem(r_idx, 1, item_user)
            self.table_tag_audit.setItem(r_idx, 2, item_name)
            self.table_tag_audit.setItem(r_idx, 3, item_center)
            self.table_tag_audit.setItem(r_idx, 4, item_pos)
            self.table_tag_audit.setItem(r_idx, 5, item_q)
            self.table_tag_audit.setItem(r_idx, 6, item_t)
            self.table_tag_audit.setItem(r_idx, 7, item_status)

        self.table_tag_audit.itemChanged.connect(self._on_audit_item_changed)
        self.table_tag_audit.resizeColumnsToContents()

    def _on_audit_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0:
            emp = item.data(Qt.UserRole)
            if isinstance(emp, EmployeeFT):
                new_state = (item.checkState() == Qt.Checked)
                self.processor.set_employee_manual_tag(emp, new_state)

                # Update total tagged badge
                self._update_meta_badges()

                # Refresh preview
                self._update_preview()

    def _reset_tags(self):
        if self.dataset:
            self.processor.reset_all_tags(self.dataset)
            self._render_tag_audit_table()
            self._update_preview()
            self._update_meta_badges()
            self.lbl_status.setText("Đã khôi phục logic tag tự động: Q > 0 và T ≤ 0.")

    def _copy_full_report(self):
        eff_dataset = self._get_effective_dataset()
        if not eff_dataset or not self.current_center_code:
            return

        center = eff_dataset.centers.get(self.current_center_code)
        if not center or len(center.employees) == 0:
            QMessageBox.information(self, "Thông báo", "Không có dữ liệu nhân sự phù hợp bộ lọc để copy.")
            return

        notice_text = self.lbl_preview_notice.text()
        ClipboardManager.copy_full_report(center, notice_text)

        self.lbl_status.setText(f"✓ Đã copy toàn bộ báo cáo trung tâm {self.current_center_code} lên Clipboard (Hỗ trợ HTML cho TAMMY).")
        QMessageBox.information(
            self,
            "Đã Copy Lên Clipboard",
            f"Đã copy toàn bộ báo cáo của trung tâm {center.center_name} ({self.current_center_code})!\n\n"
            "Bạn có thể mở TAMMY, Word, Teams hoặc Excel và nhấn Ctrl+V để dán trực tiếp."
        )

    def _copy_notice_only(self):
        notice_text = self.lbl_preview_notice.text()
        if not notice_text:
            return

        ClipboardManager.copy_notification_only(notice_text)
        self.lbl_status.setText(f"✓ Đã copy Thông báo + Danh sách TAG của huyện {self.current_center_code} lên Clipboard.")
        QMessageBox.information(
            self,
            "Đã Copy",
            "Đã copy nội dung Thông báo + Danh sách TAG lên Clipboard!\nNhấn Ctrl+V để dán."
        )

    def _copy_wo_only(self):
        eff_dataset = self._get_effective_dataset()
        if not eff_dataset or not self.current_center_code:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một trung tâm huyện.")
            return

        center = eff_dataset.centers.get(self.current_center_code)
        if not center or not center.work_orders:
            QMessageBox.information(self, "Thông báo", f"Trung tâm {self.current_center_code} không có WO quá hạn để copy.")
            return

        success = ClipboardManager.copy_work_orders(center)
        if success:
            self.lbl_status.setText(f"✓ Đã copy {len(center.work_orders)} WO quá hạn của trung tâm {self.current_center_code} lên Clipboard.")
            QMessageBox.information(
                self,
                "Đã Copy WO Quá Hạn",
                f"Đã copy thành công {len(center.work_orders)} WO quá hạn của trung tâm {center.center_name} ({self.current_center_code}) lên Clipboard!\n\n"
                "Bạn có thể mở Excel, TAMMY, Word hoặc Teams và nhấn Ctrl+V để dán trực tiếp."
            )

    def _copy_pending_wo_only(self):
        eff_dataset = self._get_effective_dataset()
        if not eff_dataset or not self.current_center_code:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một trung tâm huyện.")
            return

        center = eff_dataset.centers.get(self.current_center_code)
        if not center or not center.pending_work_orders:
            QMessageBox.information(self, "Thông báo", f"Trung tâm {self.current_center_code} không có WO tồn chưa quá hạn để copy.")
            return

        success = ClipboardManager.copy_pending_work_orders(center)
        if success:
            self.lbl_status.setText(f"✓ Đã copy {len(center.pending_work_orders)} WO tồn chưa quá hạn của trung tâm {self.current_center_code} lên Clipboard.")
            QMessageBox.information(
                self,
                "Đã Copy WO Tồn Chưa Quá Hạn",
                f"Đã copy thành công {len(center.pending_work_orders)} WO tồn chưa quá hạn của trung tâm {center.center_name} ({self.current_center_code}) lên Clipboard!\n\n"
                "Bạn có thể mở Excel, TAMMY, Word hoặc Teams và nhấn Ctrl+V để dán trực tiếp."
            )

    def _export_excel(self):
        eff_dataset = self._get_effective_dataset()
        if not eff_dataset:
            return

        pos_filter = self.cmb_position_filter.currentData() or "ALL"
        tag_format = self.cmb_tag_format.currentData() or "name"
        deadline = self.txt_deadline.text().strip()
        meeting = self.txt_meeting.text().strip()
        template = self.txt_notice_template.toPlainText()

        # Build notification text for each center
        notification_texts: Dict[str, str] = {}
        for code, center in eff_dataset.centers.items():
            notification_texts[code] = self.processor.generate_center_notification(
                center=center,
                template=template,
                report_date_str=eff_dataset.report_date_str,
                day_month_str=eff_dataset.day_month_str,
                deadline_str=deadline,
                meeting_time_str=meeting,
                tag_format=tag_format
            )

        default_dir = os.path.dirname(eff_dataset.file_path)
        out_dir = QFileDialog.getExistingDirectory(
            self,
            "Chọn thư mục lưu báo cáo Excel",
            default_dir
        )
        if not out_dir:
            return

        self.btn_export.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Đang tạo các sheet báo cáo...")

        self.export_worker = ExcelExportWorker(
            self.exporter,
            eff_dataset,
            notification_texts,
            out_dir,
            position_filter=pos_filter
        )
        self.export_worker.progress.connect(self._on_load_progress)
        self.export_worker.finished.connect(self._on_export_finished)
        self.export_worker.error.connect(self._on_load_error)
        self.export_worker.start()

    @Slot(str)
    def _on_export_finished(self, out_path: str):
        self.last_exported_file = out_path
        self.btn_export.setEnabled(True)
        self.btn_open_folder.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText(f"✓ Đã xuất thành công: {os.path.basename(out_path)}")

        reply = QMessageBox.question(
            self,
            "Xuất Báo Cáo Thành Công",
            f"Đã xuất báo cáo THFT thành công!\n\nFile: {out_path}\n\nBạn có muốn mở file này ngay bây giờ không?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            try:
                os.startfile(out_path)
            except Exception as e:
                logger.error(f"Cannot start file {out_path}: {e}")

    def _open_export_folder(self):
        if self.last_exported_file and os.path.exists(self.last_exported_file):
            folder = os.path.dirname(self.last_exported_file)
            try:
                os.startfile(folder)
            except Exception as e:
                logger.error(f"Cannot open folder: {e}")
        elif self.dataset and os.path.exists(self.dataset.file_path):
            try:
                os.startfile(os.path.dirname(self.dataset.file_path))
            except Exception as e:
                logger.error(f"Cannot open folder: {e}")
