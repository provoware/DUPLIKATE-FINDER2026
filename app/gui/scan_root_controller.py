from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.validation import validate_scan_root


class ScanRootController:
    """Kapselt Auswahl und Synchronisierung des gemeinsamen Suchordners."""

    def __init__(self, window: Any) -> None:
        self.window = window

    def choose(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self.window,
            "Suchordner wählen",
            str(Path.home()),
        )
        if not chosen:
            return

        validation = validate_scan_root(Path(chosen))
        if not validation.ok:
            QMessageBox.information(
                self.window,
                validation.title,
                validation.message,
            )
            return

        self.window.selected_root = Path(chosen)
        self.window.root_label.setText(chosen)
        self.window.duplicate_root.setText(f"Suchordner: {chosen}")
