"""
Excel reading module for WO Report Tool.
Safely reads data from Excel files using openpyxl, handles formula fallbacks,
validates sheet structure, and provides a QThread worker for smooth GUI operation.
"""

import logging
import os
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

import openpyxl
from PySide6.QtCore import QObject, QThread, Signal

from app.config import DEFAULT_REPORT_MAPPING
from app.models import CenterData, ReportData
from app.utils import (
    extract_center_code,
    extract_center_name,
    format_safe_float,
    format_safe_integer,
)

logger = logging.getLogger(__name__)


class ExcelReaderError(Exception):
    """Custom exception raised when Excel data extraction fails."""
    pass


class ExcelReader:
    """Safely extracts WO metrics from the source Excel workbook."""

    def __init__(self, mapping: Optional[Dict] = None):
        self.mapping = mapping or DEFAULT_REPORT_MAPPING

    def read_report_data(self, file_path: str, custom_date: Optional[date] = None) -> ReportData:
        """
        Reads and extracts ReportData from the specified Excel file.
        Strictly READ-ONLY. Never modifies or saves back to the source file.
        """
        if not os.path.exists(file_path):
            raise ExcelReaderError(f"File không tồn tại: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".xlsx", ".xlsm"]:
            raise ExcelReaderError("File được chọn không đúng định dạng Excel (.xlsx, .xlsm).")

        logger.info(f"Opening Excel workbook in read-only mode: {file_path}")

        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        except Exception as e:
            logger.error(f"Failed to open workbook: {e}")
            raise ExcelReaderError(f"Không thể mở file Excel. Chi tiết lỗi: {str(e)}")

        target_sheet_name = self.mapping.get("sheet_name", "TH TTH")
        available_sheets = wb.sheetnames

        # Find target sheet or similar matching name
        found_sheet_name = None
        for s in available_sheets:
            if s.strip().lower() == target_sheet_name.strip().lower():
                found_sheet_name = s
                break

        if not found_sheet_name:
            # Fallback search
            for s in available_sheets:
                if "TH TTH" in s or "TH_TTH" in s:
                    found_sheet_name = s
                    break

        if not found_sheet_name:
            wb.close()
            sheets_str = ", ".join(available_sheets)
            raise ExcelReaderError(
                f"Không tìm thấy sheet dữ liệu cần thiết '{target_sheet_name}'.\n"
                f"Các sheet hiện có trong file: {sheets_str}"
            )

        ws = wb[found_sheet_name]
        logger.info(f"Using sheet '{found_sheet_name}'")

        # Read rows
        try:
            rows = list(ws.iter_rows(values_only=True))
        except Exception as e:
            wb.close()
            raise ExcelReaderError(f"Lỗi khi đọc dữ liệu từ sheet '{found_sheet_name}': {str(e)}")
        finally:
            wb.close()

        if len(rows) < 3:
            raise ExcelReaderError("Dữ liệu sheet không đủ hàng tiêu đề và tổng hợp.")

        cols_map = self.mapping.get("columns", {})
        col_name_idx = cols_map.get("center_name", 1) - 1
        col_q_idx = cols_map.get("tong_ton", 17) - 1
        col_r_idx = cols_map.get("ton_qua_han", 18) - 1
        col_s_idx = cols_map.get("ton_30_ngay", 19) - 1
        col_t_idx = cols_map.get("thuc_hien_ngay", 20) - 1
        col_u_idx = cols_map.get("kh_ngay", 21) - 1
        col_v_idx = cols_map.get("danh_gia", 22) - 1
        col_w_idx = cols_map.get("hop_ngay", 23) - 1
        col_x_idx = cols_map.get("ty_le_ht_ngay", 24) - 1

        summary_row_idx = self.mapping.get("summary_row", 3) - 1
        summary_row = rows[summary_row_idx] if summary_row_idx < len(rows) else []

        raw_tong_ton = summary_row[col_q_idx] if len(summary_row) > col_q_idx else None
        raw_ton_qh = summary_row[col_r_idx] if len(summary_row) > col_r_idx else None
        raw_ton_30 = summary_row[col_s_idx] if len(summary_row) > col_s_idx else None
        raw_th_ngay = summary_row[col_t_idx] if len(summary_row) > col_t_idx else None

        # Read centers starting from data_start_row
        data_start_row_idx = self.mapping.get("data_start_row", 4) - 1
        centers: List[CenterData] = []
        center_stt = 1

        calc_sum_q = 0
        calc_sum_r = 0
        calc_sum_s = 0
        calc_sum_t = 0

        for r_idx in range(data_start_row_idx, len(rows)):
            row = rows[r_idx]
            if not row or not any(row):
                continue

            center_full_name = str(row[col_name_idx] or "").strip()
            # Stop if reached total row or empty center name
            if not center_full_name or "tổng" in center_full_name.lower():
                continue

            code = extract_center_code(center_full_name)
            name = extract_center_name(center_full_name)

            q_val = format_safe_integer(row[col_q_idx] if len(row) > col_q_idx else 0)
            r_val = format_safe_integer(row[col_r_idx] if len(row) > col_r_idx else 0)
            s_val = format_safe_integer(row[col_s_idx] if len(row) > col_s_idx else 0)
            t_val = format_safe_integer(row[col_t_idx] if len(row) > col_t_idx else 0)
            u_val = format_safe_integer(row[col_u_idx] if len(row) > col_u_idx else 0)
            v_val = str(row[col_v_idx] or "").strip() if len(row) > col_v_idx else ""
            w_val = str(row[col_w_idx] or "").strip() if len(row) > col_w_idx else ""
            x_val = format_safe_float(row[col_x_idx] if len(row) > col_x_idx else 0.0)

            calc_sum_q += q_val
            calc_sum_r += r_val
            calc_sum_s += s_val
            calc_sum_t += t_val

            center = CenterData(
                stt=center_stt,
                code=code,
                name=name,
                full_name=center_full_name,
                tong_ton=q_val,
                ton_qua_han=r_val,
                ton_30_ngay=s_val,
                thuc_hien_ngay=t_val,
                kh_ngay=u_val,
                ty_le_ht_ngay=x_val,
                danh_gia=v_val,
                hop_ngay=w_val
            )
            centers.append(center)
            center_stt += 1

        if not centers:
            raise ExcelReaderError("Không tìm thấy danh sách trung tâm hợp lệ trong sheet 'TH TTH'.")

        # Resolve summary values: use cached cell value if valid integer, else fallback to sum of centers
        tong_ton = format_safe_integer(raw_tong_ton) if raw_tong_ton is not None else calc_sum_q
        ton_qua_han = format_safe_integer(raw_ton_qh) if raw_ton_qh is not None else calc_sum_r
        ton_tren_30_ngay = format_safe_integer(raw_ton_30) if raw_ton_30 is not None else calc_sum_s
        thuc_hien_ngay = format_safe_integer(raw_th_ngay) if raw_th_ngay is not None else calc_sum_t

        # Safety check: if formula wasn't evaluated in file (value is 0) but sum > 0, use calculated sum
        if tong_ton == 0 and calc_sum_q > 0:
            tong_ton = calc_sum_q
        if ton_qua_han == 0 and calc_sum_r > 0:
            ton_qua_han = calc_sum_r
        if ton_tren_30_ngay == 0 and calc_sum_s > 0:
            ton_tren_30_ngay = calc_sum_s
        if thuc_hien_ngay == 0 and calc_sum_t > 0:
            thuc_hien_ngay = calc_sum_t

        # Top 5 centers with highest backlog (tong_ton)
        sorted_by_backlog = sorted(centers, key=lambda c: c.tong_ton, reverse=True)
        top_5_centers = [c.code for c in sorted_by_backlog[:5]]

        # Centers with backlog > 30 days
        overdue_30_list = [(c.code, c.ton_30_ngay) for c in centers if c.ton_30_ngay > 0]

        rep_date = custom_date or date.today()

        report_data = ReportData(
            report_date=rep_date,
            day=rep_date.day,
            month=rep_date.month,
            year=rep_date.year,
            thuc_hien_ngay=thuc_hien_ngay,
            tong_ton=tong_ton,
            ton_qua_han=ton_qua_han,
            ton_tren_30_ngay=ton_tren_30_ngay,
            top_centers=top_5_centers,
            overdue_30_centers=overdue_30_list,
            centers=centers,
            source_file_path=file_path,
            source_sheet_name=found_sheet_name
        )

        logger.info(
            f"Successfully read report data: tong_ton={tong_ton}, ton_qh={ton_qua_han}, "
            f"ton_>30={ton_tren_30_ngay}, th_ngay={thuc_hien_ngay}, top_5={top_5_centers}"
        )
        return report_data


class ExcelReaderWorker(QThread):
    """Worker thread to read large Excel files asynchronously without freezing GUI."""
    finished = Signal(object)  # Emits ReportData on success
    error = Signal(str)        # Emits error message on failure
    status_updated = Signal(str)

    def __init__(self, file_path: str, custom_date: Optional[date] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.file_path = file_path
        self.custom_date = custom_date

    def run(self):
        try:
            self.status_updated.emit("Đang mở file Excel...")
            reader = ExcelReader()
            self.status_updated.emit("Đang phân tích dữ liệu các trung tâm...")
            data = reader.read_report_data(self.file_path, self.custom_date)
            self.status_updated.emit("Hoàn thành đọc dữ liệu!")
            self.finished.emit(data)
        except Exception as e:
            logger.exception("Error in ExcelReaderWorker:")
            self.error.emit(str(e))
