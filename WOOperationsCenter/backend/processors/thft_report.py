"""
THFT Report Processor.
Manages employee tagging, center-level notifications, and position filtering
matching the exact business rules from THFTReportTool.
"""

from typing import Any, Dict, List, Optional
from backend.domain.models import CenterReport, EmployeeFT, ReportDataset


class THFTReportProcessor:
    """Business logic for FT employee reports, TAG formatting, and position filtering."""

    @classmethod
    def generate_center_notification(
        cls,
        center: CenterReport,
        template: str,
        report_date_str: str,
        day_month_str: str,
        deadline_str: str,
        meeting_time_str: str,
        tag_format: str = "name"
    ) -> str:
        """
        Renders the center notification template with strict isolation:
        Only tags employees belonging to this specific center.
        """
        tag_string = center.build_tag_string(format_type=tag_format, separator=" ")

        msg = template
        msg = msg.replace("{NGAY_BAO_CAO}", report_date_str)
        msg = msg.replace("{NGAY_THANG}", day_month_str)
        msg = msg.replace("{HAN_HOAN_THANH}", deadline_str)
        msg = msg.replace("{GIO_HOP}", meeting_time_str)
        msg = msg.replace("{DANH_SACH_TAG}", tag_string)
        msg = msg.replace("{TEN_HUYEN}", center.center_name)
        msg = msg.replace("{MA_HUYEN}", center.center_code)

        return msg

    @classmethod
    def set_employee_tag_override(
        cls,
        dataset: ReportDataset,
        center_code: str,
        username: str,
        is_tagged: bool
    ) -> bool:
        """Sets a manual override for an employee's tag state."""
        center = dataset.centers.get(center_code)
        if not center:
            return False

        for emp in center.employees:
            if emp.username == username:
                emp.is_manually_tagged = is_tagged
                # Recalculate dataset total tagged
                dataset.total_tagged = sum(c.tagged_count for c in dataset.centers.values())
                return True
        return False
