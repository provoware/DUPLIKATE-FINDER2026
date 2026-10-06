from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Any

from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.settings_store import SettingsStore
from app.state_portability import export_state, import_state
from app.gui.error_feedback import report_ui_error
from app.gui.status_feedback import set_status


class StatePortabilityController:
    """Kapselt sicheren Export und Import des virtuellen PROVOWARE-Zustands."""

    def __init__(
        self,
        window: Any,
        base_dir: Path,
        database: Any,
        store: SettingsStore,
        settings: dict,
        collect_settings: Callable[[], dict],
        apply_loaded_settings: Callable[[], None],
    ) -> None:
        self.window = window
        self.base_dir = base_dir
        self.database = database
        self.store = store
        self.settings = settings
        self.collect_settings = collect_settings
        self.apply_loaded_settings = apply_loaded_settings

    def export(self) -> None:
        default = self.base_dir / "exports" / "PROVOWARE-Zustand.json"
        path, _ = QFileDialog.getSaveFileName(
            self.window,
            "PROVOWARE-Zustand exportieren",
            str(default),
            "JSON-Datei (*.json)",
        )
        if not path:
            return

        target = Path(path)
        try:
            export_state(
                self.database,
                target,
                self.collect_settings(),
            )
        except (OSError, sqlite3.Error, TypeError, ValueError) as exc:
            report_ui_error(
                self.window,
                area="zustandsexport",
                title="Export fehlgeschlagen",
                lead="Der Export wurde sicher gestoppt.",
                error=exc,
            )
            return

        set_status(self.window.status_label, "OK · Export geprüft und gespeichert", "ok")
        QMessageBox.information(
            self.window,
            "Export abgeschlossen",
            "Virtuelle Organisation und Einstellungen wurden exportiert."
            f"\n\n{target}\n\nOriginaldateien wurden nicht kopiert.",
        )

    def import_state(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "PROVOWARE-Zustand importieren",
            str(self.base_dir / "exports"),
            "JSON-Datei (*.json)",
        )
        if not path:
            return

        answer = QMessageBox.question(
            self.window,
            "Import vorprüfen und übernehmen",
            "Importiert werden nur Einstellungen, Markierungen und virtuelle "
            "Sammlungen. Originaldateien werden nicht verändert.\n\nFortfahren?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        backup = (
            self.base_dir
            / "recovery"
            / f"PROVOWARE-vor-Import-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )
        try:
            export_state(
                self.database,
                backup,
                self.collect_settings(),
            )
            payload = import_state(self.database, Path(path))
        except (OSError, sqlite3.Error, ValueError) as exc:
            report_ui_error(
                self.window,
                area="zustandsimport",
                title="Import abgelehnt",
                lead="Die Datei wurde nicht übernommen.",
                error=exc,
            )
            return

        imported_settings = payload.get("settings")
        try:
            if isinstance(imported_settings, dict):
                self.settings.update(imported_settings)
                self.store.save(self.settings)
                self.apply_loaded_settings()
            self.window._refresh_collections()
        except (OSError, sqlite3.Error, ValueError) as exc:
            report_ui_error(
                self.window,
                area="zustandsimport-nachbereitung",
                title="Import übernommen · Nachbereitung fehlgeschlagen",
                lead=(
                    "Der virtuelle Zustand wurde importiert, aber Einstellungen "
                    "oder Anzeige konnten danach nicht vollständig aktualisiert werden."
                ),
                error=exc,
            )
            return

        set_status(self.window.status_label, "OK · Import vor- und nachgeprüft", "ok")
        QMessageBox.information(
            self.window,
            "Import abgeschlossen",
            "Der virtuelle Zustand wurde sicher übernommen."
            f"\n\nVorheriger Zustand gesichert unter:\n{backup}",
        )
