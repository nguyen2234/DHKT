"""
SQLite repository for WO Operations Center.
Stores report generation history, custom message templates, and report metadata.
Database is located in Windows AppData directory.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.core.config import get_database_path
from backend.domain.models import ReportHistoryItem

logger = logging.getLogger(__name__)


class DatabaseRepository:
    """Manages SQLite tables for history, templates, and metadata."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path) if db_path else str(get_database_path())
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS report_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    report_date TEXT NOT NULL,
                    source_file_path TEXT NOT NULL,
                    source_file_fingerprint TEXT NOT NULL,
                    applied_filters TEXT,
                    center_selection TEXT,
                    output_path TEXT,
                    message_snapshot TEXT,
                    status TEXT DEFAULT 'success'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS custom_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    template_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    placeholders TEXT,
                    is_default INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_timestamp ON report_history(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_type ON report_history(report_type)
            """)
            conn.commit()

    def add_history(self, item: ReportHistoryItem) -> int:
        """Inserts a new report history entry and returns its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO report_history (
                    timestamp, report_type, report_date, source_file_path,
                    source_file_fingerprint, applied_filters, center_selection,
                    output_path, message_snapshot, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.timestamp or datetime.now().isoformat(),
                item.report_type,
                item.report_date,
                item.source_file_path,
                item.source_file_fingerprint,
                item.applied_filters,
                item.center_selection,
                item.output_path,
                item.message_snapshot,
                item.status
            ))
            conn.commit()
            return cursor.lastrowid

    def get_history(self, limit: int = 50, offset: int = 0, report_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves paginated report history records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if report_type:
                cursor.execute("""
                    SELECT * FROM report_history
                    WHERE report_type = ?
                    ORDER BY id DESC LIMIT ? OFFSET ?
                """, (report_type, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM report_history
                    ORDER BY id DESC LIMIT ? OFFSET ?
                """, (limit, offset))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_history_by_id(self, history_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM report_history WHERE id = ?", (history_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_history(self, history_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM report_history WHERE id = ?", (history_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all_history(self) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM report_history")
            conn.commit()
            return True

    def get_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if template_type:
                cursor.execute("SELECT * FROM custom_templates WHERE template_type = ? ORDER BY id ASC", (template_type,))
            else:
                cursor.execute("SELECT * FROM custom_templates ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

    def save_template(self, name: str, template_type: str, content: str, placeholders: str = "", is_default: bool = False) -> int:
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO custom_templates (name, template_type, content, placeholders, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, template_type, content, placeholders, 1 if is_default else 0, now, now))
            conn.commit()
            return cursor.lastrowid
