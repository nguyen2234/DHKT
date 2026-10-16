"""
Excel Input Engine for WO Operations Center.
High-performance, read-only streaming parser that extracts and validates
all sheets (TH TTH, THFT, WO, Sheet2) into a unified ReportDataset.
Guards against large sheet memory exhaustion (e.g., Logfile 370k+ rows).
"""

import hashlib
import logging
import os
import re
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import openpyxl
from openpyxl.utils import column_index_from_string

from backend.domain.models import (
    CenterReport,
    CenterSummary,
    EmployeeFT,
    ProvinceSummary,
    ReportDataset,
    WorkOrder,
)

logger = logging.getLogger(__name__)


class ExcelEngineError(Exception):
    """Custom exception raised when Excel processing encounters fatal errors."""
    pass


class DiscrepancyWarning:
    """Carries warnings if summary rows differ from the sum of detail records."""
    pass


CENTER_CODE_PATTERN = re.compile(r"(?:VCC_NAN_\d{3}_|_)??([A-Z]{3})\b")

KNOWN_CENTER_MAPPING: Dict[str, str] = {
    "VPU": "Vinh Phú",
    "KLN": "Kim Liên",
    "NLC": "Nam Lộc",
    "DCU": "Diễn Châu",
    "YTH": "Yên Thành",
    "QLU": "Quỳnh Lưu",
    "THU": "Thanh Chương",
    "QHP": "Quỳ Hợp",
    "QPG": "Quế Phong",
    "TKY": "Tân Kỳ",
    "DDG": "Đô Lương",
    "VTG": "Vũ Quang / Vị Thủy",
    "TDG": "Tương Dương",
    "MXN": "Mường Xén / Kỳ Sơn"
}


def compute_file_fingerprint(file_path: str) -> str:
    """Computes a fast SHA-256 fingerprint based on file metadata and head/tail bytes."""
    try:
        stat = os.stat(file_path)
        hasher = hashlib.sha256()
        hasher.update(f"{stat.st_size}_{stat.st_mtime}".encode("utf-8"))
        with open(file_path, "rb") as f:
            chunk = f.read(65536)
            hasher.update(chunk)
            if stat.st_size > 65536:
                f.seek(max(0, stat.st_size - 65536))
                hasher.update(f.read(65536))
        return hasher.hexdigest()[:16]
    except Exception as e:
        logger.warning(f"Failed to calculate fingerprint for {file_path}: {e}")
        return "unknown_hash"


def extract_center_code_and_name(raw_text: str) -> Tuple[str, str]:
    """
    Extracts short 3-letter code and readable name from raw center string.
    Example:
        'Trung tâm Diễn Châu (VCC_NAN_004_DCU)' -> ('DCU', 'Diễn Châu')
        'QLU' -> ('QLU', 'Quỳnh Lưu')
        'VCC_NAN_001_VPU' -> ('VPU', 'Vinh Phú')
    """
    if not raw_text:
        return "KHAC", "Khác"

    raw_str = str(raw_text).strip()
    match = CENTER_CODE_PATTERN.search(raw_str)
    if match:
        code = match.group(1).upper()
    else:
        # Fallback check against known codes
        code = "KHAC"
        for k in KNOWN_CENTER_MAPPING.keys():
            if k in raw_str.upper():
                code = k
                break

    name = KNOWN_CENTER_MAPPING.get(code, "")
    if not name:
        # Extract readable name from prefix before '('
        if "(" in raw_str:
            clean = raw_str.split("(")[0].replace("Trung tâm", "").strip()
            name = clean or code
        else:
            name = raw_str

    return code, name


def safe_int(val: Any, default: int = 0) -> int:
    """Safely converts value to integer, handling formulas, floats, and formatted strings."""
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip().replace(",", "")
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return default


def safe_float(val: Any, default: float = 0.0) -> float:
    """Safely converts value to float."""
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", "").replace("%", "")
    try:
        v = float(s)
        if "%" in str(val):
            v = v / 100.0
        return v
    except (ValueError, TypeError):
        return default


class ExcelInputEngine:
    """Comprehensive, streaming Excel reader and domain builder."""

    def __init__(self, custom_mapping: Optional[Dict[str, Any]] = None):
        self.custom_mapping = custom_mapping or {}

    def parse_workbook(self, file_path: str, progress_callback: Optional[Callable[[int, str], None]] = None) -> ReportDataset:
        """
        Parses source workbook into a unified ReportDataset.
        Strictly READ-ONLY. Protects memory against large sheets.
        """
        if not os.path.exists(file_path):
            raise ExcelEngineError(f"Tệp không tồn tại: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".xlsx", ".xlsm"]:
            raise ExcelEngineError("Định dạng tệp không hợp lệ. Vui lòng chọn tệp Excel (.xlsx, .xlsm).")

        if progress_callback:
            progress_callback(5, "Đang kiểm tra cấu trúc workbook...")

        fingerprint = compute_file_fingerprint(file_path)

        # 1. Quick sheet names inspection
        try:
            wb_meta = openpyxl.load_workbook(file_path, read_only=True)
            available_sheets = wb_meta.sheetnames
            wb_meta.close()
        except Exception as e:
            raise ExcelEngineError(f"Không thể mở tệp Excel. Chi tiết: {str(e)}")

        logger.info(f"Detected sheets in {file_path}: {available_sheets}")

        # Locate essential sheets
        sheet_th_tth = self._find_sheet(available_sheets, ["TH TTH", "TH_TTH"])
        sheet_thft = self._find_sheet(available_sheets, ["THFT", "TH_FT"])
        sheet_wo = self._find_sheet(available_sheets, ["WO"])

        if not sheet_th_tth and not sheet_thft:
            raise ExcelEngineError(
                f"Tệp không chứa các sheet tổng hợp cần thiết ('TH TTH' hoặc 'THFT').\n"
                f"Các sheet hiện có trong tệp: {', '.join(available_sheets)}"
            )

        if progress_callback:
            progress_callback(15, "Đang mở tệp dữ liệu ở chế độ chỉ đọc...")

        # 2. Open workbook with data_only=True to read evaluated formulas
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        except Exception as e:
            raise ExcelEngineError(f"Lỗi khi nạp workbook dữ liệu: {str(e)}")

        centers_map: Dict[str, CenterReport] = {}

        # 3. Parse 'TH TTH' if present (Executive Provincial & Center Summary)
        province_summary: Optional[ProvinceSummary] = None
        detected_date_str = ""
        day_month_str = ""

        if sheet_th_tth and sheet_th_tth in wb.sheetnames:
            if progress_callback:
                progress_callback(30, "Đang phân tích số liệu điều hành toàn tỉnh (TH TTH)...")
            ws_tth = wb[sheet_th_tth]
            province_summary, detected_date_str, day_month_str, tth_centers = self._parse_th_tth(ws_tth)
            for c_code, c_summary in tth_centers.items():
                if c_code not in centers_map:
                    centers_map[c_code] = CenterReport(
                        center_code=c_code,
                        center_name=c_summary.name,
                        center_raw=c_summary.full_name,
                        summary=c_summary
                    )
                else:
                    centers_map[c_code].summary = c_summary

        # 4. Fallback date detection from filename if TH TTH had no date
        if not detected_date_str:
            detected_date_str, day_month_str = self._detect_date_from_filename(file_path)

        # 5. Parse 'THFT' (FT Employee metrics & TAG logic)
        total_employees = 0
        total_tagged = 0
        if sheet_thft and sheet_thft in wb.sheetnames:
            if progress_callback:
                progress_callback(55, "Đang phân tích nhân viên kỹ thuật và điều kiện TAG (THFT)...")
            ws_thft = wb[sheet_thft]
            thft_emps, total_employees, total_tagged = self._parse_thft(ws_thft)
            for emp in thft_emps:
                c_code = emp.center_code
                if c_code not in centers_map:
                    centers_map[c_code] = CenterReport(
                        center_code=c_code,
                        center_name=emp.center_name,
                        center_raw=emp.center_raw,
                        employees=[]
                    )
                centers_map[c_code].employees.append(emp)

        # 6. Parse 'WO' (Work Orders: Overdue, Pending, Boundary)
        total_wos = 0
        total_pending_wos = 0
        total_boundary_wos = 0
        if sheet_wo and sheet_wo in wb.sheetnames:
            if progress_callback:
                progress_callback(75, "Đang phân loại danh sách công việc (WO)...")
            ws_wo = wb[sheet_wo]
            wos, pending_wos, boundary_wos = self._parse_wo(ws_wo)

            for wo in wos:
                c_code = wo.center_code
                if c_code not in centers_map:
                    centers_map[c_code] = CenterReport(
                        center_code=c_code,
                        center_name=wo.center_name,
                        center_raw=wo.center_raw
                    )
                centers_map[c_code].work_orders.append(wo)
                total_wos += 1

            for pwo in pending_wos:
                c_code = pwo.center_code
                if c_code not in centers_map:
                    centers_map[c_code] = CenterReport(
                        center_code=c_code,
                        center_name=pwo.center_name,
                        center_raw=pwo.center_raw
                    )
                centers_map[c_code].pending_work_orders.append(pwo)
                total_pending_wos += 1

            for bwo in boundary_wos:
                c_code = bwo.center_code
                if c_code not in centers_map:
                    centers_map[c_code] = CenterReport(
                        center_code=c_code,
                        center_name=bwo.center_name,
                        center_raw=bwo.center_raw
                    )
                centers_map[c_code].boundary_work_orders.append(bwo)
                total_boundary_wos += 1

        # Close workbook
        wb.close()

        # Sort center work orders
        for center in centers_map.values():
            center.work_orders.sort(key=lambda w: (w.performer.lower(), str(w.deadline)))
            center.pending_work_orders.sort(key=lambda w: (w.performer.lower(), str(w.deadline)))
            center.boundary_work_orders.sort(key=lambda w: (w.performer.lower(), str(w.deadline)))

        # Fallback ProvinceSummary if TH TTH was absent
        if not province_summary:
            today = date.today()
            calc_tong_ton = sum(c.summary.tong_ton if c.summary else sum(e.ton for e in c.employees) for c in centers_map.values())
            calc_ton_qh = sum(c.summary.ton_qua_han if c.summary else sum(e.qua_han for e in c.employees) for c in centers_map.values())
            calc_ton_30 = sum(c.summary.ton_30_ngay if c.summary else sum(e.qua_han_30 for e in c.employees) for c in centers_map.values())
            calc_th_ngay = sum(c.summary.thuc_hien_ngay if c.summary else sum(e.thuc_hien_ngay for e in c.employees) for c in centers_map.values())

            sorted_centers = sorted(centers_map.values(), key=lambda c: c.summary.tong_ton if c.summary else sum(e.ton for e in c.employees), reverse=True)
            top_5 = [c.center_code for c in sorted_centers[:5]]
            overdue_30 = [(c.center_code, c.summary.ton_30_ngay if c.summary else sum(e.qua_han_30 for e in c.employees)) for c in centers_map.values() if (c.summary.ton_30_ngay if c.summary else sum(e.qua_han_30 for e in c.employees)) > 0]

            province_summary = ProvinceSummary(
                report_date=today,
                day=today.day,
                month=today.month,
                year=today.year,
                thuc_hien_ngay=calc_th_ngay,
                tong_ton=calc_tong_ton,
                ton_qua_han=calc_ton_qh,
                ton_tren_30_ngay=calc_ton_30,
                top_centers=top_5,
                overdue_30_centers=overdue_30
            )

        deadline_str = "05/10"
        meeting_time_str = "06:30"

        dataset = ReportDataset(
            file_path=file_path,
            file_fingerprint=fingerprint,
            detected_sheets=available_sheets,
            report_date_str=detected_date_str or f"{province_summary.day:02d}/{province_summary.month:02d}/{province_summary.year}",
            day_month_str=day_month_str or f"{province_summary.day}/{province_summary.month}",
            deadline_str=deadline_str,
            meeting_time_str=meeting_time_str,
            province_summary=province_summary,
            centers=centers_map,
            total_employees=total_employees,
            total_tagged=total_tagged
        )

        if progress_callback:
            progress_callback(100, f"Đã hoàn thành nạp {total_employees} FT, {total_wos} WO quá hạn, {total_pending_wos} WO trong hạn trên {len(centers_map)} trung tâm.")

        logger.info(
            f"Parsed dataset: {len(centers_map)} centers, {total_employees} FTs, "
            f"{total_wos} overdue WOs, {total_pending_wos} pending WOs, {total_boundary_wos} boundary WOs."
        )
        return dataset

    def _find_sheet(self, sheet_names: List[str], target_names: List[str]) -> Optional[str]:
        for target in target_names:
            for s in sheet_names:
                if s.strip().lower() == target.strip().lower():
                    return s
        for target in target_names:
            for s in sheet_names:
                if target.lower() in s.lower():
                    return s
        return None

    def _detect_date_from_filename(self, file_path: str) -> Tuple[str, str]:
        filename = os.path.basename(file_path)
        m8 = re.search(r"(\d{2})(\d{2})(\d{4})", filename)
        if m8:
            d, m, y = int(m8.group(1)), int(m8.group(2)), int(m8.group(3))
            if 1 <= d <= 31 and 1 <= m <= 12:
                return f"{d:02d}/{m:02d}/{y}", f"{d}/{m}"

        m_iso = re.search(r"(\d{4})(\d{2})(\d{2})", filename)
        if m_iso:
            y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
            if 1 <= d <= 31 and 1 <= m <= 12:
                return f"{d:02d}/{m:02d}/{y}", f"{d}/{m}"

        today = date.today()
        return f"{today.day:02d}/{today.month:02d}/{today.year}", f"{today.day}/{today.month}"

    def _parse_th_tth(self, ws) -> Tuple[ProvinceSummary, str, str, Dict[str, CenterSummary]]:
        """Parses sheet 'TH TTH' (Summary row 3, Centers rows 4..17)."""
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 3:
            raise ExcelEngineError("Sheet 'TH TTH' không đủ dữ liệu hàng tiêu đề và tổng hợp.")

        # Detect date from row 2 (col Y=25, AA=27) if available
        detected_date_str = ""
        day_month_str = ""
        if len(rows) >= 2:
            r2 = rows[1]
            val_y2 = r2[24] if len(r2) > 24 else None
            val_aa2 = r2[26] if len(r2) > 26 else None
            if isinstance(val_y2, (datetime, date)) and val_aa2 is not None:
                day_int = safe_int(val_aa2)
                if 1 <= day_int <= 31:
                    detected_date_str = f"{day_int:02d}/{val_y2.month:02d}/{val_y2.year}"
                    day_month_str = f"{day_int}/{val_y2.month}"

        summary_row = rows[2]  # Row 3 (0-indexed 2)
        raw_tong_ton = summary_row[16] if len(summary_row) > 16 else None
        raw_ton_qh = summary_row[17] if len(summary_row) > 17 else None
        raw_ton_30 = summary_row[18] if len(summary_row) > 18 else None
        raw_th_ngay = summary_row[19] if len(summary_row) > 19 else None

        centers: Dict[str, CenterSummary] = {}
        stt = 1
        calc_q = 0
        calc_r = 0
        calc_s = 0
        calc_t = 0

        for r_idx in range(3, len(rows)):
            row = rows[r_idx]
            if not row or not any(row):
                continue
            center_full_name = str(row[0] or "").strip()
            if not center_full_name or "tổng" in center_full_name.lower():
                continue

            code, name = extract_center_code_and_name(center_full_name)
            q_val = safe_int(row[16] if len(row) > 16 else 0)
            r_val = safe_int(row[17] if len(row) > 17 else 0)
            s_val = safe_int(row[18] if len(row) > 18 else 0)
            t_val = safe_int(row[19] if len(row) > 19 else 0)
            u_val = safe_int(row[20] if len(row) > 20 else 0)
            v_val = str(row[21] or "").strip() if len(row) > 21 else ""
            w_val = str(row[22] or "").strip() if len(row) > 22 else ""
            x_val = safe_float(row[23] if len(row) > 23 else 0.0)

            calc_q += q_val
            calc_r += r_val
            calc_s += s_val
            calc_t += t_val

            cs = CenterSummary(
                stt=stt,
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
            centers[code] = cs
            stt += 1

        # Reconcile summary row vs center totals
        val_q = safe_int(raw_tong_ton) if raw_tong_ton is not None else calc_q
        val_r = safe_int(raw_ton_qh) if raw_ton_qh is not None else calc_r
        val_s = safe_int(raw_ton_30) if raw_ton_30 is not None else calc_s
        val_t = safe_int(raw_th_ngay) if raw_th_ngay is not None else calc_t

        has_discrepancy = False
        disc_notes = []
        if raw_tong_ton is not None and val_q != calc_q and calc_q > 0:
            has_discrepancy = True
            disc_notes.append(f"Tổng tồn dòng 3 ({val_q}) khác tổng các huyện ({calc_q})")
        if raw_ton_qh is not None and val_r != calc_r and calc_r > 0:
            has_discrepancy = True
            disc_notes.append(f"Tồn quá hạn dòng 3 ({val_r}) khác tổng các huyện ({calc_r})")
        if raw_ton_30 is not None and val_s != calc_s and calc_s > 0:
            has_discrepancy = True
            disc_notes.append(f"Tồn >30N dòng 3 ({val_s}) khác tổng các huyện ({calc_s})")
        if raw_th_ngay is not None and val_t != calc_t and calc_t > 0:
            has_discrepancy = True
            disc_notes.append(f"TH ngày dòng 3 ({val_t}) khác tổng các huyện ({calc_t})")

        # Top 5 centers
        sorted_by_ton = sorted(centers.values(), key=lambda c: c.tong_ton, reverse=True)
        top_5 = [c.code for c in sorted_by_ton[:5]]
        overdue_30 = [(c.code, c.ton_30_ngay) for c in centers.values() if c.ton_30_ngay > 0]

        rep_date = date.today()
        if detected_date_str:
            try:
                parts = detected_date_str.split("/")
                rep_date = date(int(parts[2]), int(parts[1]), int(parts[0]))
            except Exception:
                pass

        prov = ProvinceSummary(
            report_date=rep_date,
            day=rep_date.day,
            month=rep_date.month,
            year=rep_date.year,
            thuc_hien_ngay=val_t,
            tong_ton=val_q,
            ton_qua_han=val_r,
            ton_tren_30_ngay=val_s,
            top_centers=top_5,
            overdue_30_centers=overdue_30,
            has_discrepancy=has_discrepancy,
            discrepancy_details="; ".join(disc_notes)
        )

        return prov, detected_date_str, day_month_str, centers

    def _parse_thft(self, ws) -> Tuple[List[EmployeeFT], int, int]:
        """Parses sheet 'THFT' dynamically detecting column layout (19 vs 20 columns)."""
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 4:
            raise ExcelEngineError("Sheet 'THFT' không đủ số hàng tiêu đề và nhân viên.")

        r1 = rows[0]
        r2 = rows[1]

        # Dynamic header detection
        # Check if Col B is Full Name or Center
        col_b_text = str(r1[1] or "").strip().lower()
        has_fullname_col = ("tên" in col_b_text or "họ và tên" in col_b_text or "fullname" in col_b_text)

        if has_fullname_col:
            # 20 columns layout
            idx_user = 0
            idx_name = 1
            idx_center = 2
            idx_pos = 3
            idx_q = 16
            idx_r = 17
            idx_s = 18
            idx_t = 19
            # ICMS details
            idx_icms_bd_nt_ton = 4
            idx_icms_bd_nt_qh = 5
            idx_icms_bd_nt_qh30 = 6
            idx_icms_bd_thc_ton = 7
            idx_icms_bd_thc_qh = 8
            idx_icms_bd_thc_qh30 = 9
            idx_icms_tt_tc_ton = 10
            idx_icms_tt_tc_qh = 11
            idx_icms_tt_tc_qh30 = 12
            idx_bao_hong_ton = 13
            idx_bao_hong_qh = 14
            idx_bao_hong_qh30 = 15
        else:
            # 19 columns layout (Col B is Center, Col C is Position, Col P is Tong Ton)
            idx_user = 0
            idx_name = None
            idx_center = 1
            idx_pos = 2
            idx_q = 15
            idx_r = 16
            idx_s = 17
            idx_t = 18
            # ICMS details
            idx_icms_bd_nt_ton = 3
            idx_icms_bd_nt_qh = 4
            idx_icms_bd_nt_qh30 = 5
            idx_icms_bd_thc_ton = 6
            idx_icms_bd_thc_qh = 7
            idx_icms_bd_thc_qh30 = 8
            idx_icms_tt_tc_ton = 9
            idx_icms_tt_tc_qh = 10
            idx_icms_tt_tc_qh30 = 11
            idx_bao_hong_ton = 12
            idx_bao_hong_qh = 13
            idx_bao_hong_qh30 = 14

        employees: List[EmployeeFT] = []
        tot_emps = 0
        tot_tagged = 0

        for r_idx in range(3, len(rows)):
            row = rows[r_idx]
            if not row or not any(row):
                continue

            username_val = row[idx_user] if len(row) > idx_user else None
            if not username_val:
                continue

            user_str = str(username_val).strip()
            if not user_str or "tổng" in user_str.lower():
                continue

            fullname_val = row[idx_name] if (idx_name is not None and len(row) > idx_name) else None
            fullname_str = str(fullname_val).strip() if fullname_val is not None else user_str

            center_val = row[idx_center] if len(row) > idx_center else ""
            center_raw_str = str(center_val).strip() if center_val is not None else "Khác"

            pos_val = row[idx_pos] if len(row) > idx_pos else ""
            pos_str = str(pos_val).strip() if pos_val is not None else ""

            ton_val = safe_int(row[idx_q] if len(row) > idx_q else 0)
            qua_han_val = safe_int(row[idx_r] if len(row) > idx_r else 0)
            qua_han_30_val = safe_int(row[idx_s] if len(row) > idx_s else 0)
            th_ngay_val = safe_int(row[idx_t] if len(row) > idx_t else 0)

            # AUTOMATIC TAGGING RULE: ton > 0 AND thuc_hien_ngay <= 0
            should_tag = (ton_val > 0 and th_ngay_val <= 0)

            c_code, c_name = extract_center_code_and_name(center_raw_str)

            emp = EmployeeFT(
                row_idx=r_idx + 1,
                username=user_str,
                full_name=fullname_str,
                center_raw=center_raw_str,
                center_code=c_code,
                center_name=c_name,
                position=pos_str,
                icms_bd_nt_ton=safe_int(row[idx_icms_bd_nt_ton] if len(row) > idx_icms_bd_nt_ton else 0),
                icms_bd_nt_qh=safe_int(row[idx_icms_bd_nt_qh] if len(row) > idx_icms_bd_nt_qh else 0),
                icms_bd_nt_qh30=safe_int(row[idx_icms_bd_nt_qh30] if len(row) > idx_icms_bd_nt_qh30 else 0),
                icms_bd_thc_ton=safe_int(row[idx_icms_bd_thc_ton] if len(row) > idx_icms_bd_thc_ton else 0),
                icms_bd_thc_qh=safe_int(row[idx_icms_bd_thc_qh] if len(row) > idx_icms_bd_thc_qh else 0),
                icms_bd_thc_qh30=safe_int(row[idx_icms_bd_thc_qh30] if len(row) > idx_icms_bd_thc_qh30 else 0),
                icms_tt_tc_ton=safe_int(row[idx_icms_tt_tc_ton] if len(row) > idx_icms_tt_tc_ton else 0),
                icms_tt_tc_qh=safe_int(row[idx_icms_tt_tc_qh] if len(row) > idx_icms_tt_tc_qh else 0),
                icms_tt_tc_qh30=safe_int(row[idx_icms_tt_tc_qh30] if len(row) > idx_icms_tt_tc_qh30 else 0),
                bao_hong_ton=safe_int(row[idx_bao_hong_ton] if len(row) > idx_bao_hong_ton else 0),
                bao_hong_qh=safe_int(row[idx_bao_hong_qh] if len(row) > idx_bao_hong_qh else 0),
                bao_hong_qh30=safe_int(row[idx_bao_hong_qh30] if len(row) > idx_bao_hong_qh30 else 0),
                ton=ton_val,
                qua_han=qua_han_val,
                qua_han_30=qua_han_30_val,
                thuc_hien_ngay=th_ngay_val,
                should_tag=should_tag
            )

            employees.append(emp)
            tot_emps += 1
            if should_tag:
                tot_tagged += 1

        return employees, tot_emps, tot_tagged

    def _parse_wo(self, ws) -> Tuple[List[WorkOrder], List[WorkOrder], List[WorkOrder]]:
        """Parses sheet 'WO' into Overdue (<0), Pending (>0), and Boundary/Zero/Blank records."""
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            return [], [], []

        overdue_wos: List[WorkOrder] = []
        pending_wos: List[WorkOrder] = []
        boundary_wos: List[WorkOrder] = []

        for r_idx in range(1, len(rows)):
            row = rows[r_idx]
            if not row or len(row) < 12:
                continue

            col_l = row[11]  # Col L (0-indexed 11): Ngày quá hạn
            classification = "boundary"

            if col_l is not None:
                if isinstance(col_l, (int, float)):
                    if col_l < 0:
                        classification = "overdue"
                    elif col_l > 0:
                        classification = "pending"
                else:
                    s_l = str(col_l).strip()
                    try:
                        val_l = float(s_l)
                        if val_l < 0:
                            classification = "overdue"
                        elif val_l > 0:
                            classification = "pending"
                    except (ValueError, TypeError):
                        classification = "boundary"

            tth_raw = str(row[12] or "").strip() if len(row) > 12 else ""
            c_code, c_name = extract_center_code_and_name(tth_raw)

            wo = WorkOrder(
                stt=row[0] if row[0] is not None else r_idx,
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
                center_name=c_name,
                classification=classification
            )

            if classification == "overdue":
                overdue_wos.append(wo)
            elif classification == "pending":
                pending_wos.append(wo)
            else:
                boundary_wos.append(wo)

        return overdue_wos, pending_wos, boundary_wos
