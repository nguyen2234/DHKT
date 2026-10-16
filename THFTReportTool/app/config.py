"""
Configuration manager for THFT Report Tool.
Handles loading and saving settings from config.json.
Supports execution in both script mode and PyInstaller frozen executable mode.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "app_name": "CÔNG CỤ TẠO BÁO CÁO THFT",
    "version": "1.0.0",
    "sheet_name": "THFT",
    "header_row": 1,
    "sub_header_row": 2,
    "subtotal_row": 3,
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
    },
    "notification": {
        "deadline": "05/10",
        "meeting_time": "06:30",
        "template": "FT tồn quá hạn wo đến ngày hôm nay {NGAY_THANG}, khẩn trương hoàn thành trước {HAN_HOAN_THANH}. FT không có tiến độ ngày sẽ triệu tập họp vào {GIO_HOP} ngày mai\n\n{DANH_SACH_TAG}",
        "tag_format": "name",
        "tag_separator": " "
    },
    "export": {
        "font_family": "Times New Roman",
        "header_font_size": 10,
        "data_font_size": 10,
        "title_font_size": 11,
        "page_orientation": "landscape",
        "paper_size": "A4",
        "fit_to_width": 1,
        "fit_to_height": 0
    }
}


def get_base_dir() -> str:
    """Returns the base application directory whether running from script or PyInstaller."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_config_path() -> str:
    """Returns absolute path to config.json."""
    base_dir = get_base_dir()
    config_dir = os.path.join(base_dir, "config")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")


def load_config() -> Dict[str, Any]:
    """Loads configuration from config.json or returns default if not found."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # merge with defaults to ensure all keys exist
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            return DEFAULT_CONFIG.copy()
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """Saves configuration dictionary to config.json."""
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving config to {config_path}: {e}")
        return False
