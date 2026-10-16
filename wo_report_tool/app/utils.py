"""
Utility helper functions for WO Report Tool.
Provides text parsing, date formatting, clipboard helpers, and logging setup.
"""

import logging
import os
import re
import sys
from datetime import date, datetime
from typing import Optional, Tuple


def setup_logging(log_filename: str = "wo_report_tool.log") -> None:
    """Configures application-wide logging to console and local file."""
    # Ensure stdout is utf-8 on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers = [logging.StreamHandler(sys.stdout)]

    try:
        from app.config import get_base_directory
        log_dir = os.path.join(get_base_directory(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, log_filename)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        handlers.append(file_handler)
    except Exception:
        pass

    logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers, force=True)


def extract_center_code(full_name: str) -> str:
    """
    Extracts the short 3-letter district code from the center string.
    Example:
        'Trung tâm Vinh Phú (VCC_NAN_001_VPU)' -> 'VPU'
        'Trung tâm Mường Xén (VCC_NAN_014_MXN)' -> 'MXN'
        'VCC_NAN_006_QLU' -> 'QLU'
        'TDG' -> 'TDG'
    """
    if not full_name:
        return ""

    text = full_name.strip()

    # Search for text inside parentheses, e.g. (VCC_NAN_001_VPU)
    paren_match = re.search(r'\(([^)]+)\)', text)
    if paren_match:
        inside = paren_match.group(1).strip()
        # Look for the last chunk after an underscore
        if "_" in inside:
            parts = inside.split("_")
            last_part = parts[-1].strip()
            if last_part:
                return last_part
        return inside

    # Fallback: if no parentheses, look for underscore pattern
    if "_" in text:
        parts = text.split("_")
        last_part = parts[-1].strip()
        if last_part:
            return last_part

    # Fallback: clean non-alphanumeric and return uppercase
    return text.strip().upper()


def extract_center_name(full_name: str) -> str:
    """
    Extracts the readable center name before the parenthetical code.
    Example:
        'Trung tâm Vinh Phú (VCC_NAN_001_VPU)' -> 'Trung tâm Vinh Phú'
    """
    if not full_name:
        return ""
    text = full_name.strip()
    idx = text.find("(")
    if idx != -1:
        return text[:idx].strip()
    return text


def format_safe_integer(val: any) -> int:
    """Safely parses any value to integer, returning 0 if invalid."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        try:
            return int(round(val))
        except (ValueError, OverflowError):
            return 0
    if isinstance(val, str):
        val = val.strip().replace(",", "").replace(".", "")
        if not val:
            return 0
        try:
            return int(val)
        except ValueError:
            return 0
    return 0


def format_safe_float(val: any) -> float:
    """Safely parses any value to float, returning 0.0 if invalid."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip().replace("%", "")
        try:
            return float(val) / 100.0 if "%" in str(val) else float(val)
        except ValueError:
            return 0.0
    return 0.0


def parse_file_modified_time(filepath: str) -> str:
    """Returns human-readable last modified timestamp of a file."""
    try:
        mtime = os.path.getmtime(filepath)
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "Không xác định"
