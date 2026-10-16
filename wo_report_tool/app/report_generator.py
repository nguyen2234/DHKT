"""
Report generator module for WO Report Tool.
Formats extracted metrics into the exact Word report template string ready for TAMMI clipboard copying.
"""

from typing import List, Tuple
from app.models import ReportData


class ReportGenerator:
    """Generates formatted report message matching the Word template."""

    @staticmethod
    def format_overdue_30_details(overdue_centers: List[Tuple[str, int]]) -> str:
        """
        Formats centers with backlog > 30 days into '(CODE:COUNT, ...)' string.
        Example:
            [('MXN', 2), ('TDG', 1)] -> '(MXN:2, TDG:1)'
            [('MXN', 1)] -> '(MXN:1)'
            [] -> ''
        """
        valid_items = [f"{code}:{count}" for code, count in overdue_centers if count > 0]
        if not valid_items:
            return ""
        return f" ({', '.join(valid_items)})"

    @staticmethod
    def format_top_centers(top_centers: List[str]) -> str:
        """
        Formats list of top backlog center codes.
        Example:
            ['QLU', 'DDG', 'VPU', 'KLN', 'YTH'] -> 'QLU, DDG, VPU, KLN, YTH'
        """
        if not top_centers:
            return ""
        return ", ".join(top_centers)

    @classmethod
    def generate_report_text(cls, data: ReportData) -> str:
        """
        Constructs the complete report text matching the exact specification:

        Kính gửi PGĐ @NAN PGĐ A THẮNG , TP @A Sơnpb1 TPKT NAN , TTH!

        PVHKT kính gửi tiến độ cắt tồn wo tháng {THANG}
        theo PGNV của Đ/c PGĐCN đến ngày {NGAY}/{THANG}

        +Thực hiện ngày: {THUC_HIEN_NGAY} WO

        - Tổng tồn: {TONG_TON} Wo, trong đó:
        {TON_QUA_HAN} Wo tồn quá hạn,
        {TON_TREN_30_NGAY} Wo tồn >30 ngày{CHI_TIET_TREN_30_NGAY}

        - Tồn cao tại TT: {TOP_5_TRUNG_TAM}

        Kính đề nghị TTH tồn wo:

        {NOI_DUNG_THONG_BAO}

        @mọi người
        """
        recipient = data.recipient.strip() or "Kính gửi PGĐ @NAN PGĐ A THẮNG , TP @A Sơnpb1 TPKT NAN , TTH!"
        thang = data.month
        ngay = data.day
        thuc_hien_ngay = data.thuc_hien_ngay
        tong_ton = data.tong_ton
        ton_qua_han = data.ton_qua_han
        ton_tren_30_ngay = data.ton_tren_30_ngay

        detail_30_str = cls.format_overdue_30_details(data.overdue_30_centers)
        top_centers_str = cls.format_top_centers(data.top_centers)

        notification = data.notification.strip()
        if not notification:
            deadline_qh = data.deadline_qh or "30/09"
            deadline_month = data.deadline_month or "05/10"
            notification = (
                f"Đóng Wo quá hạn trước {deadline_qh}.\n"
                f"Đóng hết wo tháng {thang} xong trước {deadline_month}."
            )

        report_lines = [
            recipient,
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
            notification,
            "",
            "@mọi người"
        ]

        return "\n".join(report_lines)
