from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QMessageBox

from app.core.scanner import ScanOptions
from app.error_management import record_error
from app.validation import ValidationResult
from app.gui.status_feedback import set_status


def show_validation_error(window: Any, validation: ValidationResult) -> bool:
    if validation.ok:
        return False
    QMessageBox.information(window, validation.title, validation.message)
    return True


def current_scan_options(window: Any) -> ScanOptions:
    options = ScanOptions(
        exclude_python_project_dirs=window.exclude_python_box.isChecked(),
        excluded_extensions=window.scan_options.excluded_extensions,
    )
    window.scan_options = options
    return options


def prepare_process_start(window: Any, status_text: str) -> None:
    set_status(window.status_label, status_text, "neutral")
    window.activity_label.setText("Aktivität: Dateiliste wird vorbereitet")
    window.step_label.setText("Schritt: Dateien inventarisieren")
    window.eta_label.setText("Restzeit: wird ermittelt")
    window.progress_bar.setRange(0, 0)


def fail_process(
    window: Any,
    *,
    area: str,
    button: Any,
    status_text: str,
    dialog_title: str,
    lead_text: str,
    message: str,
) -> None:
    entry = record_error(window.base_dir / "logs", area, message)
    button.setEnabled(True)
    window._set_process_idle()
    set_status(window.status_label, status_text, "error")
    window.activity_label.setText("Aktivität: sicher gestoppt")
    window.progress_bar.setRange(0, 100)
    window.progress_bar.setValue(0)
    QMessageBox.critical(
        window,
        dialog_title,
        f"{lead_text}\n\n{message}\n\nLösung: {entry['solution']}",
    )
