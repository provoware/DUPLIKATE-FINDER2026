from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QMessageBox

from app.error_management import record_error
from app.gui.status_feedback import set_status


def report_ui_error(
    window: Any,
    *,
    area: str,
    title: str,
    lead: str,
    error: BaseException,
) -> None:
    """Protokolliert GUI-Fehler einheitlich und zeigt eine laiengerechte Lösung."""
    message = str(error) or error.__class__.__name__
    entry = record_error(window.base_dir / "logs", area, message)
    set_status(window.status_label, f"Fehler · {title}", "error")
    QMessageBox.critical(
        window,
        title,
        f"{lead}\n\n{message}\n\nLösung: {entry['solution']}",
    )
