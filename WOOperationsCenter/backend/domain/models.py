"""
Domain models for WO Operations Center.
Clean, structured dataclasses representing the normalized operational data
across Executive WO reports, FT Employee reports, and Work Order explorer.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CenterSummary:
    """Executive metrics for a single district center from 'TH TTH'."""
    stt: int
    code: str  # Short 3-letter code, e.g. 'QLU', 'VPU', 'DCU'
    name: str  # e.g. 'Quỳnh Lưu'
    full_name: str  # e.g. 'Trung tâm Quỳnh Lưu (VCC_NAN_007_QLU)'
    tong_ton: int = 0
    ton_qua_han: int = 0
    ton_30_ngay: int = 0
    thuc_hien_ngay: int = 0
    kh_ngay: int = 0
    ty_le_ht_ngay: float = 0.0
    danh_gia: str = ""
    hop_ngay: str = ""


@dataclass
class EmployeeFT:
    """FT technical employee record from 'THFT'."""
    row_idx: int
    username: str
    full_name: str
    center_raw: str
    center_code: str
    center_name: str
    position: str

    # Detail ICMS & Báo hỏng breakdown metrics
    icms_bd_nt_ton: int = 0
    icms_bd_nt_qh: int = 0
    icms_bd_nt_qh30: int = 0

    icms_bd_thc_ton: int = 0
    icms_bd_thc_qh: int = 0
    icms_bd_thc_qh30: int = 0

    icms_tt_tc_ton: int = 0
    icms_tt_tc_qh: int = 0
    icms_tt_tc_qh30: int = 0

    bao_hong_ton: int = 0
    bao_hong_qh: int = 0
    bao_hong_qh30: int = 0

    # Key aggregated columns
    ton: int = 0             # Cột Q: Tổng Tồn
    qua_han: int = 0         # Cột R: Tổng Quá hạn
    qua_han_30: int = 0      # Cột S: Tổng Quá hạn 30N
    thuc_hien_ngay: int = 0  # Cột T: Thực hiện ngày

    # Business Tagging logic: ton > 0 AND thuc_hien_ngay <= 0
    should_tag: bool = False
    is_manually_tagged: Optional[bool] = None

    @property
    def is_tagged(self) -> bool:
        """Evaluates whether employee is currently tagged (manual override takes precedence)."""
        if self.is_manually_tagged is not None:
            return self.is_manually_tagged
        return self.should_tag

    def get_tag_token(self, format_type: str = "name") -> str:
        """Formats the tag mention for clipboard and notifications."""
        clean_name = self.full_name.strip() if self.full_name and self.full_name != "#N/A" else self.username
        clean_user = self.username.strip() if self.username else ""

        if format_type == "name_upper":
            return f"@{clean_name.upper()}"
        elif format_type == "username":
            return f"@{clean_user}"
        elif format_type == "ft_username":
            return f"@FT {clean_user}"
        elif format_type == "user_pos_center":
            pos_clean = self.position.replace(" ", "") if self.position else "FT"
            return f"@{clean_user} {pos_clean} {self.center_code}"
        else:  # default 'name'
            return f"@{clean_name}"


@dataclass
class WorkOrder:
    """Individual work order from 'WO' sheet."""
    stt: Any
    code: str                  # Cột B: Mã công việc
    job_type: str              # Cột C: Loại công việc
    content: str               # Cột D: Nội dung công việc
    deadline: str              # Cột E: Thời điểm yêu cầu kết thúc
    status: str                # Cột F: Trạng thái
    performer: str             # Cột G: Nhân viên thực hiện
    station_code: str          # Cột H: Mã trạm
    ft_comment: Optional[str]  # Cột I: FT comment
    ft_mobile: Optional[str]   # Cột J: FT mobile
    completed_date: Any        # Cột K: Ngày hoàn thành
    overdue_days: Any          # Cột L: Ngày quá hạn
    center_raw: str            # Cột M: TTH
    bkk: Optional[str]         # Cột N: BKK
    bkk_reason: Optional[str]  # Cột O: Lý do BKK
    center_code: str = ""      # Mã trung tâm huyện (VD: QLU)
    center_name: str = ""      # Tên trung tâm huyện (VD: Quỳnh Lưu)
    classification: str = ""   # 'overdue' (<0), 'pending' (>0), 'boundary' (==0 or blank)


@dataclass
class CenterReport:
    """Aggregated operational report for a single center."""
    center_code: str
    center_name: str
    center_raw: str
    summary: Optional[CenterSummary] = None
    employees: List[EmployeeFT] = field(default_factory=list)
    work_orders: List[WorkOrder] = field(default_factory=list)          # Overdue (< 0)
    pending_work_orders: List[WorkOrder] = field(default_factory=list)  # In progress / Pending (> 0)
    boundary_work_orders: List[WorkOrder] = field(default_factory=list) # Zero or blank

    @property
    def total_count(self) -> int:
        return len(self.employees)

    @property
    def tagged_employees(self) -> List[EmployeeFT]:
        return [e for e in self.employees if e.is_tagged]

    @property
    def tagged_count(self) -> int:
        return len(self.tagged_employees)

    @property
    def work_orders_count(self) -> int:
        return len(self.work_orders)

    @property
    def pending_work_orders_count(self) -> int:
        return len(self.pending_work_orders)

    @property
    def boundary_work_orders_count(self) -> int:
        return len(self.boundary_work_orders)

    def build_tag_string(self, format_type: str = "name", separator: str = " ") -> str:
        tags = [e.get_tag_token(format_type) for e in self.tagged_employees]
        return separator.join(tags)

    def get_subtotal(self) -> Dict[str, int]:
        """Calculates total metric sums across employees."""
        return {
            "icms_bd_nt_ton": sum(e.icms_bd_nt_ton for e in self.employees),
            "icms_bd_nt_qh": sum(e.icms_bd_nt_qh for e in self.employees),
            "icms_bd_nt_qh30": sum(e.icms_bd_nt_qh30 for e in self.employees),
            "icms_bd_thc_ton": sum(e.icms_bd_thc_ton for e in self.employees),
            "icms_bd_thc_qh": sum(e.icms_bd_thc_qh for e in self.employees),
            "icms_bd_thc_qh30": sum(e.icms_bd_thc_qh30 for e in self.employees),
            "icms_tt_tc_ton": sum(e.icms_tt_tc_ton for e in self.employees),
            "icms_tt_tc_qh": sum(e.icms_tt_tc_qh for e in self.employees),
            "icms_tt_tc_qh30": sum(e.icms_tt_tc_qh30 for e in self.employees),
            "bao_hong_ton": sum(e.bao_hong_ton for e in self.employees),
            "bao_hong_qh": sum(e.bao_hong_qh for e in self.employees),
            "bao_hong_qh30": sum(e.bao_hong_qh30 for e in self.employees),
            "ton": sum(e.ton for e in self.employees),
            "qua_han": sum(e.qua_han for e in self.employees),
            "qua_han_30": sum(e.qua_han_30 for e in self.employees),
            "thuc_hien_ngay": sum(e.thuc_hien_ngay for e in self.employees),
        }

    def filter_by_position(self, position_filter: str) -> "CenterReport":
        """Returns a cloned CenterReport with filtered employee list."""
        if not position_filter or position_filter.strip().upper() in ("ALL", "TẤT CẢ", "TAT CA"):
            return self

        target = position_filter.strip().upper()
        filtered = []
        for emp in self.employees:
            pos = (emp.position or "").strip().upper()
            if target == pos or target in pos:
                filtered.append(emp)
            elif target in ("NV DM", "DM", "NHÂN VIÊN DM") and ("DM" in pos or "DÂY MÁY" in pos):
                filtered.append(emp)
            elif target in ("NV NHÀ TRẠM", "NHÀ TRẠM", "NHA TRAM") and ("TRẠM" in pos or "TRAM" in pos):
                filtered.append(emp)

        return CenterReport(
            center_code=self.center_code,
            center_name=self.center_name,
            center_raw=self.center_raw,
            summary=self.summary,
            employees=filtered,
            work_orders=self.work_orders,
            pending_work_orders=self.pending_work_orders,
            boundary_work_orders=self.boundary_work_orders
        )


@dataclass
class ProvinceSummary:
    """Aggregated province-wide executive numbers."""
    report_date: date
    day: int
    month: int
    year: int
    thuc_hien_ngay: int = 0
    tong_ton: int = 0
    ton_qua_han: int = 0
    ton_tren_30_ngay: int = 0
    top_centers: List[str] = field(default_factory=list)
    overdue_30_centers: List[Tuple[str, int]] = field(default_factory=list)
    has_discrepancy: bool = False
    discrepancy_details: str = ""


@dataclass
class ReportDataset:
    """The unified master dataset loaded from the source workbook."""
    file_path: str
    file_fingerprint: str
    detected_sheets: List[str]
    report_date_str: str           # DD/MM/YYYY
    day_month_str: str             # DD/MM
    deadline_str: str              # DD/MM
    meeting_time_str: str          # HH:MM
    province_summary: ProvinceSummary
    centers: Dict[str, CenterReport] = field(default_factory=dict)
    total_employees: int = 0
    total_tagged: int = 0

    @property
    def total_work_orders(self) -> int:
        return sum(len(c.work_orders) for c in self.centers.values())

    @property
    def total_pending_work_orders(self) -> int:
        return sum(len(c.pending_work_orders) for c in self.centers.values())

    @property
    def total_boundary_work_orders(self) -> int:
        return sum(len(c.boundary_work_orders) for c in self.centers.values())

    def get_filtered_dataset(self, position_filter: str) -> "ReportDataset":
        """Generates a dataset view filtered by employee position."""
        if not position_filter or position_filter.strip().upper() in ("ALL", "TẤT CẢ", "TAT CA"):
            return self

        filtered_centers: Dict[str, CenterReport] = {}
        tot_emps = 0
        tot_tagged = 0
        for code, center in self.centers.items():
            fc = center.filter_by_position(position_filter)
            filtered_centers[code] = fc
            tot_emps += fc.total_count
            tot_tagged += fc.tagged_count

        return ReportDataset(
            file_path=self.file_path,
            file_fingerprint=self.file_fingerprint,
            detected_sheets=self.detected_sheets,
            report_date_str=self.report_date_str,
            day_month_str=self.day_month_str,
            deadline_str=self.deadline_str,
            meeting_time_str=self.meeting_time_str,
            province_summary=self.province_summary,
            centers=filtered_centers,
            total_employees=tot_emps,
            total_tagged=tot_tagged
        )


@dataclass
class ReportHistoryItem:
    """Metadata for a generated report record stored in SQLite."""
    id: Optional[int]
    timestamp: str
    report_type: str
    report_date: str
    source_file_path: str
    source_file_fingerprint: str
    applied_filters: str
    center_selection: str
    output_path: str
    message_snapshot: str
    status: str = "success"
