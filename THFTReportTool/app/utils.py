"""
Helper utilities for THFT Report Tool.
Includes center name parsing, safe integer conversion, date formatting, and text sanitization.
"""

import re
import datetime
from typing import Tuple, Any, Optional


def parse_center(raw: Optional[str]) -> Tuple[str, str]:
    """
    Parses center string into (center_code, center_name).
    Examples:
    'Trung tâm Diễn Châu (VCC_NAN_004_DCU)' -> ('DCU', 'Diễn Châu')
    'Trung tâm Kim Liên (VCC_NAN_002_KLN)' -> ('KLN', 'Kim Liên')
    'DCU' -> ('DCU', 'DCU')
    """
    if not raw or not str(raw).strip():
        return "UNKNOWN", "Chưa xác định"

    raw_str = str(raw).strip()

    # Pattern: 'Trung tâm <Name> (<..._><CODE>)'
    m = re.search(r'^(?:Trung tâm\s*)?(.*?)\s*\((?:.*_)?([A-Za-z0-9]+)\)$', raw_str)
    if m:
        name = m.group(1).strip()
        code = m.group(2).strip().upper()
        if not name:
            name = code
        return code, name

    # Pattern: just uppercase code like 'DCU' or 'VPU'
    if re.match(r'^[A-Za-z0-9]{3,4}$', raw_str):
        return raw_str.upper(), raw_str.upper()

    # Fallback: clean up non-word characters
    clean = re.sub(r'[\(\)\[\]]', '', raw_str)
    code = clean[:10].replace(" ", "_").upper()
    return code, raw_str


def safe_int(val: Any, default: int = 0) -> int:
    """
    Safely converts a cell value to integer.
    Handles None, empty strings, float strings, formula texts, '#N/A', etc.
    """
    if val is None:
        return default
    if isinstance(val, (int, float)):
        try:
            return int(round(val))
        except (ValueError, OverflowError):
            return default

    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "blank", "#n/a", "#value!", "-", ""):
        return default

    # If it's an uncalculated Excel formula (starts with =)
    if s.startswith("="):
        # We can't evaluate formulas directly here
        return default

    try:
        return int(round(float(s)))
    except (ValueError, TypeError):
        return default


def parse_report_date(date_val: Any = None, filename: str = "") -> Tuple[str, str]:
    """
    Determines report date string.
    Returns:
    - full_date: 'DD/MM/YYYY' (e.g. '28/09/2026')
    - day_month: 'DD/MM' (e.g. '28/9')
    """
    # 1. From datetime object
    if isinstance(date_val, (datetime.datetime, datetime.date)):
        full = date_val.strftime("%d/%m/%Y")
        dm = f"{date_val.day}/{date_val.month}"
        return full, dm

    # 2. From filename (e.g. 'WoExport28_09_2026_15_21_28.xlsx' or 'ĐH WO UT1 (05102026) (1).xlsx')
    if filename:
        m1 = re.search(r'(\d{2})_(\d{2})_(\d{4})', filename)
        if m1:
            day, month, year = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
            return f"{day:02d}/{month:02d}/{year}", f"{day}/{month}"

        m2 = re.search(r'\((\d{2})(\d{2})(\d{4})\)', filename)
        if m2:
            day, month, year = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
            return f"{day:02d}/{month:02d}/{year}", f"{day}/{month}"

    # 3. Fallback to current date
    now = datetime.datetime.now()
    return now.strftime("%d/%m/%Y"), f"{now.day}/{now.month}"


def sanitize_sheet_name(name: str) -> str:
    r"""Excel sheet name max 31 chars and no : \ / ? * [ ]"""
    clean = re.sub(r'[:\\/?*\[\]]', '_', name.strip())
    return clean[:31] if len(clean) > 31 else clean
