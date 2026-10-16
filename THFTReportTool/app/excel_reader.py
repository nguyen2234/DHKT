"""
Excel Reader module for THFT Report Tool.
Validates input file, safely extracts cached values, checks column formulas,
and builds the structured ReportDataset.
"""

import os
import re
import datetime
import logging
import openpyxl
from openpyxl.utils import column_index_from_string
from typing import Dict, Any, Tuple, Optional, List

from .models import EmployeeFT, CenterReport, ReportDataset, WorkOrder
from .utils import parse_center, safe_int, parse_report_date

logger = logging.getLogger(__name__)


class ExcelValidationError(Exception):
    """Raised when the Excel file does not match expected THFT report structure."""
    pass


class ExcelUncalculatedError(Exception):
    """Raised when Excel formulas were not calculated or cached."""
    pass


class ExcelReader:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.columns_cfg = config.get("columns", {})
        self.sheet_target = config.get("sheet_name", "THFT")

    def read_report_file(self, file_path: str, progress_callback=None) -> ReportDataset:
        """
        Reads and validates the Excel file, returning a populated ReportDataset.
        Raises ExcelValidationError or ExcelUncalculatedError on validation issues.
        """
        if not os.path.exists(file_path):
            raise ExcelValidationError(f"File không tồn tại: {file_path}")

        if progress_callback:
            progress_callback(10, "Đang mở file Excel...")

        # 1. Inspect sheet names first
        try:
            wb_meta = openpyxl.load_workbook(file_path, read_only=True)
            sheet_names = wb_meta.sheetnames
            wb_meta.close()
        except Exception as e:
            raise ExcelValidationError(f"Không thể mở file Excel. Lỗi: {str(e)}")

        # Find target sheet
        target_sheet_name = self._find_target_sheet(sheet_names)
        if not target_sheet_name:
            sheets_str = ", ".join(sheet_names)
            raise ExcelValidationError(
                f"File không chứa sheet '{self.sheet_target}'.\n"
                f"Các sheet hiện có: {sheets_str}.\n"
                "Vui lòng chọn đúng file báo cáo ĐH WO UT1!"
            )

        if progress_callback:
            progress_callback(25, f"Đang đọc dữ liệu từ sheet '{target_sheet_name}'...")

        # 2. Try to detect date from 'TH TTH' or filename
        detected_date, day_month = self._detect_report_date(file_path, sheet_names)

        # Find WO sheet if available
        wo_sheet_name = self._find_wo_sheet(sheet_names)

        # 3. Load with data_only=True to get calculated cached values
        all_wo_rows = []
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb[target_sheet_name]
            all_rows = list(ws.iter_rows(values_only=True))

            if wo_sheet_name and wo_sheet_name in wb.sheetnames:
                try:
                    ws_wo = wb[wo_sheet_name]
                    all_wo_rows = list(ws_wo.iter_rows(values_only=True))
                except Exception as e:
                    logger.warning(f"Không thể đọc sheet WO '{wo_sheet_name}': {e}")

            wb.close()
        except Exception as e:
            raise ExcelValidationError(f"Lỗi khi đọc file Excel: {str(e)}")

        if not all_rows or len(all_rows) < 4:
            raise ExcelValidationError(
                f"Sheet '{target_sheet_name}' không có đủ dữ liệu (ít hơn 4 hàng)."
            )

        if progress_callback:
            progress_callback(50, "Đang kiểm tra cấu trúc tiêu đề và cột...")

        # 4. Validate header rows and columns
        header_row_1 = all_rows[0]
        header_row_2 = all_rows[1]
        self._validate_headers(header_row_1, header_row_2)

        if progress_callback:
            progress_callback(70, "Đang xử lý dữ liệu nhân viên và logic TAG...")

        # 5. Extract employees starting from data_start_row (row index 3 = 4th row)
        data_start_idx = self.config.get("data_start_row", 4) - 1
        centers_map: Dict[str, CenterReport] = {}
        total_employees = 0
        total_tagged = 0
        formula_count = 0

        # Column indices (0-based)
        col_map = self._get_col_indices()

        for r_idx in range(data_start_idx, len(all_rows)):
            row = all_rows[r_idx]
            if not row:
                continue

            username_val = row[col_map["username"]] if col_map["username"] < len(row) else None
            fullname_val = row[col_map["full_name"]] if col_map["full_name"] < len(row) else None
            center_val = row[col_map["center"]] if col_map["center"] < len(row) else None

            # Skip blank rows
            if not username_val and not fullname_val:
                continue

            username_str = str(username_val).strip() if username_val is not None else ""
            fullname_str = str(fullname_val).strip() if fullname_val is not None else ""
            center_raw_str = str(center_val).strip() if center_val is not None else "Khác"
            pos_val = row[col_map["position"]] if col_map["position"] < len(row) else ""
            pos_str = str(pos_val).strip() if pos_val is not None else ""

            # Check if values are uncalculated formula strings (e.g. starts with '=')
            raw_q = row[col_map["ton"]] if col_map["ton"] < len(row) else 0
            raw_t = row[col_map["thuc_hien_ngay"]] if col_map["thuc_hien_ngay"] < len(row) else 0

            if isinstance(raw_q, str) and raw_q.startswith("="):
                formula_count += 1
            if isinstance(raw_t, str) and raw_t.startswith("="):
                formula_count += 1

            ton_val = safe_int(raw_q)
            thuc_hien_ngay_val = safe_int(raw_t)

            # Detail counts
            icms_bd_nt_ton = safe_int(row[col_map["icms_bd_nt_ton"]]) if col_map["icms_bd_nt_ton"] < len(row) else 0
            icms_bd_nt_qh = safe_int(row[col_map["icms_bd_nt_qh"]]) if col_map["icms_bd_nt_qh"] < len(row) else 0
            icms_bd_nt_qh30 = safe_int(row[col_map["icms_bd_nt_qh30"]]) if col_map["icms_bd_nt_qh30"] < len(row) else 0

            icms_bd_thc_ton = safe_int(row[col_map["icms_bd_thc_ton"]]) if col_map["icms_bd_thc_ton"] < len(row) else 0
            icms_bd_thc_qh = safe_int(row[col_map["icms_bd_thc_qh"]]) if col_map["icms_bd_thc_qh"] < len(row) else 0
            icms_bd_thc_qh30 = safe_int(row[col_map["icms_bd_thc_qh30"]]) if col_map["icms_bd_thc_qh30"] < len(row) else 0

            icms_tt_tc_ton = safe_int(row[col_map["icms_tt_tc_ton"]]) if col_map["icms_tt_tc_ton"] < len(row) else 0
            icms_tt_tc_qh = safe_int(row[col_map["icms_tt_tc_qh"]]) if col_map["icms_tt_tc_qh"] < len(row) else 0
            icms_tt_tc_qh30 = safe_int(row[col_map["icms_tt_tc_qh30"]]) if col_map["icms_tt_tc_qh30"] < len(row) else 0

            bao_hong_ton = safe_int(row[col_map["bao_hong_ton"]]) if col_map["bao_hong_ton"] < len(row) else 0
            bao_hong_qh = safe_int(row[col_map["bao_hong_qh"]]) if col_map["bao_hong_qh"] < len(row) else 0
            bao_hong_qh30 = safe_int(row[col_map["bao_hong_qh30"]]) if col_map["bao_hong_qh30"] < len(row) else 0

            qua_han = safe_int(row[col_map["qua_han"]]) if col_map["qua_han"] < len(row) else 0
            qua_han_30 = safe_int(row[col_map["qua_han_30"]]) if col_map["qua_han_30"] < len(row) else 0

            # CRITICAL BUSINESS RULE:
            # Q > 0 AND T <= 0 (rỗng hoặc <= 0)
            should_tag = (ton_val > 0 and thuc_hien_ngay_val <= 0)

            c_code, c_name = parse_center(center_raw_str)

            emp = EmployeeFT(
                row_idx=r_idx + 1,
                username=username_str,
                full_name=fullname_str,
                center_raw=center_raw_str,
                center_code=c_code,
                center_name=c_name,
                position=pos_str,
                icms_bd_nt_ton=icms_bd_nt_ton,
                icms_bd_nt_qh=icms_bd_nt_qh,
                icms_bd_nt_qh30=icms_bd_nt_qh30,
                icms_bd_thc_ton=icms_bd_thc_ton,
                icms_bd_thc_qh=icms_bd_thc_qh,
                icms_bd_thc_qh30=icms_bd_thc_qh30,
                icms_tt_tc_ton=icms_tt_tc_ton,
                icms_tt_tc_qh=icms_tt_tc_qh,
                icms_tt_tc_qh30=icms_tt_tc_qh30,
                bao_hong_ton=bao_hong_ton,
                bao_hong_qh=bao_hong_qh,
                bao_hong_qh30=bao_hong_qh30,
                ton=ton_val,
                qua_han=qua_han,
                qua_han_30=qua_han_30,
                thuc_hien_ngay=thuc_hien_ngay_val,
                should_tag=should_tag
            )

            if c_code not in centers_map:
                centers_map[c_code] = CenterReport(
                    center_code=c_code,
                    center_name=c_name,
                    center_raw=center_raw_str,
                    employees=[]
                )

            centers_map[c_code].employees.append(emp)
            total_employees += 1
            if should_tag:
                total_tagged += 1

        if formula_count > 5:
            logger.warning(f"Detected {formula_count} uncalculated formula strings in dataset.")
            raise ExcelUncalculatedError(
                "File Excel chưa được tính toán đầy đủ giá trị (cached calculated values).\n"
                "Vui lòng mở file bằng Microsoft Excel, nhấn Ctrl+S (Save) và thử lại."
            )

        if total_employees == 0:
            raise ExcelValidationError("Không tìm thấy dữ liệu nhân viên FT trong sheet.")

        # 6. Extract Work Orders from sheet WO (quá hạn: cột L < 0, tồn chưa quá hạn: cột L > 0)
        total_wos = 0
        total_pending_wos = 0
        if all_wo_rows and len(all_wo_rows) >= 2:
            if progress_callback:
                progress_callback(85, "Đang trích xuất danh sách WO quá hạn và tồn chưa quá hạn theo từng huyện...")

            for r_idx in range(1, len(all_wo_rows)):
                row = all_wo_rows[r_idx]
                if not row or len(row) < 12:
                    continue

                col_l = row[11]
                # Condition: Cột L có giá trị âm (< 0) là quá hạn, dương (> 0) là tồn chưa quá hạn
                if col_l is None:
                    continue
                is_negative = False
                is_positive = False
                if isinstance(col_l, (int, float)):
                    is_negative = (col_l < 0)
                    is_positive = (col_l > 0)
                else:
                    s_l = str(col_l).strip()
                    try:
                        val_l = float(s_l)
                        is_negative = (val_l < 0)
                        is_positive = (val_l > 0)
                    except (ValueError, TypeError):
                        is_negative = False
                        is_positive = False

                if not (is_negative or is_positive):
                    continue

                tth_raw = str(row[12] or "").strip() if len(row) > 12 else ""
                c_code, c_name = parse_center(tth_raw)

                stt_val = row[0] if row[0] is not None else (total_wos + total_pending_wos + 1)
                wo = WorkOrder(
                    stt=stt_val,
                    code=str(row[1] or "").strip() if len(row) > 1 and row[1] is not None else "",
                    job_type=str(row[2] or "").strip() if len(row) > 2 and row[2] is not None else "",
                    content=str(row[3] or "").strip() if len(row) > 3 and row[3] is not None else "",
                    deadline=str(row[4] or "").strip() if len(row) > 4 and row[4] is not None else "",
                    status=str(row[5] or "").strip() if len(row) > 5 and row[5] is not None else "",
                    performer=str(row[6] or "").strip() if len(row) > 6 and row[6] is not None else "",
                    station_code=str(row[7] or "").strip() if len(row) > 7 and row[7] is not None else "",
                    ft_comment=str(row[8] or "").strip() if len(row) > 8 and row[8] is not None else "",
                    ft_mobile=str(row[9] or "").strip() if len(row) > 9 and row[9] is not None else "",
                    completed_date=str(row[10] or "").strip() if len(row) > 10 and row[10] is not None else "",
                    overdue_days=col_l,
                    center_raw=tth_raw,
                    bkk=str(row[13] or "").strip() if len(row) > 13 and row[13] is not None else "",
                    bkk_reason=str(row[14] or "").strip() if len(row) > 14 and row[14] is not None else "",
                    center_code=c_code,
                    center_name=c_name
                )

                if c_code not in centers_map:
                    centers_map[c_code] = CenterReport(
                        center_code=c_code,
                        center_name=c_name,
                        center_raw=tth_raw,
                        employees=[],
                        work_orders=[],
                        pending_work_orders=[]
                    )

                if is_negative:
                    centers_map[c_code].work_orders.append(wo)
                    total_wos += 1
                elif is_positive:
                    centers_map[c_code].pending_work_orders.append(wo)
                    total_pending_wos += 1

            # Sắp xếp WO trong từng huyện theo nhân viên thực hiện rồi đến thời điểm yêu cầu kết thúc
            for c_code, center in centers_map.items():
                center.work_orders.sort(key=lambda w: (w.performer.lower(), str(w.deadline)))
                center.pending_work_orders.sort(key=lambda w: (w.performer.lower(), str(w.deadline)))

            logger.info(f"Loaded {total_wos} overdue WOs and {total_pending_wos} pending WOs across {len(centers_map)} centers.")

        if progress_callback:
            msg_wo = []
            if total_wos > 0:
                msg_wo.append(f"{total_wos} WO quá hạn")
            if total_pending_wos > 0:
                msg_wo.append(f"{total_pending_wos} WO tồn chưa quá hạn")
            msg_suffix = f", {', '.join(msg_wo)}" if msg_wo else ""
            progress_callback(100, f"Đọc thành công: {total_employees} FT, {len(centers_map)} huyện{msg_suffix}.")

        deadline = self.config.get("notification", {}).get("deadline", "05/10")
        meeting_time = self.config.get("notification", {}).get("meeting_time", "06:30")

        return ReportDataset(
            file_path=file_path,
            sheet_name=target_sheet_name,
            report_date_str=detected_date,
            day_month_str=day_month,
            deadline_str=deadline,
            meeting_time_str=meeting_time,
            centers=centers_map,
            total_employees=total_employees,
            total_tagged=total_tagged
        )

    def _find_target_sheet(self, sheet_names: List[str]) -> Optional[str]:
        # exact match
        for s in sheet_names:
            if s.strip().lower() == self.sheet_target.strip().lower():
                return s
        # contains THFT
        for s in sheet_names:
            if "thft" in s.lower() or "th_ft" in s.lower():
                return s
        return None

    def _find_wo_sheet(self, sheet_names: List[str]) -> Optional[str]:
        for s in sheet_names:
            if s.strip().upper() == "WO":
                return s
        for s in sheet_names:
            if s.strip().upper().startswith("WO"):
                return s
        return None

    def _detect_report_date(self, file_path: str, sheet_names: List[str]) -> Tuple[str, str]:
        """Attempts to read date from 'TH TTH' sheet, otherwise uses filename or current date."""
        filename = os.path.basename(file_path)

        if "TH TTH" in sheet_names:
            try:
                wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
                ws = wb["TH TTH"]
                # Cell Y2 might contain end date datetime(2026, 9, 30)
                # Cell AA2 might contain current day (28)
                val_y2 = ws.cell(row=2, column=25).value # Y is 25
                val_aa2 = ws.cell(row=2, column=27).value # AA is 27
                wb.close()

                if isinstance(val_y2, (datetime.datetime, datetime.date)) and val_aa2 is not None:
                    day_int = safe_int(val_aa2)
                    if 1 <= day_int <= 31:
                        full = f"{day_int:02d}/{val_y2.month:02d}/{val_y2.year}"
                        dm = f"{day_int}/{val_y2.month}"
                        return full, dm
            except Exception as e:
                logger.debug(f"Could not read date from TH TTH: {e}")

        return parse_report_date(filename=filename)

    def _get_col_indices(self) -> Dict[str, int]:
        """Converts column letter mappings from config into 0-based integer indices."""
        indices = {}
        for key, letter in self.columns_cfg.items():
            try:
                indices[key] = column_index_from_string(letter) - 1
            except Exception:
                indices[key] = 0
        return indices

    def _validate_headers(self, r1: Tuple[Any, ...], r2: Tuple[Any, ...]):
        """Validates that header rows contain essential columns, especially Q (Tồn) and T (Thực hiện ngày)."""
        # Column Q is 1-based 17 -> 0-based 16
        # Column T is 1-based 20 -> 0-based 19
        if len(r1) < 17 or len(r2) < 20:
            raise ExcelValidationError(
                f"File thiếu các cột cần thiết. Số cột hiện tại: {max(len(r1), len(r2))}, "
                "yêu cầu tối thiểu 20 cột (A đến T)."
            )

        # Validate Column A (FT), B (Tên FT), C (TTH), D (Vị trí)
        col_a_text = str(r1[0] or "").strip().lower()
        if "ft" not in col_a_text:
            logger.warning(f"Cột A header='{r1[0]}' không chứa 'FT'")

        # Validate Column Q (Tổng Tồn)
        # In r1 col 16: "Tổng", in r2 col 16: "Tồn"
        r1_q = str(r1[16] or "").strip().lower()
        r2_q = str(r2[16] or "").strip().lower()
        if "tồn" not in r2_q and "tong" not in r1_q and "tổng" not in r1_q:
            logger.warning(f"Cột Q header1='{r1[16]}', header2='{r2[16]}' có thể không phải cột Tồn!")

        # Validate Column T (Thực hiện ngày)
        r2_t = str(r2[19] or "").strip().lower()
        if "thực hiện" not in r2_t and "thuc hien" not in r2_t and "ngày" not in r2_t:
            logger.warning(f"Cột T header2='{r2[19]}' có thể không phải cột Thực hiện ngày!")
