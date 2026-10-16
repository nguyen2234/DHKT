"""
Report Processor module for THFT Report Tool.
Manages notification formatting, tag rendering, and business rules application.
"""

from typing import Dict, Any, List, Optional
from .models import EmployeeFT, CenterReport, ReportDataset


class ReportProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def generate_center_notification(
        self,
        center: CenterReport,
        template: str,
        report_date_str: str,
        day_month_str: str,
        deadline_str: str,
        meeting_time_str: str,
        tag_format: str = "name"
    ) -> str:
        """
        Generates final notification text for a specific center.
        Replaces variables:
        - {NGAY_THANG} -> e.g. '28/9'
        - {NGAY} -> e.g. '28'
        - {THANG} -> e.g. '9'
        - {NGAY_BAO_CAO} -> e.g. '28/09/2026'
        - {HAN_HOAN_THANH} -> e.g. '05/10'
        - {GIO_HOP} -> e.g. '06:30'
        - {DANH_SACH_TAG} -> e.g. '@Đinh Xuân Hương @Hoàng Thành Long ...'
        """
        # Parse day & month from day_month_str
        parts = day_month_str.split("/")
        day = parts[0] if len(parts) > 0 else ""
        month = parts[1] if len(parts) > 1 else ""

        # Build tag list for THIS CENTER ONLY
        tag_str = center.build_tag_string(format_type=tag_format)

        text = template
        text = text.replace("{NGAY_THANG}", day_month_str)
        text = text.replace("{NGAY}/{THANG}", day_month_str)
        text = text.replace("{NGAY}", day)
        text = text.replace("{THANG}", month)
        text = text.replace("{NGAY_BAO_CAO}", report_date_str)
        text = text.replace("{HAN_HOAN_THANH}", deadline_str)
        text = text.replace("{GIO_HOP}", meeting_time_str)
        text = text.replace("{DANH_SACH_TAG}", tag_str)

        return text.strip()

    def set_employee_manual_tag(self, employee: EmployeeFT, tagged: bool):
        """Allows manual tag toggle from UI."""
        employee.is_manually_tagged = tagged

    def reset_all_tags(self, dataset: ReportDataset):
        """Resets manual overrides to default Q > 0 and T <= 0 logic."""
        for center in dataset.centers.values():
            for emp in center.employees:
                emp.is_manually_tagged = None
