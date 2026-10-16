"""
Configuration manager for WO Operations Center.
Stores user settings, templates, and column mappings in Windows AppData directory.
Never writes directly to Program Files or system directories.
"""

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_app_data_dir() -> Path:
    """Returns the persistent Windows AppData path for WO Operations Center."""
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA")
        if app_data:
            base_dir = Path(app_data)
        else:
            base_dir = Path.home() / "AppData" / "Roaming"
    else:
        base_dir = Path.home() / ".config"

    target_dir = base_dir / "WOOperationsCenter"
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def get_database_path() -> Path:
    """Returns path to SQLite database."""
    return get_app_data_dir() / "wo_operations.db"


def get_config_file_path() -> Path:
    """Returns path to configuration JSON file."""
    return get_app_data_dir() / "config.json"


def get_logs_dir() -> Path:
    """Returns path to log directory."""
    logs_dir = get_app_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "1.0.0",
    "theme": "light",
    "recent_files": [],
    "default_output_dir": str(Path.home() / "Documents" / "WO_Reports"),
    "auto_open_export": True,
    "executive_report": {
        "recipient": "Kính gửi PGĐ @NAN PGĐ A THẮNG , TP @A Sơnpb1 TPKT NAN , TTH!",
        "notification": "Đóng Wo quá hạn trước {HAN_QUA_HAN}.\nĐóng hết wo tháng {THANG} xong trước {HAN_THANG}.",
        "deadline_qh": "30/09",
        "deadline_month": "05/10",
        "template": (
            "{NGUOI_NHAN}\n\n"
            "PVHKT kính gửi tiến độ cắt tồn wo tháng {THANG}\n"
            "theo PGNV của Đ/c PGĐCN đến ngày {NGAY}/{THANG}\n\n"
            "+Thực hiện ngày: {THUC_HIEN_NGAY} WO\n\n"
            "- Tổng tồn: {TONG_TON} Wo, trong đó:\n"
            "{TON_QUA_HAN} Wo tồn quá hạn,\n"
            "{TON_TREN_30_NGAY} Wo tồn >30 ngày{CHI_TIET_TREN_30_NGAY}\n\n"
            "- Tồn cao tại TT: {TOP_5_TRUNG_TAM}\n\n"
            "Kính đề nghị TTH tồn wo:\n\n"
            "{NOI_DUNG_THONG_BAO}\n\n"
            "@mọi người"
        )
    },
    "thft_report": {
        "tag_format": "name",  # name, name_upper, username, ft_username, user_pos_center
        "deadline": "05/10",
        "meeting_time": "06:30",
        "position_filter": "Tất cả",
        "template": (
            "FT tồn quá hạn wo đến ngày hôm nay {NGAY_THANG}, "
            "khẩn trương hoàn thành trước {HAN_HOAN_THANH}. "
            "FT không có tiến độ ngày sẽ triệu tập họp vào {GIO_HOP} ngày mai {DANH_SACH_TAG}"
        )
    },
    "column_mapping": {
        "th_tth": {
            "sheet_name": "TH TTH",
            "summary_row": 3,
            "data_start_row": 4,
            "columns": {
                "center_name": 1,   # Col A
                "tong_ton": 17,      # Col Q
                "ton_qua_han": 18,   # Col R
                "ton_30_ngay": 19,   # Col S
                "thuc_hien_ngay": 20,# Col T
                "kh_ngay": 21,       # Col U
                "danh_gia": 22,      # Col V
                "hop_ngay": 23,      # Col W
                "ty_le_ht_ngay": 24  # Col X
            }
        },
        "thft": {
            "sheet_name": "THFT",
            "data_start_row": 4,
            "columns": {
                "username": "A",
                "full_name": "B",
                "center": "C",
                "position": "D",
                "icms_bd_nt_ton": "E",
                "icms_bd_nt_qh": "F",
                "icms_bd_nt_qh30": "G",
                "icms_bd_thc_ton": "H",
                "icms_bd_thc_qh": "I",
                "icms_bd_thc_qh30": "J",
                "icms_tt_tc_ton": "K",
                "icms_tt_tc_qh": "L",
                "icms_tt_tc_qh30": "M",
                "bao_hong_ton": "N",
                "bao_hong_qh": "O",
                "bao_hong_qh30": "P",
                "ton": "Q",
                "qua_han": "R",
                "qua_han_30": "S",
                "thuc_hien_ngay": "T"
            }
        },
        "wo": {
            "sheet_name": "WO",
            "header_row": 1,
            "data_start_row": 2
        }
    },
    "center_aliases": {
        "VPU": "Vinh Phú",
        "KLN": "Kim Liên",
        "NLC": "Nam Lộc",
        "DCU": "Diễn Châu",
        "YTH": "Yên Thành",
        "QLU": "Quỳnh Lưu",
        "THU": "Thanh Chương",
        "QHP": "Quỳ Hợp",
        "QPG": "Quế Phong",
        "TKY": "Tân Kỳ",
        "DDG": "Đô Lương",
        "VTG": "Vũ Quang / Vị Thủy",
        "TDG": "Tương Dương",
        "MXN": "Mường Xén / Kỳ Sơn"
    }
}


class ConfigManager:
    """Manages application settings with automatic persistence to AppData."""

    def __init__(self):
        self.config_path = get_config_file_path()
        self.data: Dict[str, Any] = self.load()

    def load(self) -> Dict[str, Any]:
        """Loads config from file, creating with defaults if absent."""
        if not self.config_path.exists():
            self.save(DEFAULT_CONFIG)
            return dict(DEFAULT_CONFIG)

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Merge missing keys from default config
            merged = self._merge_defaults(dict(DEFAULT_CONFIG), loaded)
            return merged
        except Exception as e:
            logger.error(f"Error reading config from {self.config_path}: {e}")
            return dict(DEFAULT_CONFIG)

    def save(self, data: Optional[Dict[str, Any]] = None) -> bool:
        """Persists config to AppData JSON file."""
        if data is not None:
            self.data = data
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.config_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            temp_path.replace(self.config_path)
            return True
        except Exception as e:
            logger.error(f"Error writing config to {self.config_path}: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        self.data[key] = value
        return self.save()

    def add_recent_file(self, file_path: str):
        """Adds a file path to the beginning of the recent files list."""
        recent: List[str] = self.data.get("recent_files", [])
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        self.data["recent_files"] = recent[:10]  # Keep max 10
        self.save()

    def _merge_defaults(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                base[k] = self._merge_defaults(base[k], v)
            else:
                base[k] = v
        return base
