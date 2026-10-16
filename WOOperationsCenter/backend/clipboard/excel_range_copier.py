"""
Excel Range Copier & Parser for WO Operations Center.
Allows opening an Excel file (either raw input or exported report),
inspecting its worksheets, selecting an Excel cell range (e.g. A1:T30),
previewing the formatted table, and copying directly to the Windows Clipboard
as structured HTML Table (preserving merged cells, colors, borders, font weights),
TSV (tab-separated for Excel), and Plain Text.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import openpyxl
from openpyxl.utils import get_column_letter, range_boundaries

from backend.clipboard.clipboard_engine import ClipboardEngine

logger = logging.getLogger(__name__)


def _normalize_hex_color(color_val) -> Optional[str]:
    """Extracts a valid 6-character hex color string from openpyxl color object."""
    if not color_val:
        return None
    try:
        rgb = getattr(color_val, "rgb", None)
        if rgb and isinstance(rgb, str):
            # RGB could be AARRGGBB or RRGGBB
            clean = rgb.strip().upper()
            if len(clean) == 8:
                return f"#{clean[2:]}"
            elif len(clean) == 6:
                return f"#{clean}"
    except Exception:
        pass
    return None


class ExcelRangeCopier:
    """Provides Excel range inspection, HTML table generation, and clipboard copying."""

    @classmethod
    def get_sheet_names(cls, file_path: str) -> List[str]:
        """Returns the list of worksheet names in an Excel file without heavy loading."""
        if not os.path.exists(file_path):
            return []
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True)
            names = wb.sheetnames
            wb.close()
            return names
        except Exception as e:
            logger.error(f"Failed to read sheet names from {file_path}: {e}")
            return []

    @classmethod
    def parse_range(
        cls,
        file_path: str,
        sheet_name: str,
        range_str: Optional[str] = None,
        max_preview_rows: int = 150
    ) -> Dict[str, Any]:
        """
        Parses an Excel range from a file and produces:
        - preview_rows: 2D array of cells for frontend rendering
        - html_table: Clean styled HTML <table>
        - tsv_text: TSV string
        - plain_text: Formatted text table
        - dimensions: min/max row/col
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Tệp không tồn tại: {file_path}")

        wb = openpyxl.load_workbook(file_path, data_only=True)
        if sheet_name not in wb.sheetnames:
            sheet_name = wb.sheetnames[0]
        ws = wb[sheet_name]

        # Determine boundaries
        if range_str and ":" in range_str:
            try:
                min_col, min_row, max_col, max_row = range_boundaries(range_str.strip().upper())
            except Exception:
                min_col, min_row, max_col, max_row = 1, 1, ws.max_column, ws.max_row
        else:
            min_col = 1
            min_row = 1
            max_col = min(ws.max_column or 20, 30)
            max_row = min(ws.max_row or 50, 200)

        # Cap range if unreasonably large to protect UI
        max_row = min(max_row, min_row + 500)
        max_col = min(max_col, min_col + 40)

        resolved_range = f"{get_column_letter(min_col)}{min_row}:{get_column_letter(max_col)}{max_row}"

        # Build merged cells map: (row, col) -> (rowspan, colspan, is_slave)
        merged_map: Dict[Tuple[int, int], Dict[str, Any]] = {}
        for rng in ws.merged_cells.ranges:
            rng_min_col, rng_min_row, rng_max_col, rng_max_row = rng.min_col, rng.min_row, rng.max_col, rng.max_row
            # Check overlap with requested range
            if not (rng_max_col < min_col or rng_min_col > max_col or rng_max_row < min_row or rng_min_row > max_row):
                r_span = rng_max_row - rng_min_row + 1
                c_span = rng_max_col - rng_min_col + 1
                for r in range(rng_min_row, rng_max_row + 1):
                    for c in range(rng_min_col, rng_max_col + 1):
                        if r == rng_min_row and c == rng_min_col:
                            merged_map[(r, c)] = {"is_master": True, "rowspan": r_span, "colspan": c_span}
                        else:
                            merged_map[(r, c)] = {"is_master": False, "rowspan": 1, "colspan": 1}

        preview_rows = []
        html_lines = [
            "<table border='1' cellspacing='0' cellpadding='4' style='border-collapse: collapse; border: 1px solid #000; font-family: Arial, sans-serif; font-size: 11px;'>"
        ]
        tsv_lines = []

        for r in range(min_row, max_row + 1):
            row_preview = []
            html_row_cells = []
            tsv_row_cells = []

            for c in range(min_col, max_col + 1):
                cell = ws.cell(r, c)
                val = cell.value
                val_str = "" if val is None else str(val)

                # Check merged status
                m_info = merged_map.get((r, c))
                is_slave = False
                rowspan = 1
                colspan = 1

                if m_info:
                    if not m_info["is_master"]:
                        is_slave = True
                    else:
                        rowspan = m_info["rowspan"]
                        colspan = m_info["colspan"]

                # Extract styling
                bg_color = None
                if cell.fill and getattr(cell.fill, "fill_type", None) == "solid":
                    bg_color = _normalize_hex_color(getattr(cell.fill, "start_color", None))

                font_color = None
                bold = False
                if cell.font:
                    bold = bool(cell.font.bold)
                    font_color = _normalize_hex_color(getattr(cell.font, "color", None))

                align = "left"
                if cell.alignment and cell.alignment.horizontal:
                    align = cell.alignment.horizontal
                elif isinstance(val, (int, float)):
                    align = "right"

                cell_dict = {
                    "r": r,
                    "c": c,
                    "val": val_str,
                    "bg": bg_color,
                    "color": font_color or "#000000",
                    "bold": bold,
                    "align": align,
                    "rowspan": rowspan,
                    "colspan": colspan,
                    "is_slave": is_slave
                }
                row_preview.append(cell_dict)

                if not is_slave:
                    style_parts = [
                        "border: 1px solid #000",
                        f"text-align: {align}"
                    ]
                    if bg_color:
                        style_parts.append(f"background-color: {bg_color}")
                    if font_color:
                        style_parts.append(f"color: {font_color}")
                    if bold:
                        style_parts.append("font-weight: bold")

                    style_attr = "; ".join(style_parts)
                    span_attr = ""
                    if rowspan > 1:
                        span_attr += f" rowspan='{rowspan}'"
                    if colspan > 1:
                        span_attr += f" colspan='{colspan}'"

                    safe_val = val_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
                    html_row_cells.append(f"<td style='{style_attr}'{span_attr}>{safe_val}</td>")

                tsv_row_cells.append(val_str.replace("\t", " ").replace("\n", " "))

            if html_row_cells:
                html_lines.append(f"<tr>{''.join(html_row_cells)}</tr>")
            tsv_lines.append("\t".join(tsv_row_cells))

            if len(preview_rows) < max_preview_rows:
                preview_rows.append(row_preview)

        html_lines.append("</table>")
        html_table = "".join(html_lines)
        tsv_text = "\n".join(tsv_lines)

        wb.close()

        return {
            "sheet_name": sheet_name,
            "range_str": resolved_range,
            "total_rows": max_row - min_row + 1,
            "total_cols": max_col - min_col + 1,
            "preview_rows": preview_rows,
            "html_table": html_table,
            "tsv_text": tsv_text,
            "plain_text": tsv_text
        }

    @classmethod
    def copy_range_to_clipboard(
        cls,
        file_path: str,
        sheet_name: str,
        range_str: Optional[str] = None,
        copy_mode: str = "html"
    ) -> bool:
        """
        Parses the Excel range and sets it to system clipboard in the requested mode:
        - 'html': CF_HTML with TSV fallback
        - 'tsv': Plain TSV (for Excel paste)
        - 'text': Plain text
        """
        data = cls.parse_range(file_path, sheet_name, range_str)
        if copy_mode == "html":
            return ClipboardEngine.set_system_clipboard(data["tsv_text"], data["html_table"])
        elif copy_mode == "tsv":
            return ClipboardEngine.set_system_clipboard(data["tsv_text"])
        elif copy_mode == "text":
            return ClipboardEngine.set_system_clipboard(data["plain_text"])
        return False
