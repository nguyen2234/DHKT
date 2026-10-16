"""
Main application window for WO Report Tool.
Provides a modern, intuitive, responsive PySide6 user interface in Vietnamese.
"""

import logging
import os
import subprocess
import sys
from datetime import date
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config import get_base_directory, load_config, save_config
from app.excel_exporter import ExcelExporter
from app.excel_reader import ExcelReaderWorker
from app.models import ReportData, ReportSettings
from app.report_generator import ReportGenerator
from app.utils import parse_file_modified_time

logger = logging.getLogger(__name__)


# Modern styling sheet for the application
MODERN_STYLE_SHEET = """
QMainWindow {
    background-color: #F8FAFC;
}

QWidget {
    font-family: 'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size: 13px;
    color: #1E293B;
}

QGroupBox {
    font-weight: bold;
    font-size: 13px;
    color: #1E40AF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    background-color: #FFFFFF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #FFFFFF;
}

QLineEdit, QTextEdit, QDateEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #0F172A;
    selection-background-color: #3B82F6;
}

QLineEdit:focus, QTextEdit:focus, QDateEdit:focus {
    border: 1.5px solid #2563EB;
    background-color: #F8FAFC;
}

QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #1E40AF;
}

QPushButton:disabled {
    background-color: #94A3B8;
    color: #E2E8F0;
}

QPushButton#btnCopy {
    background-color: #10B981;
    font-size: 14px;
    padding: 10px 20px;
}

QPushButton#btnCopy:hover {
    background-color: #059669;
}

QPushButton#btnExport {
    background-color: #0284C7;
    font-size: 14px;
    padding: 10px 20px;
}

QPushButton#btnExport:hover {
    background-color: #0369A1;
}

QPushButton#btnRead {
    background-color: #4F46E5;
    font-size: 14px;
    padding: 10px 22px;
}

QPushButton#btnRead:hover {
    background-color: #4338CA;
}

QPushButton#btnSecondary {
    background-color: #E2E8F0;
    color: #334155;
    border: 1px solid #CBD5E1;
}

QPushButton#btnSecondary:hover {
    background-color: #CBD5E1;
}

QTableWidget {
    background-color: #FFFFFF;
    gridline-color: #E2E8F0;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
}

QHeaderView::section {
    background-color: #F1F5F9;
    color: #1E293B;
    font-weight: 600;
    padding: 6px;
    border: 1px solid #CBD5E1;
}

QProgressBar {
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    text-align: center;
    background-color: #E2E8F0;
    color: #0F172A;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #3B82F6;
    border-radius: 3px;
}

QLabel#lblCardValue {
    font-size: 20px;
    font-weight: bold;
    color: #1E40AF;
}

QLabel#lblCardTitle {
    font-size: 11px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
}

QFrame#statCard {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px;
}
"""


class CenterDetailDialog(QDialog):
    """Dialog showing the detailed table of all 14 district centers."""

    def __init__(self, centers: list, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Chi tiết số liệu WO các Trung tâm Huyện (NAN)")
        self.resize(950, 520)
        self.setModal(True)

        layout = QVBoxLayout(self)

        title = QLabel("BẢNG TỔNG HỢP CHI TIẾT TỪNG TRUNG TÂM HUYỆN")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("color: #1E3A8A; margin-bottom: 8px;")
        layout.addWidget(title)

        table = QTableWidget()
        headers = [
            "STT", "Mã TT", "Tên trung tâm", "Tổng tồn",
            "Tồn quá hạn", "Tồn >30 ngày", "TH Ngày", "KH Ngày",
            "Tỷ lệ HT", "Đánh giá", "Họp Ngày"
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(centers))

        for row_idx, c in enumerate(centers):
            table.setItem(row_idx, 0, QTableWidgetItem(str(c.stt)))
            table.setItem(row_idx, 1, QTableWidgetItem(c.code))
            table.setItem(row_idx, 2, QTableWidgetItem(c.name))
            table.setItem(row_idx, 3, QTableWidgetItem(str(c.tong_ton)))
            table.setItem(row_idx, 4, QTableWidgetItem(str(c.ton_qua_han)))
            table.setItem(row_idx, 5, QTableWidgetItem(str(c.ton_30_ngay)))
            table.setItem(row_idx, 6, QTableWidgetItem(str(c.thuc_hien_ngay)))
            table.setItem(row_idx, 7, QTableWidgetItem(str(c.kh_ngay)))
            pct_text = f"{c.ty_le_ht_ngay * 100:.1f}%" if c.ty_le_ht_ngay else "0.0%"
            table.setItem(row_idx, 8, QTableWidgetItem(pct_text))
            table.setItem(row_idx, 9, QTableWidgetItem(c.danh_gia))
            table.setItem(row_idx, 10, QTableWidgetItem(c.hop_ngay))

        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(table)

        btn_close = QPushButton("Đóng")
        btn_close.setObjectName("btnSecondary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)


class MainWindow(QMainWindow):
    """Main Application Window."""

    def __init__(self):
        super().__init__()
        self.settings: ReportSettings = load_config()
        self.current_report_data: Optional[ReportData] = None
        self.worker: Optional[ExcelReaderWorker] = None
        self.last_exported_excel_path: Optional[str] = None

        self.init_ui()
        self.apply_settings()

    def init_ui(self):
        """Constructs and organizes the GUI layout."""
        self.setWindowTitle("CÔNG CỤ TẠO BÁO CÁO WO - NAN_DHKT")
        self.resize(self.settings.window_width, self.settings.window_height)
        self.setStyleSheet(MODERN_STYLE_SHEET)

        # Set application icon
        icon_path = os.path.join(get_base_directory(), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # Header Title Banner
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1E3A8A; border-radius: 8px; padding: 10px;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 6, 12, 6)

        title_vbox = QVBoxLayout()
        lbl_app_title = QLabel("CÔNG CỤ TẠO BÁO CÁO WO")
        lbl_app_title.setFont(QFont("Arial", 16, QFont.Bold))
        lbl_app_title.setStyleSheet("color: #FFFFFF;")
        lbl_app_sub = QLabel("Phòng VHKT - Tự động trích xuất số liệu tiến độ cắt tồn WO từ file Excel sang mẫu báo cáo chuẩn")
        lbl_app_sub.setStyleSheet("color: #93C5FD; font-size: 12px;")
        title_vbox.addWidget(lbl_app_title)
        title_vbox.addWidget(lbl_app_sub)
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()

        main_layout.addWidget(header_frame)

        # Main splitter: Left side (Inputs & Controls) | Right side (Preview & Actions)
        splitter = QSplitter(Qt.Horizontal)

        # ==========================================
        # LEFT PANEL: Controls, Inputs, File selection
        # ==========================================
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(12)

        # [1] KHU VỰC CHỌN FILE
        grp_file = QGroupBox("[1] KHU VỰC CHỌN FILE EXCEL BÁO CÁO")
        grp_file_layout = QVBoxLayout(grp_file)
        grp_file_layout.setSpacing(8)

        file_pick_layout = QHBoxLayout()
        self.txt_file_path = QLineEdit()
        self.txt_file_path.setPlaceholderText("Chọn đường dẫn đến file Excel (.xlsx)...")
        self.txt_file_path.setReadOnly(True)
        file_pick_layout.addWidget(self.txt_file_path)

        self.btn_browse = QPushButton("Chọn file Excel")
        self.btn_browse.clicked.connect(self.on_browse_file)
        file_pick_layout.addWidget(self.btn_browse)
        grp_file_layout.addLayout(file_pick_layout)

        # File info panel
        file_info_grid = QGridLayout()
        file_info_grid.setSpacing(6)

        file_info_grid.addWidget(QLabel("Tên file:"), 0, 0)
        self.lbl_file_name = QLabel("(Chưa chọn)")
        self.lbl_file_name.setStyleSheet("font-weight: 600; color: #1E3A8A;")
        file_info_grid.addWidget(self.lbl_file_name, 0, 1)

        file_info_grid.addWidget(QLabel("Ngày sửa file:"), 1, 0)
        self.lbl_file_mtime = QLabel("-")
        file_info_grid.addWidget(self.lbl_file_mtime, 1, 1)

        file_info_grid.addWidget(QLabel("Sheet nhận diện:"), 2, 0)
        self.lbl_file_sheet = QLabel("-")
        file_info_grid.addWidget(self.lbl_file_sheet, 2, 1)

        file_info_grid.addWidget(QLabel("Trạng thái:"), 3, 0)
        self.lbl_file_status = QLabel("Chờ chọn file")
        self.lbl_file_status.setStyleSheet("color: #64748B; font-style: italic;")
        file_info_grid.addWidget(self.lbl_file_status, 3, 1)

        grp_file_layout.addLayout(file_info_grid)

        # Read Button & Progress
        self.btn_read_data = QPushButton("  ▶  ĐỌC DỮ LIỆU EXCEL")
        self.btn_read_data.setObjectName("btnRead")
        self.btn_read_data.clicked.connect(self.on_read_data)
        self.btn_read_data.setEnabled(False)
        grp_file_layout.addWidget(self.btn_read_data)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Marquee animation
        grp_file_layout.addWidget(self.progress_bar)

        left_layout.addWidget(grp_file)

        # [2] THÔNG TIN BÁO CÁO
        grp_info = QGroupBox("[2] THÔNG TIN BÁO CÁO")
        grp_info_layout = QGridLayout(grp_info)
        grp_info_layout.setSpacing(8)

        grp_info_layout.addWidget(QLabel("Ngày báo cáo:"), 0, 0)
        self.date_report = QDateEdit()
        self.date_report.setCalendarPopup(True)
        self.date_report.setDate(QDate.currentDate())
        self.date_report.setDisplayFormat("dd/MM/yyyy")
        self.date_report.dateChanged.connect(self.on_date_changed)
        grp_info_layout.addWidget(self.date_report, 0, 1)

        grp_info_layout.addWidget(QLabel("Tháng báo cáo:"), 0, 2)
        self.txt_month = QLineEdit(f"{QDate.currentDate().month():02d}/{QDate.currentDate().year()}")
        self.txt_month.textChanged.connect(self.update_preview_from_inputs)
        grp_info_layout.addWidget(self.txt_month, 0, 3)

        grp_info_layout.addWidget(QLabel("Hạn chót WO quá hạn:"), 1, 0)
        self.txt_deadline_qh = QLineEdit(self.settings.deadline_qh)
        self.txt_deadline_qh.textChanged.connect(self.on_deadlines_changed)
        grp_info_layout.addWidget(self.txt_deadline_qh, 1, 1)

        grp_info_layout.addWidget(QLabel("Hạn chót WO tháng:"), 1, 2)
        self.txt_deadline_month = QLineEdit(self.settings.deadline_month)
        self.txt_deadline_month.textChanged.connect(self.on_deadlines_changed)
        grp_info_layout.addWidget(self.txt_deadline_month, 1, 3)

        grp_info_layout.addWidget(QLabel("Thực hiện ngày (WO):"), 2, 0)
        self.txt_thuc_hien_ngay = QLineEdit("0")
        self.txt_thuc_hien_ngay.setPlaceholderText("Số WO thực hiện trong ngày")
        self.txt_thuc_hien_ngay.textChanged.connect(self.update_preview_from_inputs)
        grp_info_layout.addWidget(self.txt_thuc_hien_ngay, 2, 1)

        grp_info_layout.addWidget(QLabel("Người nhận:"), 3, 0)
        self.txt_recipient = QLineEdit(self.settings.recipient)
        self.txt_recipient.textChanged.connect(self.update_preview_from_inputs)
        grp_info_layout.addWidget(self.txt_recipient, 3, 1, 1, 3)

        left_layout.addWidget(grp_info)

        # [3] THÔNG BÁO / NỘI DUNG CÓ THỂ CHỈNH SỬA
        grp_notify = QGroupBox("[3] NỘI DUNG YÊU CẦU / THÔNG BÁO")
        grp_notify_layout = QVBoxLayout(grp_notify)
        grp_notify_layout.setSpacing(6)

        self.txt_notification = QTextEdit()
        self.txt_notification.setPlaceholderText("Nhập nội dung thông báo/chỉ đạo...")
        self.txt_notification.setPlainText(self.settings.notification)
        self.txt_notification.setMaximumHeight(85)
        self.txt_notification.textChanged.connect(self.update_preview_from_inputs)
        grp_notify_layout.addWidget(self.txt_notification)

        notify_btns = QHBoxLayout()
        btn_reset_notify = QPushButton("Khôi phục mặc định")
        btn_reset_notify.setObjectName("btnSecondary")
        btn_reset_notify.clicked.connect(self.on_reset_notification)
        notify_btns.addWidget(btn_reset_notify)

        btn_save_config = QPushButton("Lưu cấu hình mặc định")
        btn_save_config.setObjectName("btnSecondary")
        btn_save_config.clicked.connect(self.on_save_settings)
        notify_btns.addWidget(btn_save_config)

        grp_notify_layout.addLayout(notify_btns)
        left_layout.addWidget(grp_notify)

        # SUMMARY STAT CARDS (Chỉ số tổng hợp)
        grp_stats = QGroupBox("CHỈ SỐ TỔNG HỢP NHANH")
        stats_layout = QGridLayout(grp_stats)
        stats_layout.setSpacing(8)

        self.card_th_ngay = self._create_stat_card("THỰC HIỆN NGÀY", "0 WO", "#2563EB")
        self.card_tong_ton = self._create_stat_card("TỔNG TỒN", "0 WO", "#DC2626")
        self.card_ton_qh = self._create_stat_card("TỒN QUÁ HẠN", "0 WO", "#D97706")
        self.card_ton_30 = self._create_stat_card("TỒN > 30 NGÀY", "0 WO", "#9333EA")

        stats_layout.addWidget(self.card_th_ngay, 0, 0)
        stats_layout.addWidget(self.card_tong_ton, 0, 1)
        stats_layout.addWidget(self.card_ton_qh, 1, 0)
        stats_layout.addWidget(self.card_ton_30, 1, 1)

        self.lbl_top5_centers = QLabel("Top 5 tồn cao: Chưa có dữ liệu")
        self.lbl_top5_centers.setStyleSheet("font-weight: 600; color: #1E3A8A; padding-top: 4px;")
        stats_layout.addWidget(self.lbl_top5_centers, 2, 0, 1, 2)

        self.btn_view_centers = QPushButton("🔍 Xem bảng chi tiết 14 huyện")
        self.btn_view_centers.setObjectName("btnSecondary")
        self.btn_view_centers.clicked.connect(self.on_view_centers_dialog)
        self.btn_view_centers.setEnabled(False)
        stats_layout.addWidget(self.btn_view_centers, 3, 0, 1, 2)

        left_layout.addWidget(grp_stats)
        left_layout.addStretch()

        left_scroll.setWidget(left_widget)
        splitter.addWidget(left_scroll)

        # ==========================================
        # RIGHT PANEL: Preview & Action Buttons
        # ==========================================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(10)

        # Group Preview
        grp_preview = QGroupBox("XEM TRƯỚC BÁO CÁO (CÓ THỂ SỬA TRỰC TIẾP)")
        grp_preview_layout = QVBoxLayout(grp_preview)
        grp_preview_layout.setSpacing(8)

        lbl_preview_tip = QLabel("💡 Bạn có thể sửa trực tiếp văn bản bên dưới trước khi bấm [Sao chép báo cáo] để dán lên TAMMI:")
        lbl_preview_tip.setStyleSheet("color: #475569; font-size: 12px;")
        grp_preview_layout.addWidget(lbl_preview_tip)

        self.txt_preview = QTextEdit()
        self.txt_preview.setFont(QFont("Consolas", 11))
        self.txt_preview.setPlaceholderText("Nội dung báo cáo sẽ hiển thị tại đây sau khi đọc dữ liệu...")
        grp_preview_layout.addWidget(self.txt_preview)

        right_layout.addWidget(grp_preview)

        # Action Buttons Area
        btn_grid = QGridLayout()
        btn_grid.setSpacing(10)

        self.btn_refresh_preview = QPushButton("🔄 Làm mới Preview")
        self.btn_refresh_preview.setObjectName("btnSecondary")
        self.btn_refresh_preview.clicked.connect(self.update_preview_from_inputs)
        btn_grid.addWidget(self.btn_refresh_preview, 0, 0)

        self.chk_open_after_export = QCheckBox("Mở file Excel ngay sau khi xuất")
        self.chk_open_after_export.setChecked(True)
        btn_grid.addWidget(self.chk_open_after_export, 0, 1)

        self.btn_copy_tammi = QPushButton("📋 SAO CHÉP BÁO CÁO (DÁN TAMMI)")
        self.btn_copy_tammi.setObjectName("btnCopy")
        self.btn_copy_tammi.clicked.connect(self.on_copy_to_tammi)
        btn_grid.addWidget(self.btn_copy_tammi, 1, 0)

        self.btn_export_excel = QPushButton("📊 XUẤT FILE EXCEL")
        self.btn_export_excel.setObjectName("btnExport")
        self.btn_export_excel.clicked.connect(self.on_export_excel)
        btn_grid.addWidget(self.btn_export_excel, 1, 1)

        right_layout.addLayout(btn_grid)
        splitter.addWidget(right_widget)

        # Set splitter proportions (45% left, 55% right)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 5)
        main_layout.addWidget(splitter)

        # Auto-detect sample file if present in workspace or samples
        self.auto_detect_sample_file()

    def _create_stat_card(self, title: str, initial_value: str, color_hex: str) -> QFrame:
        """Helper to create a modern statistical indicator card."""
        frame = QFrame()
        frame.setObjectName("statCard")
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(2)

        lbl_t = QLabel(title)
        lbl_t.setObjectName("lblCardTitle")
        vbox.addWidget(lbl_t)

        lbl_v = QLabel(initial_value)
        lbl_v.setObjectName("lblCardValue")
        lbl_v.setStyleSheet(f"color: {color_hex}; font-size: 18px; font-weight: bold;")
        vbox.addWidget(lbl_v)

        # Store label reference on frame for updating
        frame.val_label = lbl_v
        return frame

    def apply_settings(self):
        """Loads and reflects settings into UI fields."""
        self.txt_recipient.setText(self.settings.recipient)
        self.txt_notification.setPlainText(self.settings.notification)
        self.txt_deadline_qh.setText(self.settings.deadline_qh)
        self.txt_deadline_month.setText(self.settings.deadline_month)

    def auto_detect_sample_file(self):
        """Auto detects the sample Excel file if found in root or samples directory."""
        candidates = [
            os.path.join(get_base_directory(), "samples", "ĐH WO UT1 (05102026).xlsx"),
            os.path.join(get_base_directory(), "samples", "ĐH WO UT1 (05102026)(3).xlsx"),
            r"d:\NAN-DHKT\ĐH WO UT1 (05102026).xlsx",
            r"d:\NAN-DHKT\ĐH WO UT1 (05102026)(3).xlsx",
        ]
        for p in candidates:
            if os.path.exists(p):
                self.load_file_path(p)
                break

    def on_browse_file(self):
        """Prompts user to select an Excel workbook."""
        start_dir = self.settings.last_output_directory or get_base_directory()
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file Excel báo cáo WO",
            start_dir,
            "Excel Files (*.xlsx *.xlsm);;All Files (*.*)"
        )
        if filepath:
            self.load_file_path(filepath)

    def load_file_path(self, filepath: str):
        """Validates and displays file metadata."""
        if not os.path.exists(filepath):
            return

        self.txt_file_path.setText(filepath)
        filename = os.path.basename(filepath)
        self.lbl_file_name.setText(filename)
        self.lbl_file_mtime.setText(parse_file_modified_time(filepath))
        self.lbl_file_sheet.setText("TH TTH (Mặc định)")
        self.lbl_file_status.setText("Sẵn sàng đọc dữ liệu")
        self.lbl_file_status.setStyleSheet("color: #059669; font-weight: 600;")
        self.btn_read_data.setEnabled(True)

    def on_read_data(self):
        """Starts asynchronous background worker to read Excel data."""
        filepath = self.txt_file_path.text().strip()
        if not filepath or not os.path.exists(filepath):
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file Excel hợp lệ trước.")
            return

        # Prepare UI for reading
        self.btn_read_data.setEnabled(False)
        self.btn_browse.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_file_status.setText("Đang đọc dữ liệu Excel...")
        self.lbl_file_status.setStyleSheet("color: #2563EB; font-weight: 600;")

        qdate = self.date_report.date()
        custom_date = date(qdate.year(), qdate.month(), qdate.day())

        self.worker = ExcelReaderWorker(filepath, custom_date)
        self.worker.status_updated.connect(lambda msg: self.lbl_file_status.setText(msg))
        self.worker.finished.connect(self.on_read_success)
        self.worker.error.connect(self.on_read_error)
        self.worker.start()

    def on_read_success(self, data: ReportData):
        """Handles successfully extracted ReportData."""
        self.progress_bar.setVisible(False)
        self.btn_read_data.setEnabled(True)
        self.btn_browse.setEnabled(True)
        self.btn_view_centers.setEnabled(True)

        self.current_report_data = data
        self.lbl_file_status.setText("Đọc dữ liệu thành công!")
        self.lbl_file_status.setStyleSheet("color: #059669; font-weight: bold;")
        self.lbl_file_sheet.setText(data.source_sheet_name)

        # Update input field
        self.txt_thuc_hien_ngay.setText(str(data.thuc_hien_ngay))

        # Update Stat Cards
        self.card_th_ngay.val_label.setText(f"{data.thuc_hien_ngay} WO")
        self.card_tong_ton.val_label.setText(f"{data.tong_ton} WO")
        self.card_ton_qh.val_label.setText(f"{data.ton_qua_han} WO")

        detail_30 = ""
        if data.overdue_30_centers:
            detail_30 = " (" + ", ".join(f"{c}:{cnt}" for c, cnt in data.overdue_30_centers) + ")"
        self.card_ton_30.val_label.setText(f"{data.ton_tren_30_ngay} WO{detail_30}")

        top_str = ", ".join(data.top_centers) if data.top_centers else "Không có dữ liệu"
        self.lbl_top5_centers.setText(f"Top 5 tồn cao: {top_str}")

        # Sync input settings into data and update preview
        self.sync_inputs_to_report_data()
        self.update_preview()

    def on_read_error(self, err_msg: str):
        """Handles Excel reading errors."""
        self.progress_bar.setVisible(False)
        self.btn_read_data.setEnabled(True)
        self.btn_browse.setEnabled(True)
        self.lbl_file_status.setText("Đọc dữ liệu thất bại!")
        self.lbl_file_status.setStyleSheet("color: #DC2626; font-weight: bold;")

        QMessageBox.critical(
            self,
            "Lỗi đọc dữ liệu Excel",
            f"Không thể đọc dữ liệu từ file Excel được chọn.\n\nNguyên nhân: {err_msg}\n\n"
            "Vui lòng kiểm tra lại cấu trúc file và sheet dữ liệu."
        )

    def on_date_changed(self, new_qdate: QDate):
        """Updates month text and preview when report date changes."""
        self.txt_month.setText(f"{new_qdate.month():02d}/{new_qdate.year()}")
        if self.current_report_data:
            self.current_report_data.day = new_qdate.day()
            self.current_report_data.month = new_qdate.month()
            self.current_report_data.year = new_qdate.year()
            self.current_report_data.report_date = date(new_qdate.year(), new_qdate.month(), new_qdate.day())
        self.update_preview_from_inputs()

    def on_deadlines_changed(self):
        """Updates default notification text when deadlines are modified."""
        qh = self.txt_deadline_qh.text().strip() or "30/09"
        month_dl = self.txt_deadline_month.text().strip() or "05/10"
        m = self.date_report.date().month()
        default_notification = f"Đóng Wo quá hạn trước {qh}.\nĐóng hết wo tháng {m} xong trước {month_dl}."
        self.txt_notification.setPlainText(default_notification)
        self.update_preview_from_inputs()

    def on_reset_notification(self):
        """Resets notification text to standard template."""
        self.on_deadlines_changed()

    def on_save_settings(self):
        """Saves current input fields to config.json."""
        self.settings.recipient = self.txt_recipient.text().strip()
        self.settings.notification = self.txt_notification.toPlainText().strip()
        self.settings.deadline_qh = self.txt_deadline_qh.text().strip()
        self.settings.deadline_month = self.txt_deadline_month.text().strip()
        self.settings.window_width = self.width()
        self.settings.window_height = self.height()

        if save_config(self.settings):
            QMessageBox.information(self, "Thông báo", "Đã lưu cấu hình mặc định vào config.json thành công!")
        else:
            QMessageBox.warning(self, "Lỗi", "Không thể lưu cấu hình vào config.json.")

    def sync_inputs_to_report_data(self):
        """Synchronizes GUI inputs with current_report_data model."""
        if not self.current_report_data:
            return
        qdate = self.date_report.date()
        self.current_report_data.day = qdate.day()
        self.current_report_data.month = qdate.month()
        self.current_report_data.year = qdate.year()
        
        try:
            th_val = int(self.txt_thuc_hien_ngay.text().strip() or "0")
            self.current_report_data.thuc_hien_ngay = th_val
            if hasattr(self, 'card_th_ngay') and hasattr(self.card_th_ngay, 'val_label'):
                self.card_th_ngay.val_label.setText(f"{th_val} WO")
        except ValueError:
            pass

        self.current_report_data.recipient = self.txt_recipient.text().strip()
        self.current_report_data.notification = self.txt_notification.toPlainText().strip()
        self.current_report_data.deadline_qh = self.txt_deadline_qh.text().strip()
        self.current_report_data.deadline_month = self.txt_deadline_month.text().strip()

    def update_preview(self):
        """Generates formatted report text and loads it into the preview edit."""
        if not self.current_report_data:
            return
        self.sync_inputs_to_report_data()
        report_text = ReportGenerator.generate_report_text(self.current_report_data)
        self.txt_preview.setPlainText(report_text)

    def update_preview_from_inputs(self):
        """Triggered on text changes to regenerate preview if data is loaded."""
        if self.current_report_data:
            self.update_preview()

    def on_view_centers_dialog(self):
        """Opens modal table with 14 district centers."""
        if not self.current_report_data or not self.current_report_data.centers:
            QMessageBox.information(self, "Thông báo", "Chưa có dữ liệu chi tiết các huyện.")
            return
        dialog = CenterDetailDialog(self.current_report_data.centers, self)
        dialog.exec()

    def on_copy_to_tammi(self):
        """Copies preview text directly into Windows clipboard as plain text for TAMMI."""
        content = self.txt_preview.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Thông báo", "Không có nội dung báo cáo để sao chép. Vui lòng đọc dữ liệu trước.")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(content)

        QMessageBox.information(
            self,
            "Đã sao chép thành công",
            "Toàn bộ nội dung báo cáo đã được sao chép vào bộ nhớ tạm (Clipboard)!\n\n"
            "Bây giờ bạn chỉ cần mở nhóm TAMMI và nhấn Ctrl + V để dán."
        )

    def on_export_excel(self):
        """Exports report into a beautifully styled Excel workbook."""
        if not self.current_report_data:
            QMessageBox.warning(self, "Thông báo", "Vui lòng đọc dữ liệu Excel trước khi xuất báo cáo.")
            return

        qdate = self.date_report.date()
        date_str = f"{qdate.year():04d}{qdate.month():02d}{qdate.day():02d}"
        default_filename = f"BaoCao_WO_{date_str}.xlsx"

        suggested_dir = self.settings.last_output_directory or os.path.dirname(self.txt_file_path.text()) or get_base_directory()
        default_full_path = os.path.join(suggested_dir, default_filename)

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Lưu file Excel báo cáo",
            default_full_path,
            "Excel Files (*.xlsx)"
        )

        if not save_path:
            return

        try:
            self.sync_inputs_to_report_data()
            preview_content = self.txt_preview.toPlainText().strip()
            exported_path = ExcelExporter.export_report(
                self.current_report_data,
                save_path,
                preview_text=preview_content
            )
            self.last_exported_excel_path = exported_path

            # Update last output directory
            self.settings.last_output_directory = os.path.dirname(save_path)
            save_config(self.settings)

            if self.chk_open_after_export.isChecked():
                try:
                    os.startfile(exported_path)
                except Exception as e:
                    logger.warning(f"Could not open file automatically: {e}")

            QMessageBox.information(
                self,
                "Xuất file thành công",
                f"Đã xuất báo cáo Excel thành công tại:\n\n{exported_path}\n\n"
                "File gồm 2 sheet:\n"
                "- 'BaoCao': Trình bày tổng quan theo chuẩn mẫu Word\n"
                "- 'ChiTiet': Bảng chi tiết toàn bộ các trung tâm huyện"
            )
        except Exception as e:
            logger.exception("Failed to export Excel report:")
            QMessageBox.critical(self, "Lỗi xuất Excel", f"Không thể xuất file Excel.\nChi tiết lỗi: {str(e)}")

    def closeEvent(self, event):
        """Saves window size on exit."""
        self.settings.window_width = self.width()
        self.settings.window_height = self.height()
        save_config(self.settings)
        event.accept()
