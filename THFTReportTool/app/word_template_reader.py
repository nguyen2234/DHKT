"""
Word Template Reader module.
Reads and inspects 'mẫu báo cáo FT.docx' to capture the exact layout,
styling, colors, font rules, and notification text pattern.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import docx

logger = logging.getLogger(__name__)


class WordTemplateReader:
    def __init__(self, template_path: Optional[str] = None):
        self.template_path = template_path
        self.notification_sample: str = ""
        self.table_headers: List[List[str]] = []
        self.shading_colors: List[str] = []

    def load_template(self, template_path: str) -> bool:
        if not os.path.exists(template_path):
            logger.warning(f"Word template not found at {template_path}")
            return False

        try:
            self.template_path = template_path
            doc = docx.Document(template_path)

            # 1. Read first non-empty paragraph
            for p in doc.paragraphs:
                if p.text.strip():
                    self.notification_sample = p.text.strip()
                    break

            # 2. Read table headers and shading
            if doc.tables:
                table = doc.tables[0]
                if len(table.rows) >= 2:
                    h1 = [c.text.strip() for c in table.rows[0].cells]
                    h2 = [c.text.strip() for c in table.rows[1].cells]
                    self.table_headers = [h1, h2]

                    # Extract shading fill
                    colors = []
                    for cell in table.rows[0].cells:
                        tcPr = cell._tc.get_or_add_tcPr()
                        shd = tcPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd')
                        fill = shd.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill') if shd is not None else "FFFFFF"
                        colors.append(fill)
                    self.shading_colors = colors

            logger.info("Successfully analyzed Word template.")
            return True
        except Exception as e:
            logger.error(f"Error reading Word template: {e}")
            return False

    def get_template_info(self) -> Dict[str, Any]:
        return {
            "notification_sample": self.notification_sample,
            "table_headers": self.table_headers,
            "shading_colors": self.shading_colors
        }
