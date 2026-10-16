"""
Data models for THFT Report Tool.
Uses dataclasses for structured, clean, and type-safe data handling.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import re


@dataclass
class EmployeeFT:
    row_idx: int
    username: str
    full_name: str
    center_raw: str
    center_code: str
    center_name: str
    position: str

    # Detail ICMS & Báo hỏng columns
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

    # Key columns (Q, R, S, T)
    ton: int = 0             # Cột Q: Tổng Tồn
    qua_han: int = 0         # Cột R: Tổng Quá hạn
    qua_han_30: int = 0      # Cột S: Tổng Quá hạn 30N
    thuc_hien_ngay: int = 0  # Cột T: Thực hiện ngày

    # Business Tagging logic
    # Q > 0 AND thuc_hien_ngay <= 0
    should_tag: bool = False
    is_manually_tagged: Optional[bool] = None

    @property
    def is_tagged(self) -> bool:
        """Determines if this employee is currently tagged (manual override or auto)."""
        if self.is_manually_tagged is not None:
            return self.is_manually_tagged
        return self.should_tag

    def get_tag_token(self, format_type: str = "name") -> str:
        """
        Generates tag token for employee based on format.
        Supported formats:
        - 'name': @Đinh Xuân Hương
        - 'name_upper': @ĐINH XUÂN HƯƠNG
        - 'username': @huongdx3
        - 'ft_username': @FT huongdx3
        - 'user_pos_center': @huongdx3 NV DM DCU
        - 'custom_word': @FT <username> <pos> <center>
        """
        clean_name = self.full_name if self.full_name and self.full_name != "#N/A" else self.username
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
        else: # default 'name'
            return f"@{clean_name}"


@dataclass
class WorkOrder:
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


@dataclass
class CenterReport:
    center_code: str
    center_name: str
    center_raw: str
    employees: List[EmployeeFT] = field(default_factory=list)
    work_orders: List[WorkOrder] = field(default_factory=list)
    pending_work_orders: List[WorkOrder] = field(default_factory=list)

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

    def build_tag_string(self, format_type: str = "name", separator: str = " ") -> str:
        tags = [e.get_tag_token(format_type) for e in self.tagged_employees]
        return separator.join(tags)

    def get_subtotal(self) -> Dict[str, int]:
        """Calculates sum for all numerical columns for this center."""
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
        """Returns a new CenterReport filtered by employee position (e.g. 'NV DM', 'NV NHÀ TRẠM')."""
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
            employees=filtered,
            work_orders=self.work_orders,
            pending_work_orders=self.pending_work_orders
        )


@dataclass
class ReportDataset:
    file_path: str
    sheet_name: str
    report_date_str: str           # DD/MM/YYYY
    day_month_str: str             # DD/MM
    deadline_str: str              # DD/MM
    meeting_time_str: str          # HH:MM
    centers: Dict[str, CenterReport] = field(default_factory=dict)
    total_employees: int = 0
    total_tagged: int = 0

    @property
    def total_work_orders(self) -> int:
        return sum(len(c.work_orders) for c in self.centers.values())

    @property
    def total_pending_work_orders(self) -> int:
        return sum(len(c.pending_work_orders) for c in self.centers.values())

    def get_filtered_dataset(self, position_filter: str) -> "ReportDataset":
        """Returns a new ReportDataset filtered by employee position."""
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
            sheet_name=self.sheet_name,
            report_date_str=self.report_date_str,
            day_month_str=self.day_month_str,
            deadline_str=self.deadline_str,
            meeting_time_str=self.meeting_time_str,
            centers=filtered_centers,
            total_employees=tot_emps,
            total_tagged=tot_tagged
        )
