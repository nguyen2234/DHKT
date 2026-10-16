"""
Configuration management for WO Report Tool.
Handles config.json loading/saving and Excel mapping configurations.
"""

import json
import logging
import os
import sys
from typing import Any, Dict

from app.models import ReportSettings

logger = logging.getLogger(__name__)

# Standard Excel column indices (1-based index)
DEFAULT_REPORT_MAPPING: Dict[str, Any] = {
    "sheet_name": "TH TTH",
    "summary_row": 3,
    "data_start_row": 4,
    "columns": {
        "center_name": 1,      # Col A: Tên trung tâm huyện (TTH)
        "tong_ton": 17,        # Col Q: Tổng tồn Điều hành UT1
        "ton_qua_han": 18,     # Col R: Tồn quá hạn
        "ton_30_ngay": 19,     # Col S: Tồn quá hạn >30 ngày
        "thuc_hien_ngay": 20,  # Col T: Thực hiện ngày (TH Ngày)
        "kh_ngay": 21,         # Col U: Kế hoạch ngày (KH Ngày)
        "danh_gia": 22,        # Col V: Đánh giá
        "hop_ngay": 23,        # Col W: Họp Ngày
        "ty_le_ht_ngay": 24,   # Col X: Tỷ lệ HT Ngày
        "deadline_date": 25,   # Col Y: kết thúc ngày
        "days_left": 26,       # Col Z: số ngày còn lại
        "today_day": 27        # Col AA: Hôm nay
    }
}


def get_base_directory() -> str:
    """
    Returns the application root directory.
    Works for both development environment and PyInstaller packaged executable.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled binary
        return os.path.dirname(sys.executable)
    else:
        # Running in regular python script
        # Return path to wo_report_tool directory
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_config_file_path() -> str:
    """Returns absolute path to config.json file."""
    base_dir = get_base_directory()
    config_dir = os.path.join(base_dir, "config")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")


def load_config() -> ReportSettings:
    """Loads configuration settings from config.json or returns default settings."""
    config_path = get_config_file_path()
    settings = ReportSettings()

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                settings.recipient = data.get("recipient", settings.recipient)
                settings.notification = data.get("notification", settings.notification)
                settings.deadline_qh = data.get("deadline_qh", settings.deadline_qh)
                settings.deadline_month = data.get("deadline_month", settings.deadline_month)
                settings.last_output_directory = data.get("last_output_directory", settings.last_output_directory)
                settings.window_width = data.get("window_width", settings.window_width)
                settings.window_height = data.get("window_height", settings.window_height)
                logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Error loading configuration from {config_path}: {e}. Using defaults.")

    return settings


def save_config(settings: ReportSettings) -> bool:
    """Persists configuration settings to config.json."""
    config_path = get_config_file_path()
    try:
        data = {
            "recipient": settings.recipient,
            "notification": settings.notification,
            "deadline_qh": settings.deadline_qh,
            "deadline_month": settings.deadline_month,
            "last_output_directory": settings.last_output_directory,
            "window_width": settings.window_width,
            "window_height": settings.window_height,
            "excel_mapping": DEFAULT_REPORT_MAPPING
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Saved configuration to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration to {config_path}: {e}")
        return False
