"""
Executive WO Report Processor.
Generates province-level executive report text and formatted summaries
according to the verified TAMMI notification standard.
"""

from typing import Any, Dict, List, Optional, Tuple
from backend.domain.models import ProvinceSummary, ReportDataset


class ExecutiveReportProcessor:
    """Handles text generation, template resolution, and discrepancy checking for Module A."""

    @staticmethod
    def format_overdue_30_details(overdue_centers: List[Tuple[str, int]]) -> str:
        """
        Formats centers with backlog > 30 days into '(CODE:COUNT, ...)' string.
        Example: [('MXN', 1)] -> ' (MXN:1)'
        """
        valid_items = [f"{code}:{count}" for code, count in overdue_centers if count > 0]
        if not valid_items:
            return ""
        return f" ({', '.join(valid_items)})"

    @staticmethod
    def format_top_centers(top_centers: List[str]) -> str:
        """Formats list of top backlog center codes. Example: 'QLU, DDG, VPU, KLN, YTH'."""
        if not top_centers:
            return ""
        return ", ".join(top_centers)

    @classmethod
    def generate_report_text(
        cls,
        summary: ProvinceSummary,
        recipient: str = "",
        notification: str = "",
        deadline_qh: str = "30/09",
        deadline_month: str = "05/10",
        template: Optional[str] = None
    ) -> str:
        """
        Constructs the complete executive report message matching the exact Word specification.
        """
        recip = recipient.strip() or "Kính gửi PGĐ @NAN PGĐ A THẮNG , TP @A Sơnpb1 TPKT NAN , TTH!"
        thang = summary.month
        ngay = summary.day
        nam = summary.year
        thuc_hien_ngay = summary.thuc_hien_ngay
        tong_ton = summary.tong_ton
        ton_qua_han = summary.ton_qua_han
        ton_tren_30_ngay = summary.ton_tren_30_ngay

        detail_30_str = cls.format_overdue_30_details(summary.overdue_30_centers)
        top_centers_str = cls.format_top_centers(summary.top_centers)

        notif = notification.strip()
        if not notif:
            notif = (
                f"Đóng Wo quá hạn trước {deadline_qh}.\n"
                f"Đóng hết wo tháng {thang} xong trước {deadline_month}."
            )

        if template:
            # Deterministic template substitution
            text = template
            text = text.replace("{NGUOI_NHAN}", recip)
            text = text.replace("{THANG}", str(thang))
            text = text.replace("{NGAY}", str(ngay))
            text = text.replace("{NAM}", str(nam))
            text = text.replace("{THUC_HIEN_NGAY}", str(thuc_hien_ngay))
            text = text.replace("{TONG_TON}", str(tong_ton))
            text = text.replace("{TON_QUA_HAN}", str(ton_qua_han))
            text = text.replace("{TON_TREN_30_NGAY}", str(ton_tren_30_ngay))
            text = text.replace("{CHI_TIET_TREN_30_NGAY}", detail_30_str)
            text = text.replace("{TOP_5_TRUNG_TAM}", top_centers_str)
            text = text.replace("{NOI_DUNG_THONG_BAO}", notif)
            return text

        report_lines = [
            recip,
            "",
            f"PVHKT kính gửi tiến độ cắt tồn wo tháng {thang}",
            f"theo PGNV của Đ/c PGĐCN đến ngày {ngay}/{thang}",
            "",
            f"+Thực hiện ngày: {thuc_hien_ngay} WO",
            "",
            f"- Tổng tồn: {tong_ton} Wo, trong đó:",
            f"{ton_qua_han} Wo tồn quá hạn,",
            f"{ton_tren_30_ngay} Wo tồn >30 ngày{detail_30_str}",
            "",
            f"- Tồn cao tại TT: {top_centers_str}",
            "",
            "Kính đề nghị TTH tồn wo:",
            "",
            notif,
            "",
            "@mọi người"
        ]

        return "\n".join(report_lines)
