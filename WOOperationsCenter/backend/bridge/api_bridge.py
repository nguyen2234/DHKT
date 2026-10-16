"""
Secure Python - React Bridge for WO Operations Center.
Exposes typed API methods via PySide6 QtWebChannel / QObject slots
so the React UI can seamlessly invoke all backend business logic
without external HTTP servers or ports.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QFileDialog

from backend.clipboard.clipboard_engine import ClipboardEngine
from backend.core.config import ConfigManager, get_app_data_dir
from backend.database.repository import DatabaseRepository
from backend.domain.models import ReportDataset, ReportHistoryItem
from backend.exporters.docx_exporter import DocxExporter
from backend.exporters.excel_exporter import ExcelExporter
from backend.processors.executive_report import ExecutiveReportProcessor
from backend.processors.thft_report import THFTReportProcessor
from backend.processors.wo_explorer import WOExplorerProcessor
from backend.readers.excel_input_engine import ExcelInputEngine

logger = logging.getLogger(__name__)


class APIBridge(QObject):
    """Bridge object registered with QtWebChannel and accessible from React JavaScript."""

    # Signals to frontend
    importProgress = Signal(int, str)
    datasetLoaded = Signal(str)  # JSON payload
    exportFinished = Signal(str)
    errorMessage = Signal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.config_mgr = ConfigManager()
        self.repo = DatabaseRepository()
        self.reader = ExcelInputEngine()
        self.current_dataset: Optional[ReportDataset] = None

    # ==========================================
    # FILE PICKER & SYSTEM
    # ==========================================

    @Slot(result=str)
    def pickExcelFile(self) -> str:
        """Opens native Windows file picker for Excel files."""
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Chọn tệp Excel điều hành WO",
            "",
            "Excel Files (*.xlsx *.xlsm);;All Files (*.*)"
        )
        return file_path or ""

    @Slot(result=str)
    def pickDirectory(self) -> str:
        """Opens native Windows directory chooser."""
        folder = QFileDialog.getExistingDirectory(
            None,
            "Chọn thư mục lưu báo cáo"
        )
        return folder or ""

    @Slot(result=str)
    def getAppConfig(self) -> str:
        """Returns JSON config."""
        return json.dumps(self.config_mgr.data, ensure_ascii=False)

    @Slot(str, result=bool)
    def saveAppConfig(self, config_json: str) -> bool:
        """Saves JSON config."""
        try:
            data = json.loads(config_json)
            return self.config_mgr.save(data)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    # ==========================================
    # DATASET LOADING
    # ==========================================

    @Slot(str, result=str)
    def loadExcelDataset(self, file_path: str) -> str:
        """
        Loads and parses the Excel workbook, caching it in memory.
        Returns serialized summary payload or error.
        """
        try:
            if not os.path.exists(file_path):
                return json.dumps({"success": False, "error": f"Tệp không tồn tại: {file_path}"})

            def on_progress(pct: int, msg: str):
                self.importProgress.emit(pct, msg)

            dataset = self.reader.parse_workbook(file_path, progress_callback=on_progress)
            self.current_dataset = dataset
            self.config_mgr.add_recent_file(file_path)

            summary_payload = self._serialize_dataset_summary(dataset)
            self.datasetLoaded.emit(json.dumps(summary_payload, ensure_ascii=False))
            return json.dumps({"success": True, "data": summary_payload}, ensure_ascii=False)
        except Exception as e:
            logger.exception("Error in loadExcelDataset:")
            self.errorMessage.emit(str(e))
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @Slot(result=str)
    def getLoadedDataset(self) -> str:
        """Returns currently cached dataset summary if available."""
        if not self.current_dataset:
            return json.dumps({"loaded": False})
        return json.dumps({"loaded": True, "data": self._serialize_dataset_summary(self.current_dataset)}, ensure_ascii=False)

    def _serialize_dataset_summary(self, ds: ReportDataset) -> Dict[str, Any]:
        ps = ds.province_summary
        centers_list = []
        for code, c in ds.centers.items():
            cs = c.summary
            centers_list.append({
                "code": code,
                "name": c.center_name,
                "full_name": c.center_raw,
                "total_employees": c.total_count,
                "tagged_employees": c.tagged_count,
                "overdue_wos": c.work_orders_count,
                "pending_wos": c.pending_work_orders_count,
                "boundary_wos": c.boundary_work_orders_count,
                "tong_ton": cs.tong_ton if cs else sum(e.ton for e in c.employees),
                "ton_qua_han": cs.ton_qua_han if cs else sum(e.qua_han for e in c.employees),
                "ton_30_ngay": cs.ton_30_ngay if cs else sum(e.qua_han_30 for e in c.employees),
                "thuc_hien_ngay": cs.thuc_hien_ngay if cs else sum(e.thuc_hien_ngay for e in c.employees),
                "kh_ngay": cs.kh_ngay if cs else 0,
                "ty_le_ht_ngay": cs.ty_le_ht_ngay if cs else 0.0,
                "danh_gia": cs.danh_gia if cs else "",
                "hop_ngay": cs.hop_ngay if cs else ""
            })

        return {
            "file_path": ds.file_path,
            "file_fingerprint": ds.file_fingerprint,
            "detected_sheets": ds.detected_sheets,
            "report_date_str": ds.report_date_str,
            "day_month_str": ds.day_month_str,
            "deadline_str": ds.deadline_str,
            "meeting_time_str": ds.meeting_time_str,
            "total_employees": ds.total_employees,
            "total_tagged": ds.total_tagged,
            "total_work_orders": ds.total_work_orders,
            "total_pending_work_orders": ds.total_pending_work_orders,
            "total_boundary_work_orders": ds.total_boundary_work_orders,
            "province_summary": {
                "day": ps.day,
                "month": ps.month,
                "year": ps.year,
                "thuc_hien_ngay": ps.thuc_hien_ngay,
                "tong_ton": ps.tong_ton,
                "ton_qua_han": ps.ton_qua_han,
                "ton_tren_30_ngay": ps.ton_tren_30_ngay,
                "top_centers": ps.top_centers,
                "overdue_30_centers": ps.overdue_30_centers,
                "has_discrepancy": ps.has_discrepancy,
                "discrepancy_details": ps.discrepancy_details
            },
            "centers": centers_list
        }

    # ==========================================
    # MODULE A: EXECUTIVE REPORT
    # ==========================================

    @Slot(str, result=str)
    def getExecutiveReportText(self, params_json: str) -> str:
        """Generates executive report text based on input params."""
        if not self.current_dataset:
            return json.dumps({"error": "Chưa nạp dữ liệu"})
        try:
            params = json.loads(params_json) if params_json else {}
            recipient = params.get("recipient", "")
            notification = params.get("notification", "")
            deadline_qh = params.get("deadline_qh", "30/09")
            deadline_month = params.get("deadline_month", "05/10")
            template = params.get("template")

            text = ExecutiveReportProcessor.generate_report_text(
                self.current_dataset.province_summary,
                recipient=recipient,
                notification=notification,
                deadline_qh=deadline_qh,
                deadline_month=deadline_month,
                template=template
            )
            return json.dumps({"success": True, "text": text}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    # ==========================================
    # MODULE B: THFT REPORT
    # ==========================================

    @Slot(str, result=str)
    def getCenterDetails(self, center_code: str) -> str:
        """Retrieves detailed employee records and statistics for a given center."""
        if not self.current_dataset or center_code not in self.current_dataset.centers:
            return json.dumps({"error": f"Không tìm thấy trung tâm {center_code}"})

        center = self.current_dataset.centers[center_code]
        employees_data = []
        for e in center.employees:
            employees_data.append({
                "row_idx": e.row_idx,
                "username": e.username,
                "full_name": e.full_name,
                "position": e.position,
                "center_code": e.center_code,
                "ton": e.ton,
                "qua_han": e.qua_han,
                "qua_han_30": e.qua_han_30,
                "thuc_hien_ngay": e.thuc_hien_ngay,
                "should_tag": e.should_tag,
                "is_manually_tagged": e.is_manually_tagged,
                "is_tagged": e.is_tagged,
                "icms_bd_nt_ton": e.icms_bd_nt_ton,
                "icms_bd_nt_qh": e.icms_bd_nt_qh,
                "icms_bd_nt_qh30": e.icms_bd_nt_qh30,
                "icms_bd_thc_ton": e.icms_bd_thc_ton,
                "icms_bd_thc_qh": e.icms_bd_thc_qh,
                "icms_bd_thc_qh30": e.icms_bd_thc_qh30,
                "icms_tt_tc_ton": e.icms_tt_tc_ton,
                "icms_tt_tc_qh": e.icms_tt_tc_qh,
                "icms_tt_tc_qh30": e.icms_tt_tc_qh30,
                "bao_hong_ton": e.bao_hong_ton,
                "bao_hong_qh": e.bao_hong_qh,
                "bao_hong_qh30": e.bao_hong_qh30
            })

        cfg_thft = self.config_mgr.get("thft_report", {})
        tpl = cfg_thft.get("template", "")
        tag_fmt = cfg_thft.get("tag_format", "name")
        notif = THFTReportProcessor.generate_center_notification(
            center, tpl,
            self.current_dataset.report_date_str,
            self.current_dataset.day_month_str,
            cfg_thft.get("deadline", "05/10"),
            cfg_thft.get("meeting_time", "06:30"),
            tag_format=tag_fmt
        )

        return json.dumps({
            "code": center.center_code,
            "name": center.center_name,
            "notification": notif,
            "subtotal": center.get_subtotal(),
            "employees": employees_data,
            "overdue_wos_count": center.work_orders_count,
            "pending_wos_count": center.pending_work_orders_count
        }, ensure_ascii=False)

    @Slot(str, str, bool, result=bool)
    def setEmployeeTag(self, center_code: str, username: str, is_tagged: bool) -> bool:
        """Sets manual tag override for an employee."""
        if not self.current_dataset:
            return False
        return THFTReportProcessor.set_employee_tag_override(
            self.current_dataset, center_code, username, is_tagged
        )

    # ==========================================
    # MODULE C: WORK ORDER EXPLORER
    # ==========================================

    @Slot(str, result=str)
    def queryWorkOrders(self, params_json: str) -> str:
        """Searches, filters, and paginates work orders."""
        if not self.current_dataset:
            return json.dumps({"total": 0, "items": []})

        params = json.loads(params_json) if params_json else {}
        res = WOExplorerProcessor.query_work_orders(
            self.current_dataset,
            center_code=params.get("center_code"),
            classification=params.get("classification"),
            search_query=params.get("search_query"),
            job_type=params.get("job_type"),
            status=params.get("status"),
            sort_by=params.get("sort_by", "overdue_days"),
            sort_order=params.get("sort_order", "asc"),
            page=params.get("page", 1),
            page_size=params.get("page_size", 50)
        )
        return json.dumps(res, ensure_ascii=False)

    # ==========================================
    # CLIPBOARD ACTIONS
    # ==========================================

    @Slot(str, str, result=bool)
    def copyToClipboard(self, action_type: str, params_json: str) -> bool:
        """
        Executes dedicated clipboard actions:
        - 'province_report': Plain text executive report
        - 'center_report': HTML table + Plain text for center
        - 'center_notification': Plain text notification + tags
        - 'center_overdue_wos': HTML table + TSV of overdue WOs
        - 'center_pending_wos': HTML table + TSV of pending WOs
        - 'text': Raw plain text
        """
        if not self.current_dataset:
            return False

        try:
            params = json.loads(params_json) if params_json else {}
            if action_type == "text":
                text = params.get("text", "")
                return ClipboardEngine.set_system_clipboard(text)

            elif action_type == "province_report":
                text = params.get("text") or ExecutiveReportProcessor.generate_report_text(
                    self.current_dataset.province_summary
                )
                return ClipboardEngine.set_system_clipboard(text)

            elif action_type == "center_report":
                center_code = params.get("center_code")
                center = self.current_dataset.centers.get(center_code)
                if not center:
                    return False
                notif = params.get("notification", "")
                html = ClipboardEngine.build_center_html_table(center, notif)
                text = ClipboardEngine.build_center_text_report(center, notif)
                return ClipboardEngine.set_system_clipboard(text, html)

            elif action_type == "center_notification":
                text = params.get("notification", "")
                return ClipboardEngine.set_system_clipboard(text)

            elif action_type == "center_overdue_wos":
                center_code = params.get("center_code")
                center = self.current_dataset.centers.get(center_code)
                if not center or not center.work_orders:
                    return False
                html = ClipboardEngine.build_work_orders_html(center.work_orders, f"WO QUÁ HẠN — {center.center_name}", theme_color="#1F4E78")
                tsv = ClipboardEngine.build_work_orders_tsv(center.work_orders, f"WO QUÁ HẠN — {center.center_name}")
                return ClipboardEngine.set_system_clipboard(tsv, html)

            elif action_type == "center_pending_wos":
                center_code = params.get("center_code")
                center = self.current_dataset.centers.get(center_code)
                if not center or not center.pending_work_orders:
                    return False
                html = ClipboardEngine.build_work_orders_html(center.pending_work_orders, f"WO TỒN CHƯA QUÁ HẠN — {center.center_name}", theme_color="#135E48")
                tsv = ClipboardEngine.build_work_orders_tsv(center.pending_work_orders, f"WO TỒN CHƯA QUÁ HẠN — {center.center_name}")
                return ClipboardEngine.set_system_clipboard(tsv, html)

            return False
        except Exception as e:
            logger.error(f"Clipboard error: {e}")
            return False

    # ==========================================
    # EXPORT ACTIONS
    # ==========================================

    @Slot(str, str, result=str)
    def exportReport(self, export_type: str, params_json: str) -> str:
        """
        Executes report exports:
        - 'executive_excel': BaoCao_WO_YYYYMMDD.xlsx
        - 'thft_excel': BaoCao_THFT_YYYYMMDD[_NVDM].xlsx
        - 'center_docx': Word document for center
        """
        if not self.current_dataset:
            return json.dumps({"success": False, "error": "Chưa nạp dữ liệu"})

        try:
            params = json.loads(params_json) if params_json else {}
            output_dir = params.get("output_dir") or self.config_mgr.get("default_output_dir")

            if export_type == "executive_excel":
                preview_text = params.get("preview_text", "")
                centers_list = list(self.current_dataset.centers.values())
                out_path = ExcelExporter.export_executive_report(
                    self.current_dataset.province_summary,
                    centers_list,
                    output_dir,
                    preview_text=preview_text
                )

                # Save history
                self.repo.add_history(ReportHistoryItem(
                    id=None,
                    timestamp=None,
                    report_type="executive_wo",
                    report_date=self.current_dataset.report_date_str,
                    source_file_path=self.current_dataset.file_path,
                    source_file_fingerprint=self.current_dataset.file_fingerprint,
                    applied_filters="",
                    center_selection="Toàn tỉnh (14 TT)",
                    output_path=out_path,
                    message_snapshot=preview_text[:200]
                ))

                self.exportFinished.emit(out_path)
                return json.dumps({"success": True, "output_path": out_path})

            elif export_type == "thft_excel":
                pos_filter = params.get("position_filter", "Tất cả")
                separate = params.get("separate_files", False)
                selected_centers = params.get("selected_centers")

                filtered_ds = self.current_dataset.get_filtered_dataset(pos_filter)
                notifications = {}
                cfg_thft = self.config_mgr.get("thft_report", {})
                tpl = cfg_thft.get("template", "")
                tag_fmt = cfg_thft.get("tag_format", "name")

                for code, c in filtered_ds.centers.items():
                    notifications[code] = THFTReportProcessor.generate_center_notification(
                        c, tpl,
                        filtered_ds.report_date_str,
                        filtered_ds.day_month_str,
                        cfg_thft.get("deadline", "05/10"),
                        cfg_thft.get("meeting_time", "06:30"),
                        tag_format=tag_fmt
                    )

                out_paths = ExcelExporter.export_thft_reports(
                    filtered_ds,
                    notifications,
                    output_dir,
                    selected_center_codes=selected_centers,
                    separate_files=separate,
                    position_filter=pos_filter
                )

                # Save history
                for p in out_paths:
                    self.repo.add_history(ReportHistoryItem(
                        id=None,
                        timestamp=None,
                        report_type="thft",
                        report_date=filtered_ds.report_date_str,
                        source_file_path=filtered_ds.file_path,
                        source_file_fingerprint=filtered_ds.file_fingerprint,
                        applied_filters=f"Vị trí: {pos_filter}",
                        center_selection=", ".join(selected_centers) if selected_centers else "Tất cả",
                        output_path=p,
                        message_snapshot=""
                    ))

                self.exportFinished.emit(", ".join(out_paths))
                return json.dumps({"success": True, "output_paths": out_paths})

            elif export_type == "center_docx":
                center_code = params.get("center_code")
                center = self.current_dataset.centers.get(center_code)
                if not center:
                    return json.dumps({"success": False, "error": f"Không tìm thấy huyện {center_code}"})

                notification = params.get("notification", "")
                out_path = os.path.join(output_dir, f"BaoCao_FT_{center_code}_{self.current_dataset.report_date_str.replace('/', '')}.docx")
                DocxExporter.export_center_report_docx(center, notification, out_path)

                self.exportFinished.emit(out_path)
                return json.dumps({"success": True, "output_path": out_path})

            return json.dumps({"success": False, "error": "Loại xuất không hợp lệ"})
        except Exception as e:
            logger.exception("Export error:")
            return json.dumps({"success": False, "error": str(e)})

    # ==========================================
    # HISTORY & TEMPLATES
    # ==========================================

    @Slot(int, int, str, result=str)
    def getReportHistory(self, limit: int = 50, offset: int = 0, report_type: str = "") -> str:
        history = self.repo.get_history(limit=limit, offset=offset, report_type=report_type or None)
        return json.dumps(history, ensure_ascii=False)

    @Slot(int, result=bool)
    def deleteReportHistory(self, history_id: int) -> bool:
        return self.repo.delete_history(history_id)

    @Slot(str, result=str)
    def getTemplates(self, template_type: str = "") -> str:
        tpls = self.repo.get_templates(template_type=template_type or None)
        return json.dumps(tpls, ensure_ascii=False)

    @Slot(str, str, str, str, bool, result=int)
    def saveTemplate(self, name: str, template_type: str, content: str, placeholders: str = "", is_default: bool = False) -> int:
        return self.repo.save_template(name, template_type, content, placeholders, is_default)
