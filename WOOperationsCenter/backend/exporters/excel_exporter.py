"""
Excel Exporter for WO Operations Center.
Generates fully styled Excel workbooks for:
1. Executive WO Report ('BaoCao' overview + 'ChiTiet' table)
2. THFT Center Reports (1 sheet per center, with Notification, Employee Table,
   Overdue WO Table, and Pending WO Table)
Atomic file generation, professional borders, color styling, and A4 Landscape print setup.
"""

import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from backend.domain.models import CenterReport, ProvinceSummary, ReportDataset

logger = logging.getLogger(__name__)


def safe_sheet_title(name: str) -> str:
    """Sanitizes worksheet title to comply with Excel limitations (max 31 chars, no invalid chars)."""
    clean = re.sub(r'[\\/*?:\[\]]', '_', name.strip())
    return clean[:31] if clean else "Sheet"


def get_unique_output_path(base_path: str) -> str:
    """Ensures file is never silently overwritten by appending timestamp or index if file exists."""
    if not os.path.exists(base_path):
        return base_path

    directory, filename = os.path.split(base_path)
    name, ext = os.path.splitext(filename)
    counter = 1
    while True:
        new_path = os.path.join(directory, f"{name}_{counter}{ext}")
        if not os.path.exists(new_path):
            return new_path
        counter += 1


class ExcelExporter:
    """Exports both Executive and Center-level reports to Excel with exact business styling."""

    # Color Palette
    COLOR_HEADER_NAVY = "1E3A8A"
    COLOR_FT_GREEN = "92D050"
    COLOR_ICMS_NT = "EBF1DE"
    COLOR_ICMS_THC = "FDE9D9"
    COLOR_ICMS_TC = "92CDDC"
    COLOR_BAO_HONG = "0070C0"
    COLOR_TH_RED = "FF0000"
    COLOR_SUBTOTAL_YELLOW = "FEF3C7"
    COLOR_WO_NAVY = "1F4E78"
    COLOR_PENDING_GREEN = "135E48"

    @classmethod
    def export_executive_report(
        cls,
        summary: ProvinceSummary,
        centers: List[CenterReport],
        output_dir: str,
        preview_text: str = "",
        custom_filename: Optional[str] = None
    ) -> str:
        """
        Exports Module A: Executive WO Report.
        Sheet 'BaoCao' (summary + message) & Sheet 'ChiTiet' (all centers table).
        """
        os.makedirs(output_dir, exist_ok=True)
        date_str = f"{summary.year}{summary.month:02d}{summary.day:02d}"
        filename = custom_filename or f"BaoCao_WO_{date_str}.xlsx"
        target_path = get_unique_output_path(os.path.join(output_dir, filename))
        temp_path = target_path + ".tmp"

        wb = openpyxl.Workbook()

        # Sheet 1: BaoCao
        ws_bc = wb.active
        ws_bc.title = "BaoCao"
        ws_bc.views.sheetView[0].showGridLines = True

        cls._style_baocao_sheet(ws_bc, summary, preview_text)

        # Sheet 2: ChiTiet
        ws_ct = wb.create_sheet(title="ChiTiet")
        ws_ct.views.sheetView[0].showGridLines = True

        cls._style_chitiet_sheet(ws_ct, summary, centers)

        # Atomic save
        wb.save(temp_path)
        wb.close()
        os.replace(temp_path, target_path)
        logger.info(f"Executive WO Report successfully exported to {target_path}")
        return target_path

    @classmethod
    def export_thft_reports(
        cls,
        dataset: ReportDataset,
        notifications: Dict[str, str],
        output_dir: str,
        selected_center_codes: Optional[List[str]] = None,
        separate_files: bool = False,
        position_filter: str = "Tất cả",
        fit_to_page: bool = True,
        custom_filename: Optional[str] = None
    ) -> List[str]:
        """
        Exports Module B: THFT Reports.
        Either all selected centers in one workbook, or separate workbooks per center.
        """
        os.makedirs(output_dir, exist_ok=True)
        active_codes = selected_center_codes or list(dataset.centers.keys())

        # Determine file suffix based on position filter
        pos_suffix = ""
        pos_upper = position_filter.strip().upper()
        if "DM" in pos_upper:
            pos_suffix = "_NVDM"
        elif "TRẠM" in pos_upper or "TRAM" in pos_upper:
            pos_suffix = "_NVNhaTram"

        date_suffix = dataset.report_date_str.replace("/", "") if dataset.report_date_str else datetime.now().strftime("%Y%m%d")

        exported_paths = []

        if separate_files:
            for code in active_codes:
                center = dataset.centers.get(code)
                if not center:
                    continue
                filename = f"BaoCao_THFT_{code}_{date_suffix}{pos_suffix}.xlsx"
                if len(active_codes) == 1 and custom_filename:
                    filename = custom_filename
                target_path = get_unique_output_path(os.path.join(output_dir, filename))
                temp_path = target_path + ".tmp"

                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = safe_sheet_title(code)
                ws.views.sheetView[0].showGridLines = True

                notif_text = notifications.get(code, "")
                cls._render_center_sheet(ws, center, notif_text, fit_to_page)

                wb.save(temp_path)
                wb.close()
                os.replace(temp_path, target_path)
                exported_paths.append(target_path)
        else:
            filename = custom_filename or f"BaoCao_THFT_{date_suffix}{pos_suffix}.xlsx"
            target_path = get_unique_output_path(os.path.join(output_dir, filename))
            temp_path = target_path + ".tmp"

            wb = openpyxl.Workbook()
            # Remove initial default sheet
            first_sheet = True

            for code in active_codes:
                center = dataset.centers.get(code)
                if not center:
                    continue

                if first_sheet:
                    ws = wb.active
                    ws.title = safe_sheet_title(code)
                    first_sheet = False
                else:
                    ws = wb.create_sheet(title=safe_sheet_title(code))

                ws.views.sheetView[0].showGridLines = True
                notif_text = notifications.get(code, "")
                cls._render_center_sheet(ws, center, notif_text, fit_to_page)

            wb.save(temp_path)
            wb.close()
            os.replace(temp_path, target_path)
            exported_paths.append(target_path)

        logger.info(f"THFT Reports successfully exported: {len(exported_paths)} file(s).")
        return exported_paths

    # ==========================================
    # SHEET BUILDERS & STYLING
    # ==========================================

    @classmethod
    def _style_baocao_sheet(cls, ws, summary: ProvinceSummary, preview_text: str):
        thin_side = Side(border_style="thin", color="CBD5E1")
        border_thin = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        font_title = Font(name="Arial", size=16, bold=True, color="1E3A8A")
        font_sub = Font(name="Arial", size=10, italic=True, color="64748B")
        font_sec = Font(name="Arial", size=12, bold=True, color="0F172A")
        font_bold = Font(name="Arial", size=11, bold=True, color="000000")
        font_metric = Font(name="Arial", size=13, bold=True, color="DC2626")
        font_reg = Font(name="Arial", size=11, color="1E293B")

        fill_header = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        fill_metric = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")

        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")
        align_top_left = Alignment(horizontal="left", vertical="top", wrap_text=True)

        # Title
        ws.merge_cells("A1:G1")
        ws["A1"] = f"BÁO CÁO TIẾN ĐỘ CẮT TỒN WO THÁNG {summary.month}"
        ws["A1"].font = font_title
        ws["A1"].alignment = align_center
        ws.row_dimensions[1].height = 36

        # Subtitle
        ws.merge_cells("A2:G2")
        ws["A2"] = f"Thời điểm báo cáo: Ngày {summary.day:02d}/{summary.month:02d}/{summary.year}"
        ws["A2"].font = font_sub
        ws["A2"].alignment = align_center
        ws.row_dimensions[2].height = 20

        # Section 1
        ws.merge_cells("A4:G4")
        ws["A4"] = "I. CHỈ SỐ TỔNG HỢP TOÀN TỈNH"
        ws["A4"].font = font_sec

        headers = [("A5:B5", "Thực hiện ngày"), ("C5", "Tổng tồn WO"), ("D5", "Tồn quá hạn"), ("E5", "Tồn >30 ngày"), ("F5:G5", "Top 5 trung tâm tồn cao")]
        ws.merge_cells("A5:B5")
        ws["A5"] = "Thực hiện ngày"
        ws["C5"] = "Tổng tồn WO"
        ws["D5"] = "Tồn quá hạn"
        ws["E5"] = "Tồn >30 ngày"
        ws.merge_cells("F5:G5")
        ws["F5"] = "Top 5 trung tâm tồn cao"

        for col in ["A5", "B5", "C5", "D5", "E5", "F5", "G5"]:
            c = ws[col]
            c.font = font_bold
            c.fill = fill_header
            c.alignment = align_center
            c.border = border_thin
        ws.row_dimensions[5].height = 25

        ws.merge_cells("A6:B6")
        ws["A6"] = f"{summary.thuc_hien_ngay} WO"
        ws["C6"] = f"{summary.tong_ton} WO"
        ws["D6"] = f"{summary.ton_qua_han} WO"

        detail_30 = ""
        if summary.overdue_30_centers:
            detail_30 = " (" + ", ".join(f"{c}:{cnt}" for c, cnt in summary.overdue_30_centers) + ")"
        ws["E6"] = f"{summary.ton_tren_30_ngay} WO{detail_30}"
        ws.merge_cells("F6:G6")
        ws["F6"] = ", ".join(summary.top_centers)

        for col in ["A6", "B6", "C6", "D6", "E6", "F6", "G6"]:
            c = ws[col]
            c.font = font_metric if col in ["A6", "C6", "D6", "E6"] else font_bold
            c.fill = fill_metric
            c.alignment = align_center
            c.border = border_thin
        ws.row_dimensions[6].height = 30

        # Section 2: TAMMI Message
        ws.merge_cells("A8:G8")
        ws["A8"] = "II. NỘI DUNG THÔNG BÁO / ĐIỀU HÀNH (GỬI LÊN TAMMI)"
        ws["A8"].font = font_sec

        ws.merge_cells("A9:G17")
        ws["A9"] = preview_text or ""
        ws["A9"].font = font_reg
        ws["A9"].alignment = align_top_left

        for r in range(9, 18):
            for c in range(1, 8):
                ws.cell(row=r, column=c).border = border_thin

        col_widths = {"A": 16, "B": 18, "C": 16, "D": 16, "E": 20, "F": 16, "G": 22}
        for col_l, w in col_widths.items():
            ws.column_dimensions[col_l].width = w

    @classmethod
    def _style_chitiet_sheet(cls, ws, summary: ProvinceSummary, centers: List[CenterReport]):
        thin_side = Side(border_style="thin", color="CBD5E1")
        border_thin = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        font_header = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        font_reg = Font(name="Arial", size=11, color="1E293B")
        font_bold = Font(name="Arial", size=11, bold=True, color="000000")

        fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        fill_total = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")

        headers = ["STT", "Mã TT", "Tên trung tâm", "Tổng tồn", "Tồn quá hạn", "Tồn >30 ngày", "TH Ngày", "KH Ngày", "Tỷ lệ HT Ngày", "Đánh giá", "Họp Ngày"]
        ws.row_dimensions[1].height = 28
        for col_idx, h in enumerate(headers, 1):
            c = ws.cell(row=1, column=col_idx, value=h)
            c.font = font_header
            c.fill = fill_header
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = border_thin

        curr_row = 2
        for center in centers:
            cs = center.summary
            ws.row_dimensions[curr_row].height = 20

            stt_val = cs.stt if cs else curr_row - 1
            code_val = center.center_code
            full_name_val = cs.full_name if cs else center.center_raw
            tong_ton_val = cs.tong_ton if cs else sum(e.ton for e in center.employees)
            ton_qh_val = cs.ton_qua_han if cs else sum(e.qua_han for e in center.employees)
            ton_30_val = cs.ton_30_ngay if cs else sum(e.qua_han_30 for e in center.employees)
            th_ngay_val = cs.thuc_hien_ngay if cs else sum(e.thuc_hien_ngay for e in center.employees)
            kh_ngay_val = cs.kh_ngay if cs else 0
            ty_le_val = cs.ty_le_ht_ngay if cs else 0.0
            danh_gia_val = cs.danh_gia if cs else ""
            hop_ngay_val = cs.hop_ngay if cs else ""

            ws.cell(row=curr_row, column=1, value=stt_val).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=2, value=code_val).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=3, value=full_name_val).alignment = Alignment(horizontal="left")
            ws.cell(row=curr_row, column=4, value=tong_ton_val).alignment = Alignment(horizontal="right")
            ws.cell(row=curr_row, column=5, value=ton_qh_val).alignment = Alignment(horizontal="right")
            ws.cell(row=curr_row, column=6, value=ton_30_val).alignment = Alignment(horizontal="right")
            ws.cell(row=curr_row, column=7, value=th_ngay_val).alignment = Alignment(horizontal="right")
            ws.cell(row=curr_row, column=8, value=kh_ngay_val).alignment = Alignment(horizontal="right")

            pct_c = ws.cell(row=curr_row, column=9, value=ty_le_val)
            pct_c.number_format = "0.0%"
            pct_c.alignment = Alignment(horizontal="right")

            ws.cell(row=curr_row, column=10, value=danh_gia_val).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=11, value=hop_ngay_val).alignment = Alignment(horizontal="center")

            for c in range(1, 12):
                cell = ws.cell(row=curr_row, column=c)
                cell.border = border_thin
                cell.font = font_reg

            curr_row += 1

        # Total Row
        ws.row_dimensions[curr_row].height = 24
        tot_c = ws.cell(row=curr_row, column=3, value="TỔNG CỘNG TOÀN TỈNH")
        tot_c.font = font_bold

        ws.cell(row=curr_row, column=4, value=summary.tong_ton).alignment = Alignment(horizontal="right")
        ws.cell(row=curr_row, column=5, value=summary.ton_qua_han).alignment = Alignment(horizontal="right")
        ws.cell(row=curr_row, column=6, value=summary.ton_tren_30_ngay).alignment = Alignment(horizontal="right")
        ws.cell(row=curr_row, column=7, value=summary.thuc_hien_ngay).alignment = Alignment(horizontal="right")

        sum_kh = sum(c.summary.kh_ngay for c in centers if c.summary)
        ws.cell(row=curr_row, column=8, value=sum_kh).alignment = Alignment(horizontal="right")
        overall_pct = (summary.thuc_hien_ngay / sum_kh) if sum_kh > 0 else 0.0
        tot_pct = ws.cell(row=curr_row, column=9, value=overall_pct)
        tot_pct.number_format = "0.0%"
        tot_pct.alignment = Alignment(horizontal="right")

        for c in range(1, 12):
            cell = ws.cell(row=curr_row, column=c)
            cell.font = font_bold
            cell.fill = fill_total
            cell.border = border_thin

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:K{curr_row - 1}"

        for col in ws.columns:
            max_l = max(len(str(c.value or "")) for c in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_l + 4, 12)
        ws.column_dimensions["C"].width = 44

    @classmethod
    def _render_center_sheet(cls, ws, center: CenterReport, notification: str, fit_to_page: bool = True):
        """
        Renders complete center sheet:
        1. Notification card (A1:T1)
        2. Employee Table (Rows 3..N)
        3. Overdue WO Table (Navy Blue banner)
        4. Pending WO Table (Forest Green banner)
        """
        thin_side = Side(border_style="thin", color="000000")
        border_box = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        # 1. Notification Card
        ws.merge_cells("A1:T2")
        cell_a1 = ws["A1"]
        cell_a1.value = notification
        cell_a1.font = Font(name="Arial", size=11, bold=True, color="1E293B")
        cell_a1.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        fill_notif = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        for r in range(1, 3):
            for c in range(1, 21):
                cell = ws.cell(row=r, column=c)
                cell.fill = fill_notif
                cell.border = border_box

        # 2. Employee Table Headers
        row_h1 = 4
        row_h2 = 5
        ws.row_dimensions[row_h1].height = 24
        ws.row_dimensions[row_h2].height = 24

        font_hdr = Font(name="Arial", size=10, bold=True, color="000000")
        font_white = Font(name="Arial", size=10, bold=True, color="FFFFFF")

        fill_green = PatternFill(start_color=cls.COLOR_FT_GREEN, fill_type="solid")
        fill_nt = PatternFill(start_color=cls.COLOR_ICMS_NT, fill_type="solid")
        fill_thc = PatternFill(start_color=cls.COLOR_ICMS_THC, fill_type="solid")
        fill_tc = PatternFill(start_color=cls.COLOR_ICMS_TC, fill_type="solid")
        fill_bh = PatternFill(start_color=cls.COLOR_BAO_HONG, fill_type="solid")
        fill_red = PatternFill(start_color=cls.COLOR_TH_RED, fill_type="solid")

        def set_hdr(r, c, val, fill, font=font_hdr):
            cell = ws.cell(row=r, column=c, value=val)
            cell.fill = fill
            cell.font = font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border_box
            return cell

        # Header 1
        ws.merge_cells("A4:A5"); set_hdr(4, 1, "FT", fill_green)
        ws.merge_cells("B4:B5"); set_hdr(4, 2, "Tên FT", fill_green)
        ws.merge_cells("C4:C5"); set_hdr(4, 3, "TTH", fill_green)
        ws.merge_cells("D4:D5"); set_hdr(4, 4, "Vị trí", fill_green)

        ws.merge_cells("E4:G4"); set_hdr(4, 5, "ICMS_Bảo dưỡng nhà trạm", fill_nt)
        for c in range(5, 8): ws.cell(row=4, column=c).border = border_box

        ws.merge_cells("H4:J4"); set_hdr(4, 8, "ICMS_Bảo dưỡng THC", fill_thc)
        for c in range(8, 11): ws.cell(row=4, column=c).border = border_box

        ws.merge_cells("K4:M4"); set_hdr(4, 11, "ICMS_Tuần tra tuyến cáp", fill_tc)
        for c in range(11, 14): ws.cell(row=4, column=c).border = border_box

        ws.merge_cells("N4:P4"); set_hdr(4, 14, "Báo hỏng hạ tầng mạng lưới", fill_bh, font_white)
        for c in range(14, 17): ws.cell(row=4, column=c).border = border_box

        ws.merge_cells("Q4:S4"); set_hdr(4, 17, "Tổng", fill_green)
        for c in range(17, 20): ws.cell(row=4, column=c).border = border_box

        ws.merge_cells("T4:T5"); set_hdr(4, 20, "Thực hiện ngày", fill_red, font_white)

        # Header 2
        for start_c in [5, 8, 11, 14, 17]:
            fl = fill_bh if start_c == 14 else (fill_nt if start_c == 5 else (fill_thc if start_c == 8 else (fill_tc if start_c == 11 else fill_green)))
            fnt = font_white if start_c == 14 else font_hdr
            set_hdr(5, start_c, "Tồn", fl, fnt)
            set_hdr(5, start_c + 1, "Quá hạn", fl, fnt)
            set_hdr(5, start_c + 2, "Quá hạn 30N", fl, fnt)

        # Employee Data Rows
        curr_row = 6
        font_data = Font(name="Arial", size=10)
        font_data_bold = Font(name="Arial", size=10, bold=True)
        fill_tagged = PatternFill(start_color="FFF1F2", fill_type="solid")

        for emp in center.employees:
            ws.row_dimensions[curr_row].height = 20
            row_fill = fill_tagged if emp.is_tagged else None

            def write_d(col, val, is_num=True, bold=False, color=None):
                c = ws.cell(row=curr_row, column=col)
                if is_num:
                    c.value = val if val > 0 else ""
                    c.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    c.value = val
                    c.alignment = Alignment(horizontal="left", vertical="center")
                c.font = Font(name="Arial", size=10, bold=bold, color=color or "000000")
                if row_fill:
                    c.fill = row_fill
                c.border = border_box

            write_d(1, emp.username, False)
            write_d(2, emp.full_name, False)
            write_d(3, emp.center_code, False)
            write_d(4, emp.position, False)

            write_d(5, emp.icms_bd_nt_ton)
            write_d(6, emp.icms_bd_nt_qh)
            write_d(7, emp.icms_bd_nt_qh30)

            write_d(8, emp.icms_bd_thc_ton)
            write_d(9, emp.icms_bd_thc_qh)
            write_d(10, emp.icms_bd_thc_qh30)

            write_d(11, emp.icms_tt_tc_ton)
            write_d(12, emp.icms_tt_tc_qh)
            write_d(13, emp.icms_tt_tc_qh30)

            write_d(14, emp.bao_hong_ton)
            write_d(15, emp.bao_hong_qh)
            write_d(16, emp.bao_hong_qh30)

            write_d(17, emp.ton, True, bold=True)
            write_d(18, emp.qua_han, True, bold=True)
            write_d(19, emp.qua_han_30, True)

            th_color = "DC2626" if emp.thuc_hien_ngay == 0 and emp.ton > 0 else "000000"
            write_d(20, emp.thuc_hien_ngay, True, bold=True, color=th_color)
            curr_row += 1

        # Subtotal Row
        ws.row_dimensions[curr_row].height = 22
        fill_sub = PatternFill(start_color=cls.COLOR_SUBTOTAL_YELLOW, fill_type="solid")
        ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=4)
        c_sub = ws.cell(row=curr_row, column=1, value="Tổng cộng")
        c_sub.font = font_data_bold
        c_sub.alignment = Alignment(horizontal="left", vertical="center")

        sub = center.get_subtotal()
        sub_vals = [
            sub["icms_bd_nt_ton"], sub["icms_bd_nt_qh"], sub["icms_bd_nt_qh30"],
            sub["icms_bd_thc_ton"], sub["icms_bd_thc_qh"], sub["icms_bd_thc_qh30"],
            sub["icms_tt_tc_ton"], sub["icms_tt_tc_qh"], sub["icms_tt_tc_qh30"],
            sub["bao_hong_ton"], sub["bao_hong_qh"], sub["bao_hong_qh30"],
            sub["ton"], sub["qua_han"], sub["qua_han_30"], sub["thuc_hien_ngay"]
        ]

        for i, val in enumerate(sub_vals, 5):
            c = ws.cell(row=curr_row, column=i, value=val if val > 0 else "")
            c.font = font_data_bold
            c.alignment = Alignment(horizontal="right", vertical="center")

        for c in range(1, 21):
            cell = ws.cell(row=curr_row, column=c)
            cell.fill = fill_sub
            cell.border = border_box

        curr_row += 2

        # 3. Overdue WO Table (Navy Blue)
        if center.work_orders:
            curr_row = cls._render_wo_subtable(
                ws, curr_row, center.work_orders,
                title="DANH SÁCH CHI TIẾT WO QUÁ HẠN (CẦN XỬ LÝ GẤP)",
                header_fill_color=cls.COLOR_WO_NAVY,
                day_color="DC2626",
                subtotal_label="Tổng cộng WO quá hạn"
            )
            curr_row += 2

        # 4. Pending WO Table (Forest Green)
        if center.pending_work_orders:
            curr_row = cls._render_wo_subtable(
                ws, curr_row, center.pending_work_orders,
                title="DANH SÁCH CHI TIẾT WO TỒN CHƯA QUÁ HẠN (THEO DÕI TIẾN ĐỘ)",
                header_fill_color=cls.COLOR_PENDING_GREEN,
                day_color="166534",
                subtotal_label="Tổng cộng WO tồn chưa quá hạn"
            )

        # Page Setup
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        if fit_to_page:
            ws.sheet_properties.pageSetUpPr.fitToPage = True
            ws.page_setup.fitToWidth = 1
            ws.page_setup.fitToHeight = 0

        # Adjust column widths
        col_w = {
            "A": 14, "B": 22, "C": 8, "D": 14,
            "E": 8, "F": 8, "G": 8, "H": 8, "I": 8, "J": 8,
            "K": 8, "L": 8, "M": 8, "N": 8, "O": 8, "P": 8,
            "Q": 10, "R": 10, "S": 10, "T": 12
        }
        for cl, w in col_w.items():
            ws.column_dimensions[cl].width = w

    @classmethod
    def _render_wo_subtable(cls, ws, start_row: int, work_orders: list, title: str, header_fill_color: str, day_color: str, subtotal_label: str) -> int:
        thin_side = Side(border_style="thin", color="000000")
        border_box = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        fill_banner = PatternFill(start_color=header_fill_color, fill_type="solid")
        font_banner = Font(name="Arial", size=11, bold=True, color="FFFFFF")

        # Banner Title
        ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=15)
        b_cell = ws.cell(row=start_row, column=1, value=f"{title} — {len(work_orders)} WO")
        b_cell.font = font_banner
        b_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[start_row].height = 26
        for c in range(1, 16):
            ws.cell(row=start_row, column=c).fill = fill_banner
            ws.cell(row=start_row, column=c).border = border_box

        # Column Headers
        hdr_row = start_row + 1
        headers = ["STT", "Mã công việc", "Loại công việc", "Nội dung công việc", "Hạn kết thúc", "Trạng thái", "Nhân viên thực hiện", "Mã trạm", "FT comment", "FT mobile", "Ngày hoàn thành", "Ngày quá hạn", "TTH", "BKK", "Lý do BKK"]
        ws.row_dimensions[hdr_row].height = 24
        fill_sub_hdr = PatternFill(start_color="F1F5F9", fill_type="solid")
        font_hdr = Font(name="Arial", size=10, bold=True)

        for i, h in enumerate(headers, 1):
            c = ws.cell(row=hdr_row, column=i, value=h)
            c.font = font_hdr
            c.fill = fill_sub_hdr
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = border_box

        curr_r = hdr_row + 1
        font_data = Font(name="Arial", size=9)

        for idx, w in enumerate(work_orders, 1):
            ws.row_dimensions[curr_r].height = 19
            ws.cell(row=curr_r, column=1, value=idx).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_r, column=2, value=w.code).alignment = Alignment(horizontal="left")
            ws.cell(row=curr_r, column=3, value=w.job_type).alignment = Alignment(horizontal="left")
            ws.cell(row=curr_r, column=4, value=w.content).alignment = Alignment(horizontal="left")
            ws.cell(row=curr_r, column=5, value=w.deadline).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_r, column=6, value=w.status).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_r, column=7, value=w.performer).alignment = Alignment(horizontal="left")
            ws.cell(row=curr_r, column=8, value=w.station_code).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_r, column=9, value=w.ft_comment or "").alignment = Alignment(horizontal="left")
            ws.cell(row=curr_r, column=10, value=w.ft_mobile or "").alignment = Alignment(horizontal="center")
            ws.cell(row=curr_r, column=11, value=str(w.completed_date or "")).alignment = Alignment(horizontal="center")

            c_day = ws.cell(row=curr_r, column=12, value=w.overdue_days)
            c_day.alignment = Alignment(horizontal="center")
            c_day.font = Font(name="Arial", size=9, bold=True, color=day_color)

            ws.cell(row=curr_r, column=13, value=w.center_code).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_r, column=14, value=w.bkk or "").alignment = Alignment(horizontal="center")
            ws.cell(row=curr_r, column=15, value=w.bkk_reason or "").alignment = Alignment(horizontal="left")

            for col in range(1, 16):
                cell = ws.cell(row=curr_r, column=col)
                if col != 12:
                    cell.font = font_data
                cell.border = border_box
            curr_r += 1

        # Summary Row
        ws.row_dimensions[curr_r].height = 22
        ws.merge_cells(start_row=curr_r, start_column=1, end_row=curr_r, end_column=11)
        c_tot = ws.cell(row=curr_r, column=1, value=f"{subtotal_label}: {len(work_orders)} WO")
        c_tot.font = Font(name="Arial", size=10, bold=True)
        c_tot.alignment = Alignment(horizontal="left", vertical="center")

        fill_tot = PatternFill(start_color="FEF3C7", fill_type="solid")
        for col in range(1, 16):
            cell = ws.cell(row=curr_r, column=col)
            cell.fill = fill_tot
            cell.border = border_box

        return curr_r
