"""
Windows Clipboard Engine for WO Operations Center.
Supports standard Windows CF_HTML (with exact byte offset headers),
Plain Unicode Text, and TSV formats for seamless 1-click pasting into
TAMMI, Microsoft Teams, Word, and Excel.
"""

import ctypes
import logging
import sys
from typing import Optional

from backend.domain.models import CenterReport, ProvinceSummary, WorkOrder
from backend.processors.executive_report import ExecutiveReportProcessor

logger = logging.getLogger(__name__)


def format_windows_cf_html(html_fragment: str) -> str:
    """
    Wraps an HTML fragment in the Windows CF_HTML format with exact byte offsets.
    Standard requirement for Windows Clipboard HTML transfer.
    """
    prefix = (
        "Version:0.9\r\n"
        "StartHTML:<<<<<<<<1\r\n"
        "EndHTML:<<<<<<<<2\r\n"
        "StartFragment:<<<<<<<<3\r\n"
        "EndFragment:<<<<<<<<4\r\n"
        "<html>\r\n"
        "<head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"></head>\r\n"
        "<body>\r\n"
        "<!--StartFragment-->\r\n"
    )
    suffix = (
        "\r\n<!--EndFragment-->\r\n"
        "</body>\r\n"
        "</html>"
    )

    dummy_header = prefix.replace("<<<<<<<<1", "0000000000") \
                         .replace("<<<<<<<<2", "0000000000") \
                         .replace("<<<<<<<<3", "0000000000") \
                         .replace("<<<<<<<<4", "0000000000")

    header_bytes = dummy_header.encode("utf-8")
    start_html = len(header_bytes) - len("<html>\r\n<head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"></head>\r\n<body>\r\n<!--StartFragment-->\r\n".encode("utf-8"))
    start_fragment = len(header_bytes)

    fragment_bytes = html_fragment.encode("utf-8")
    end_fragment = start_fragment + len(fragment_bytes)
    end_html = end_fragment + len(suffix.encode("utf-8"))

    header = (
        f"Version:0.9\r\n"
        f"StartHTML:{start_html:010d}\r\n"
        f"EndHTML:{end_html:010d}\r\n"
        f"StartFragment:{start_fragment:010d}\r\n"
        f"EndFragment:{end_fragment:010d}\r\n"
        f"<html>\r\n"
        f"<head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"></head>\r\n"
        f"<body>\r\n"
        f"<!--StartFragment-->\r\n"
    )

    return header + html_fragment + suffix


class ClipboardEngine:
    """Provides complete clipboard generation and system copy capabilities."""

    @classmethod
    def set_system_clipboard(cls, text_content: str, html_content: Optional[str] = None) -> bool:
        """Sets both plain text and rich HTML formats to the system clipboard."""
        try:
            # Try PySide6 QGuiApplication clipboard first if running Qt app
            from PySide6.QtGui import QGuiApplication, QClipboard
            from PySide6.QtCore import QMimeData

            app = QGuiApplication.instance()
            if app:
                clipboard = QGuiApplication.clipboard()
                mime = QMimeData()
                mime.setText(text_content)
                if html_content:
                    mime.setHtml(html_content)
                clipboard.setMimeData(mime)
                return True
        except Exception as e:
            logger.debug(f"PySide6 clipboard not available, trying Win32 API: {e}")

        # Fallback to direct Win32 API on Windows
        if sys.platform == "win32":
            return cls._set_win32_clipboard(text_content, html_content)

        return False

    @classmethod
    def set_image_clipboard(cls, image_bytes: bytes) -> bool:
        """Sets raw image bytes (PNG, BMP, JPG) directly onto the system clipboard."""
        try:
            from PySide6.QtGui import QGuiApplication, QImage, QClipboard
            app = QGuiApplication.instance()
            if app:
                image = QImage()
                if image.loadFromData(image_bytes, "PNG") or image.loadFromData(image_bytes):
                    clipboard = QGuiApplication.clipboard()
                    clipboard.setImage(image)
                    return True
        except Exception as e:
            logger.error(f"PySide6 set_image_clipboard error: {e}")

        # Win32 DIB injection fallback
        if sys.platform == "win32":
            try:
                import io
                from PIL import Image
                img = Image.open(io.BytesIO(image_bytes))
                output = io.BytesIO()
                img.convert("RGB").save(output, "BMP")
                data = output.getvalue()[14:]  # Exclude 14-byte BMP header to get pure DIB
                output.close()

                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32

                kernel32.GlobalAlloc.restype = ctypes.c_void_p
                kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
                kernel32.GlobalLock.restype = ctypes.c_void_p
                kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
                kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
                user32.SetClipboardData.restype = ctypes.c_void_p
                user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
                user32.OpenClipboard.argtypes = [ctypes.c_void_p]

                CF_DIB = 8
                GMEM_MOVEABLE = 0x0002

                if user32.OpenClipboard(None):
                    user32.EmptyClipboard()
                    h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
                    p_mem = kernel32.GlobalLock(h_mem)
                    ctypes.memmove(p_mem, data, len(data))
                    kernel32.GlobalUnlock(h_mem)
                    user32.SetClipboardData(CF_DIB, h_mem)
                    user32.CloseClipboard()
                    return True
            except Exception as e:
                logger.error(f"Win32 image clipboard error: {e}")

        return False

    @classmethod
    def set_image_from_base64(cls, base64_str: str) -> bool:
        """Decodes a base64 encoded PNG data URI or raw string and copies image to clipboard."""
        import base64
        try:
            if "," in base64_str:
                base64_str = base64_str.split(",", 1)[1]
            raw_bytes = base64.b64decode(base64_str)
            return cls.set_image_clipboard(raw_bytes)
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return False

    @staticmethod
    def _set_win32_clipboard(text: str, html: Optional[str]) -> bool:
        """Low-level Windows clipboard injection via ctypes."""
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            kernel32.GlobalAlloc.restype = ctypes.c_void_p
            kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            user32.SetClipboardData.restype = ctypes.c_void_p
            user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
            user32.OpenClipboard.argtypes = [ctypes.c_void_p]
            user32.RegisterClipboardFormatW.argtypes = [ctypes.c_wchar_p]
            user32.RegisterClipboardFormatW.restype = ctypes.c_uint

            GMEM_MOVEABLE = 0x0002
            CF_UNICODETEXT = 13
            CF_HTML = user32.RegisterClipboardFormatW("HTML Format")

            if not user32.OpenClipboard(None):
                return False

            user32.EmptyClipboard()

            # 1. Set Unicode text
            text_bytes = (text + "\0").encode("utf-16le")
            h_text = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes))
            p_text = kernel32.GlobalLock(h_text)
            ctypes.memmove(p_text, text_bytes, len(text_bytes))
            kernel32.GlobalUnlock(h_text)
            user32.SetClipboardData(CF_UNICODETEXT, h_text)

            # 2. Set HTML format if provided
            if html:
                cf_html_str = format_windows_cf_html(html)
                html_bytes = cf_html_str.encode("utf-8") + b"\0"
                h_html = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(html_bytes))
                p_html = kernel32.GlobalLock(h_html)
                ctypes.memmove(p_html, html_bytes, len(html_bytes))
                kernel32.GlobalUnlock(h_html)
                user32.SetClipboardData(CF_HTML, h_html)

            user32.CloseClipboard()
            return True
        except Exception as e:
            logger.error(f"Win32 clipboard error: {e}")
            return False

    # ==========================================
    # REPORT BUILDERS
    # ==========================================

    @classmethod
    def build_center_html_table(cls, center: CenterReport, notification: str = "") -> str:
        """
        Builds the complete styled HTML table matching the Word/TAMMI template.
        Uses exact business colors:
        - A-D: #92D050
        - E-G: #EBF1DE
        - H-J: #FDE9D9
        - K-M: #92CDDC
        - N-P: #0070C0 (white text)
        - Q-S: #92D050
        - T: #FF0000 (white text)
        """
        html = []
        html.append("<div style='font-family: Arial, sans-serif; font-size: 13px;'>")

        if notification:
            html.append(f"<div style='margin-bottom: 15px; font-weight: bold; line-height: 1.5; color: #1e293b;'>{notification.replace(chr(10), '<br>')}</div>")

        html.append("<table border='1' cellspacing='0' cellpadding='4' style='border-collapse: collapse; text-align: center; border: 1px solid #000; width: 100%; font-size: 11px;'>")

        # Header Row 1
        html.append("<tr style='font-weight: bold;'>")
        html.append("<th rowspan='2' style='background-color: #92D050; border: 1px solid #000;'>FT</th>")
        html.append("<th rowspan='2' style='background-color: #92D050; border: 1px solid #000;'>Tên FT</th>")
        html.append("<th rowspan='2' style='background-color: #92D050; border: 1px solid #000;'>TTH</th>")
        html.append("<th rowspan='2' style='background-color: #92D050; border: 1px solid #000;'>Vị trí</th>")
        html.append("<th colspan='3' style='background-color: #EBF1DE; border: 1px solid #000;'>ICMS_Bảo dưỡng nhà trạm</th>")
        html.append("<th colspan='3' style='background-color: #FDE9D9; border: 1px solid #000;'>ICMS_Bảo dưỡng THC</th>")
        html.append("<th colspan='3' style='background-color: #92CDDC; border: 1px solid #000;'>ICMS_Tuần tra tuyến cáp</th>")
        html.append("<th colspan='3' style='background-color: #0070C0; color: #fff; border: 1px solid #000;'>Báo hỏng hạ tầng mạng lưới</th>")
        html.append("<th colspan='3' style='background-color: #92D050; border: 1px solid #000;'>Tổng</th>")
        html.append("<th rowspan='2' style='background-color: #FF0000; color: #fff; border: 1px solid #000;'>Thực hiện ngày</th>")
        html.append("</tr>")

        # Header Row 2
        html.append("<tr style='font-weight: bold;'>")
        for _ in range(4):
            html.append("<th style='border: 1px solid #000;'>Tồn</th>")
            html.append("<th style='border: 1px solid #000;'>Quá hạn</th>")
            html.append("<th style='border: 1px solid #000;'>Quá hạn 30N</th>")
        html.append("<th style='border: 1px solid #000;'>Tồn</th>")
        html.append("<th style='border: 1px solid #000;'>Quá hạn</th>")
        html.append("<th style='border: 1px solid #000;'>Quá hạn 30N</th>")
        html.append("</tr>")

        # Data Rows
        def render_num(val: int) -> str:
            return str(val) if val > 0 else ""

        for emp in center.employees:
            bg_emp = "#fff"
            if emp.is_tagged:
                bg_emp = "#fff5f5"

            html.append(f"<tr style='background-color: {bg_emp};'>")
            html.append(f"<td style='border: 1px solid #000; text-align: left;'>{emp.username}</td>")
            html.append(f"<td style='border: 1px solid #000; text-align: left;'>{emp.full_name}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{emp.center_code}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{emp.position}</td>")

            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.icms_bd_nt_ton)}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.icms_bd_nt_qh)}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.icms_bd_nt_qh30)}</td>")

            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.icms_bd_thc_ton)}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.icms_bd_thc_qh)}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.icms_bd_thc_qh30)}</td>")

            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.icms_tt_tc_ton)}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.icms_tt_tc_qh)}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.icms_tt_tc_qh30)}</td>")

            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.bao_hong_ton)}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.bao_hong_qh)}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.bao_hong_qh30)}</td>")

            bold_q = f"<b>{emp.ton}</b>" if emp.ton > 0 else ""
            bold_r = f"<b>{emp.qua_han}</b>" if emp.qua_han > 0 else ""
            html.append(f"<td style='border: 1px solid #000;'>{bold_q}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{bold_r}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{render_num(emp.qua_han_30)}</td>")

            th_color = "#dc2626" if emp.thuc_hien_ngay == 0 and emp.ton > 0 else "#000"
            html.append(f"<td style='border: 1px solid #000; color: {th_color}; font-weight: bold;'>{render_num(emp.thuc_hien_ngay)}</td>")
            html.append("</tr>")

        # Subtotal Row
        sub = center.get_subtotal()
        html.append("<tr style='background-color: #FEF3C7; font-weight: bold;'>")
        html.append("<td colspan='4' style='border: 1px solid #000; text-align: left;'>Tổng cộng</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['icms_bd_nt_ton'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['icms_bd_nt_qh'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['icms_bd_nt_qh30'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['icms_bd_thc_ton'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['icms_bd_thc_qh'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['icms_bd_thc_qh30'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['icms_tt_tc_ton'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['icms_tt_tc_qh'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['icms_tt_tc_qh30'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['bao_hong_ton'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['bao_hong_qh'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['bao_hong_qh30'])}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{sub['ton']}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{sub['qua_han']}</td>")
        html.append(f"<td style='border: 1px solid #000;'>{render_num(sub['qua_han_30'])}</td>")
        html.append(f"<td style='border: 1px solid #000; color: #dc2626;'>{sub['thuc_hien_ngay']}</td>")
        html.append("</tr>")

        html.append("</table>")
        html.append("</div>")

        return "".join(html)

    @classmethod
    def build_center_text_report(cls, center: CenterReport, notification: str = "") -> str:
        """Builds plain text / TSV formatted report for the center."""
        lines = []
        if notification:
            lines.append(notification)
            lines.append("")

        headers = ["FT", "Tên FT", "TTH", "Vị trí", "Tổng Tồn", "Quá hạn", "QH 30N", "TH Ngày"]
        lines.append("\t".join(headers))

        for e in center.employees:
            row = [
                e.username,
                e.full_name,
                e.center_code,
                e.position,
                str(e.ton),
                str(e.qua_han),
                str(e.qua_han_30),
                str(e.thuc_hien_ngay)
            ]
            lines.append("\t".join(row))

        sub = center.get_subtotal()
        sub_row = ["Tổng cộng", "", center.center_code, "", str(sub['ton']), str(sub['qua_han']), str(sub['qua_han_30']), str(sub['thuc_hien_ngay'])]
        lines.append("\t".join(sub_row))

        return "\n".join(lines)

    @classmethod
    def build_work_orders_html(cls, work_orders: list, title: str, theme_color: str = "#1F4E78") -> str:
        """Builds styled HTML table for Work Orders (Overdue Navy Blue or Pending Forest Green)."""
        html = []
        html.append("<div style='font-family: Arial, sans-serif; font-size: 12px;'>")
        html.append(f"<h3 style='color: {theme_color}; margin-bottom: 8px;'>{title} ({len(work_orders)} WO)</h3>")
        html.append("<table border='1' cellspacing='0' cellpadding='4' style='border-collapse: collapse; border: 1px solid #000; width: 100%; font-size: 11px;'>")

        headers = ["STT", "Mã công việc", "Loại công việc", "Nội dung", "Hạn kết thúc", "Trạng thái", "Nhân viên", "Mã trạm", "Ngày quá hạn"]
        html.append(f"<tr style='background-color: {theme_color}; color: #fff; font-weight: bold; text-align: center;'>")
        for h in headers:
            html.append(f"<th style='border: 1px solid #000;'>{h}</th>")
        html.append("</tr>")

        for idx, w in enumerate(work_orders, 1):
            bg = "#fff" if idx % 2 != 0 else "#f8fafc"
            html.append(f"<tr style='background-color: {bg};'>")
            html.append(f"<td style='border: 1px solid #000; text-align: center;'>{idx}</td>")
            html.append(f"<td style='border: 1px solid #000; font-family: monospace;'>{w.code}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{w.job_type}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{w.content}</td>")
            html.append(f"<td style='border: 1px solid #000; text-align: center;'>{w.deadline}</td>")
            html.append(f"<td style='border: 1px solid #000; text-align: center;'>{w.status}</td>")
            html.append(f"<td style='border: 1px solid #000;'>{w.performer}</td>")
            html.append(f"<td style='border: 1px solid #000; text-align: center;'>{w.station_code}</td>")
            html.append(f"<td style='border: 1px solid #000; text-align: center; font-weight: bold; color: {theme_color};'>{w.overdue_days}</td>")
            html.append("</tr>")

        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def build_work_orders_tsv(cls, work_orders: list, title: str) -> str:
        """Builds TSV formatted text for direct Excel pasting."""
        lines = [f"{title} ({len(work_orders)} WO)"]
        headers = ["STT", "Mã công việc", "Loại công việc", "Nội dung", "Hạn kết thúc", "Trạng thái", "Nhân viên", "Mã trạm", "Ngày quá hạn", "TTH"]
        lines.append("\t".join(headers))
        for idx, w in enumerate(work_orders, 1):
            row = [
                str(idx),
                str(w.code),
                str(w.job_type),
                str(w.content),
                str(w.deadline),
                str(w.status),
                str(w.performer),
                str(w.station_code),
                str(w.overdue_days),
                str(w.center_code)
            ]
            lines.append("\t".join(row))
        return "\n".join(lines)
