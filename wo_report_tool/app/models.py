"""
Data models for WO Report Tool.
Defines structured classes for centers, reports, and settings.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class CenterData:
    """Represents WO status and metrics for a single district/center."""
    stt: int
    code: str  # Short 3-letter code, e.g. 'VPU', 'KLN', 'QLU'
    name: str  # e.g. 'Trung tâm Vinh Phú'
    full_name: str  # e.g. 'Trung tâm Vinh Phú (VCC_NAN_001_VPU)'
    tong_ton: int = 0
    ton_qua_han: int = 0
    ton_30_ngay: int = 0
    thuc_hien_ngay: int = 0
    kh_ngay: int = 0
    ty_le_ht_ngay: float = 0.0
    danh_gia: str = ""
    hop_ngay: str = ""


@dataclass
class ReportData:
    """Aggregated report data extracted from Excel."""
    report_date: date
    day: int
    month: int
    year: int

    # Summary metrics (Row 3 in TH TTH sheet)
    thuc_hien_ngay: int = 0
    tong_ton: int = 0
    ton_qua_han: int = 0
    ton_tren_30_ngay: int = 0

    # Calculated metrics
    top_centers: List[str] = field(default_factory=list)  # Top 5 center codes sorted by tong_ton descending
    overdue_30_centers: List[tuple] = field(default_factory=list)  # [(code, count)] for centers with >30 days backlog

    # Template text
    recipient: str = ""
    notification: str = ""
    deadline_qh: str = ""
    deadline_month: str = ""

    # Full details
    centers: List[CenterData] = field(default_factory=list)
    source_file_path: str = ""
    source_sheet_name: str = ""


@dataclass
class ReportSettings:
    """User-configurable settings persisted in config.json."""
    recipient: str = "Kính gửi PGĐ @NAN PGĐ A THẮNG , TP @A Sơnpb1 TPKT NAN , TTH!"
    notification: str = "Đóng Wo quá hạn trước 30/9.\nĐóng hết wo tháng 9 xong trước 05/10."
    deadline_qh: str = "30/09"
    deadline_month: str = "05/10"
    last_output_directory: str = ""
    window_width: int = 1100
    window_height: int = 750
