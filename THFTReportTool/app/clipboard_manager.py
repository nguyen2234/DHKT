"""
Clipboard Manager module for THFT Report Tool.
Builds dual-format clipboard content (HTML Table + Formatted Plain Text)
optimized for pasting into TAMMY, Microsoft Word, Excel, Teams, or web portals.
"""

import html
from typing import Dict, Any, List
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QMimeData

from .models import CenterReport, EmployeeFT


class ClipboardManager:
    @staticmethod
    def copy_full_report(center: CenterReport, notification_text: str) -> bool:
        """
        Copies complete center report to clipboard:
        1. Notification text
        2. Tagged employees list
        3. Formatted data table
        Provides both HTML format and Plain Text format.
        """
        html_content = ClipboardManager._build_html_report(center, notification_text)
        text_content = ClipboardManager._build_text_report(center, notification_text)

        mime = QMimeData()
        mime.setHtml(html_content)
        mime.setText(text_content)

        clipboard = QGuiApplication.clipboard()
        clipboard.setMimeData(mime)
        return True

    @staticmethod
    def copy_notification_only(notification_text: str) -> bool:
        """Copies only the notification header and tagged employees list."""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(notification_text.strip())
        return True

    @staticmethod
    def copy_work_orders(center: CenterReport) -> bool:
        """
        Copies overdue Work Orders for this center to clipboard in dual format:
        1. HTML Table (styled for TAMMY / Word / Teams / Excel)
        2. TSV / Tab-Separated Text (for plain text paste or direct Excel paste)
        """
        if not center or not center.work_orders:
            return False

        html_content = ClipboardManager._build_html_work_orders(center)
        text_content = ClipboardManager._build_text_work_orders(center)

        mime = QMimeData()
        mime.setHtml(html_content)
        mime.setText(text_content)

        clipboard = QGuiApplication.clipboard()
        clipboard.setMimeData(mime)
        return True

    @staticmethod
    def copy_pending_work_orders(center: CenterReport) -> bool:
        """
        Copies pending Work Orders (not overdue, column L > 0) for this center to clipboard.
        """
        if not center or not center.pending_work_orders:
            return False

        html_content = ClipboardManager._build_html_pending_work_orders(center)
        text_content = ClipboardManager._build_text_pending_work_orders(center)

        mime = QMimeData()
        mime.setHtml(html_content)
        mime.setText(text_content)

        clipboard = QGuiApplication.clipboard()
        clipboard.setMimeData(mime)
        return True

    @staticmethod
    def _build_html_report(center: CenterReport, notification_text: str) -> str:
        """Generates clean HTML table with Word template styling for TAMMY / rich text."""
        # Convert newlines to <br/> and escape HTML
        safe_notice = html.escape(notification_text).replace("\n", "<br/>")

        # Table rows HTML
        data_rows_html = []
        for emp in center.employees:
            is_tag = emp.is_tagged
            q_style = "font-weight:bold; color:#C00000;" if is_tag else "font-weight:bold;"
            tr_bg = "#FFF5F5" if is_tag else "#FFFFFF"

            val_cells = [
                f"<td style='padding:5px 8px; font-weight:bold; text-align:left; border:1px solid #D9D9D9;'>{html.escape(emp.username)}</td>",
                f"<td style='padding:5px 8px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(emp.full_name)}</td>",
                f"<td style='padding:5px 8px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(emp.center_raw)}</td>",
                f"<td style='padding:5px 8px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(emp.position)}</td>",

                # ICMS Nhà trạm
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.icms_bd_nt_ton or ''}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.icms_bd_nt_qh or ''}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.icms_bd_nt_qh30 or ''}</td>",

                # ICMS THC
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.icms_bd_thc_ton or ''}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.icms_bd_thc_qh or ''}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.icms_bd_thc_qh30 or ''}</td>",

                # ICMS Tuyến cáp
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.icms_tt_tc_ton or ''}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.icms_tt_tc_qh or ''}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.icms_tt_tc_qh30 or ''}</td>",

                # Báo hỏng
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.bao_hong_ton or ''}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.bao_hong_qh or ''}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.bao_hong_qh30 or ''}</td>",

                # Tổng & TH ngày
                f"<td style='padding:5px 6px; text-align:center; {q_style} border:1px solid #D9D9D9;'>{emp.ton or ''}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.qua_han or ''}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{emp.qua_han_30 or ''}</td>",
                f"<td style='padding:5px 6px; text-align:center; font-weight:bold; border:1px solid #D9D9D9;'>{emp.thuc_hien_ngay or ''}</td>",
            ]
            data_rows_html.append(f"<tr style='background-color:{tr_bg};'>{''.join(val_cells)}</tr>")

        # Subtotal row
        sub = center.get_subtotal()
        total_row_html = f"""
        <tr style='background-color:#E2EFDA; font-weight:bold;'>
            <td colspan='4' style='padding:6px 8px; text-align:right; border:1px solid #A6A6A6;'>Tổng cộng ({center.total_count} FT - {center.tagged_count} Tag):</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['icms_bd_nt_ton'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['icms_bd_nt_qh'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['icms_bd_nt_qh30'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['icms_bd_thc_ton'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['icms_bd_thc_qh'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['icms_bd_thc_qh30'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['icms_tt_tc_ton'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['icms_tt_tc_qh'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['icms_tt_tc_qh30'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['bao_hong_ton'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['bao_hong_qh'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['bao_hong_qh30'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6; color:#C00000;'>{sub['ton'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['qua_han'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['qua_han_30'] or ''}</td>
            <td style='padding:6px; text-align:center; border:1px solid #A6A6A6;'>{sub['thuc_hien_ngay'] or ''}</td>
        </tr>
        """

        full_html = f"""
        <div style="font-family:'Times New Roman', Arial, sans-serif; font-size:13px; color:#1A1A1A; line-height:1.5;">
            <div style="background-color:#FFF9E6; border:1px solid #F0C36D; border-radius:4px; padding:12px 16px; margin-bottom:14px; font-weight:bold; color:#1F4E78;">
                {safe_notice}
            </div>

            <table style="border-collapse:collapse; width:100%; font-size:12px; border:1px solid #B0B0B0;">
                <thead>
                    <tr style="font-weight:bold; text-align:center;">
                        <th rowspan="2" style="background-color:#92D050; padding:6px; border:1px solid #A6A6A6;">FT</th>
                        <th rowspan="2" style="background-color:#92D050; padding:6px; border:1px solid #A6A6A6;">Tên FT</th>
                        <th rowspan="2" style="background-color:#92D050; padding:6px; border:1px solid #A6A6A6;">TTH</th>
                        <th rowspan="2" style="background-color:#92D050; padding:6px; border:1px solid #A6A6A6;">Vị trí</th>
                        <th colspan="3" style="background-color:#EBF1DE; padding:6px; border:1px solid #A6A6A6;">ICMS_Bảo dưỡng nhà trạm</th>
                        <th colspan="3" style="background-color:#FDE9D9; padding:6px; border:1px solid #A6A6A6;">ICMS_Bảo dưỡng THC</th>
                        <th colspan="3" style="background-color:#92CDDC; padding:6px; border:1px solid #A6A6A6;">ICMS_Tuần tra tuyến cáp</th>
                        <th colspan="3" style="background-color:#0070C0; color:#FFFFFF; padding:6px; border:1px solid #A6A6A6;">Báo hỏng hạ tầng mạng lưới</th>
                        <th colspan="3" style="background-color:#92D050; padding:6px; border:1px solid #A6A6A6;">Tổng</th>
                        <th rowspan="2" style="background-color:#FF0000; color:#FFFFFF; padding:6px; border:1px solid #A6A6A6;">Thực hiện ngày</th>
                    </tr>
                    <tr style="font-weight:bold; text-align:center; font-size:11px;">
                        <th style="background-color:#EBF1DE; padding:4px; border:1px solid #A6A6A6;">Tồn</th>
                        <th style="background-color:#EBF1DE; padding:4px; border:1px solid #A6A6A6;">Quá hạn</th>
                        <th style="background-color:#EBF1DE; padding:4px; border:1px solid #A6A6A6;">Quá hạn 30N</th>
                        <th style="background-color:#FDE9D9; padding:4px; border:1px solid #A6A6A6;">Tồn</th>
                        <th style="background-color:#FDE9D9; padding:4px; border:1px solid #A6A6A6;">Quá hạn</th>
                        <th style="background-color:#FDE9D9; padding:4px; border:1px solid #A6A6A6;">Quá hạn 30N</th>
                        <th style="background-color:#92CDDC; padding:4px; border:1px solid #A6A6A6;">Tồn</th>
                        <th style="background-color:#92CDDC; padding:4px; border:1px solid #A6A6A6;">Quá hạn</th>
                        <th style="background-color:#92CDDC; padding:4px; border:1px solid #A6A6A6;">Quá hạn 30N</th>
                        <th style="background-color:#0070C0; color:#FFFFFF; padding:4px; border:1px solid #A6A6A6;">Tồn</th>
                        <th style="background-color:#0070C0; color:#FFFFFF; padding:4px; border:1px solid #A6A6A6;">Quá hạn</th>
                        <th style="background-color:#0070C0; color:#FFFFFF; padding:4px; border:1px solid #A6A6A6;">Quá hạn 30N</th>
                        <th style="background-color:#92D050; padding:4px; border:1px solid #A6A6A6;">Tồn</th>
                        <th style="background-color:#92D050; padding:4px; border:1px solid #A6A6A6;">Quá hạn</th>
                        <th style="background-color:#92D050; padding:4px; border:1px solid #A6A6A6;">Quá hạn 30N</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(data_rows_html)}
                    {total_row_html}
                </tbody>
            </table>
        </div>
        """
        return full_html.strip()

    @staticmethod
    def _build_text_report(center: CenterReport, notification_text: str) -> str:
        """Generates clean tab-delimited plain text for pasting into chat or spreadsheet."""
        lines = [notification_text.strip(), ""]

        # Tab-separated table header
        h1 = [
            "FT", "Tên FT", "TTH", "Vị trí",
            "ICMS_BD_NT(Tồn)", "ICMS_BD_NT(QH)", "ICMS_BD_NT(QH30)",
            "ICMS_BD_THC(Tồn)", "ICMS_BD_THC(QH)", "ICMS_BD_THC(QH30)",
            "ICMS_TT_TC(Tồn)", "ICMS_TT_TC(QH)", "ICMS_TT_TC(QH30)",
            "Báo_Hỏng(Tồn)", "Báo_Hỏng(QH)", "Báo_Hỏng(QH30)",
            "Tổng_Tồn", "Tổng_QH", "Tổng_QH30", "Thực_Hiện_Ngày"
        ]
        lines.append("\t".join(h1))

        for emp in center.employees:
            row = [
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
            lines.append("\t".join(row))

        sub = center.get_subtotal()
        tot_row = [
            f"Tổng cộng ({center.total_count} FT - {center.tagged_count} Tag)", "", "", "",
            str(sub["icms_bd_nt_ton"] or ""),
            str(sub["icms_bd_nt_qh"] or ""),
            str(sub["icms_bd_nt_qh30"] or ""),
            str(sub["icms_bd_thc_ton"] or ""),
            str(sub["icms_bd_thc_qh"] or ""),
            str(sub["icms_bd_thc_qh30"] or ""),
            str(sub["icms_tt_tc_ton"] or ""),
            str(sub["icms_tt_tc_qh"] or ""),
            str(sub["icms_tt_tc_qh30"] or ""),
            str(sub["bao_hong_ton"] or ""),
            str(sub["bao_hong_qh"] or ""),
            str(sub["bao_hong_qh30"] or ""),
            str(sub["ton"] or ""),
            str(sub["qua_han"] or ""),
            str(sub["qua_han_30"] or ""),
            str(sub["thuc_hien_ngay"] or "")
        ]
        lines.append("\t".join(tot_row))

        return "\n".join(lines)

    @staticmethod
    def _build_html_work_orders(center: CenterReport) -> str:
        headers = [
            "STT", "Mã công việc", "Loại công việc", "Nội dung công việc",
            "Thời điểm kết thúc", "Trạng thái", "Nhân viên thực hiện",
            "Mã trạm", "FT comment", "FT mobile", "Ngày hoàn thành",
            "Ngày quá hạn", "TTH", "BKK", "Lý do BKK"
        ]
        th_cells = "".join(
            f"<th style='padding:6px 8px; background-color:#1F4E78; color:#FFFFFF; border:1px solid #D9D9D9; font-weight:bold; font-size:11px;'>{h}</th>"
            for h in headers
        )

        rows_html = []
        for idx, wo in enumerate(center.work_orders, 1):
            bg = "#F9FAFB" if idx % 2 == 0 else "#FFFFFF"
            overdue_val = round(wo.overdue_days, 1) if isinstance(wo.overdue_days, float) else (wo.overdue_days or "")
            cells = [
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{idx}</td>",
                f"<td style='padding:5px 8px; font-weight:bold; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.code)}</td>",
                f"<td style='padding:5px 8px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.job_type)}</td>",
                f"<td style='padding:5px 8px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.content)}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(wo.deadline)}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(wo.status)}</td>",
                f"<td style='padding:5px 6px; font-weight:bold; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.performer)}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(wo.station_code)}</td>",
                f"<td style='padding:5px 6px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.ft_comment or '')}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(wo.ft_mobile or '')}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(str(wo.completed_date or ''))}</td>",
                f"<td style='padding:5px 6px; font-weight:bold; color:#C00000; text-align:center; border:1px solid #D9D9D9;'>{overdue_val}</td>",
                f"<td style='padding:5px 6px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.center_raw)}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(wo.bkk or '')}</td>",
                f"<td style='padding:5px 6px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.bkk_reason or '')}</td>",
            ]
            rows_html.append(f"<tr style='background-color:{bg};'>{''.join(cells)}</tr>")

        summary_row = f"""
        <tr style='background-color:#FFF2CC; font-weight:bold;'>
            <td colspan='11' style='padding:6px 8px; text-align:right; border:1px solid #D9D9D9;'>Tổng cộng WO quá hạn ({center.center_name}):</td>
            <td style='padding:6px; text-align:center; color:#C00000; font-weight:bold; border:1px solid #D9D9D9;'>{len(center.work_orders)}</td>
            <td colspan='3' style='padding:6px; border:1px solid #D9D9D9;'></td>
        </tr>
        """

        return f"""
        <div style="font-family:'Times New Roman', Arial, sans-serif; font-size:12px; color:#000000;">
            <p style="font-size:13px; font-weight:bold; color:#1F4E78; margin-bottom:8px;">
                DANH SÁCH CHI TIẾT WO QUÁ HẠN - {html.escape(center.center_name.upper())} ({len(center.work_orders)} WO)
            </p>
            <table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse; border:1px solid #D9D9D9; width:100%; font-size:11px;">
                <thead>
                    <tr>{th_cells}</tr>
                </thead>
                <tbody>
                    {''.join(rows_html)}
                    {summary_row}
                </tbody>
            </table>
        </div>
        """

    @staticmethod
    def _build_text_work_orders(center: CenterReport) -> str:
        lines = []
        lines.append(f"DANH SÁCH CHI TIẾT WO QUÁ HẠN - {center.center_name.upper()} ({len(center.work_orders)} WO)\n")
        headers = [
            "STT", "Mã công việc", "Loại công việc", "Nội dung công việc",
            "Thời điểm kết thúc", "Trạng thái", "Nhân viên thực hiện",
            "Mã trạm", "FT comment", "FT mobile", "Ngày hoàn thành",
            "Ngày quá hạn", "TTH", "BKK", "Lý do BKK"
        ]
        lines.append("\t".join(headers))

        for idx, wo in enumerate(center.work_orders, 1):
            overdue_val = str(round(wo.overdue_days, 1)) if isinstance(wo.overdue_days, float) else str(wo.overdue_days or "")
            vals = [
                str(idx),
                wo.code,
                wo.job_type,
                wo.content.replace("\n", " ").replace("\r", ""),
                wo.deadline,
                wo.status,
                wo.performer,
                wo.station_code,
                (wo.ft_comment or "").replace("\n", " "),
                wo.ft_mobile or "",
                str(wo.completed_date or ""),
                overdue_val,
                wo.center_raw,
                wo.bkk or "",
                wo.bkk_reason or ""
            ]
            lines.append("\t".join(vals))

        lines.append(f"\nTổng số WO quá hạn: {len(center.work_orders)} WO")
        return "\n".join(lines)

    @staticmethod
    def _build_html_pending_work_orders(center: CenterReport) -> str:
        headers = [
            "STT", "Mã công việc", "Loại công việc", "Nội dung công việc",
            "Thời điểm kết thúc", "Trạng thái", "Nhân viên thực hiện",
            "Mã trạm", "FT comment", "FT mobile", "Ngày hoàn thành",
            "Ngày quá hạn", "TTH", "BKK", "Lý do BKK"
        ]
        th_cells = "".join(
            f"<th style='padding:6px 8px; background-color:#135E48; color:#FFFFFF; border:1px solid #D9D9D9; font-weight:bold; font-size:11px;'>{h}</th>"
            for h in headers
        )

        rows_html = []
        for idx, wo in enumerate(center.pending_work_orders, 1):
            bg = "#F4FBF7" if idx % 2 == 0 else "#FFFFFF"
            overdue_val = round(wo.overdue_days, 1) if isinstance(wo.overdue_days, float) else (wo.overdue_days or "")
            cells = [
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{idx}</td>",
                f"<td style='padding:5px 8px; font-weight:bold; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.code)}</td>",
                f"<td style='padding:5px 8px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.job_type)}</td>",
                f"<td style='padding:5px 8px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.content)}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(wo.deadline)}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(wo.status)}</td>",
                f"<td style='padding:5px 6px; font-weight:bold; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.performer)}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(wo.station_code)}</td>",
                f"<td style='padding:5px 6px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.ft_comment or '')}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(wo.ft_mobile or '')}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(str(wo.completed_date or ''))}</td>",
                f"<td style='padding:5px 6px; font-weight:bold; color:#135E48; text-align:center; border:1px solid #D9D9D9;'>{overdue_val}</td>",
                f"<td style='padding:5px 6px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.center_raw)}</td>",
                f"<td style='padding:5px 6px; text-align:center; border:1px solid #D9D9D9;'>{html.escape(wo.bkk or '')}</td>",
                f"<td style='padding:5px 6px; text-align:left; border:1px solid #D9D9D9;'>{html.escape(wo.bkk_reason or '')}</td>",
            ]
            rows_html.append(f"<tr style='background-color:{bg};'>{''.join(cells)}</tr>")

        summary_row = f"""
        <tr style='background-color:#D5F5E3; font-weight:bold;'>
            <td colspan='11' style='padding:6px 8px; text-align:right; border:1px solid #D9D9D9;'>Tổng cộng WO tồn chưa quá hạn ({center.center_name}):</td>
            <td style='padding:6px; text-align:center; color:#135E48; font-weight:bold; border:1px solid #D9D9D9;'>{len(center.pending_work_orders)}</td>
            <td colspan='3' style='padding:6px; border:1px solid #D9D9D9;'></td>
        </tr>
        """

        return f"""
        <div style="font-family:'Times New Roman', Arial, sans-serif; font-size:12px; color:#000000;">
            <p style="font-size:13px; font-weight:bold; color:#135E48; margin-bottom:8px;">
                DANH SÁCH CHI TIẾT WO TỒN CHƯA QUÁ HẠN - {html.escape(center.center_name.upper())} ({len(center.pending_work_orders)} WO)
            </p>
            <table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse; border:1px solid #D9D9D9; width:100%; font-size:11px;">
                <thead>
                    <tr>{th_cells}</tr>
                </thead>
                <tbody>
                    {''.join(rows_html)}
                    {summary_row}
                </tbody>
            </table>
        </div>
        """

    @staticmethod
    def _build_text_pending_work_orders(center: CenterReport) -> str:
        lines = []
        lines.append(f"DANH SÁCH CHI TIẾT WO TỒN CHƯA QUÁ HẠN - {center.center_name.upper()} ({len(center.pending_work_orders)} WO)\n")
        headers = [
            "STT", "Mã công việc", "Loại công việc", "Nội dung công việc",
            "Thời điểm kết thúc", "Trạng thái", "Nhân viên thực hiện",
            "Mã trạm", "FT comment", "FT mobile", "Ngày hoàn thành",
            "Ngày quá hạn", "TTH", "BKK", "Lý do BKK"
        ]
        lines.append("\t".join(headers))

        for idx, wo in enumerate(center.pending_work_orders, 1):
            overdue_val = str(round(wo.overdue_days, 1)) if isinstance(wo.overdue_days, float) else str(wo.overdue_days or "")
            vals = [
                str(idx),
                wo.code,
                wo.job_type,
                wo.content.replace("\n", " ").replace("\r", ""),
                wo.deadline,
                wo.status,
                wo.performer,
                wo.station_code,
                (wo.ft_comment or "").replace("\n", " "),
                wo.ft_mobile or "",
                str(wo.completed_date or ""),
                overdue_val,
                wo.center_raw,
                wo.bkk or "",
                wo.bkk_reason or ""
            ]
            lines.append("\t".join(vals))

        lines.append(f"\nTổng số WO tồn chưa quá hạn: {len(center.pending_work_orders)} WO")
        return "\n".join(lines)
