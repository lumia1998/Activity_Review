from __future__ import annotations

import sqlite3
from typing import Any

from ..core.paths import database_path
from .data_service import initialize_database


def save_report(report: dict[str, Any]) -> dict[str, Any]:
    initialize_database()
    connection = sqlite3.connect(database_path())
    try:
        connection.execute(
            """
            INSERT OR REPLACE INTO daily_reports (date, locale, content, ai_mode, model_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                report['date'],
                report.get('locale', 'zh-CN'),
                report['content'],
                report['ai_mode'],
                report.get('model_name'),
                report['created_at'],
            ),
        )
        connection.commit()
    finally:
        connection.close()
    return report
