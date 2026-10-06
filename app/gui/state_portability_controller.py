from __future__ import annotations

from collections.abc import Callable
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.settings_store import SettingsStore
from app.state_portability import export_state, import_state

LOGGER = logging.getLogger(__name__)


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
        except Exception as exc:
            LOGGER.exception("Zustandsexport fehlgeschlagen")
            QMessageBox.critical(
                self.window,
                "Export fehlgeschlagen",
                f"Der Export wurde sicher gestoppt.\n\n{exc}",
            )
            return

        self.window.status_label.setText("OK · Export geprüft und gespeichert")
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
        except Exception as exc:
            LOGGER.exception("Zustandsimport fehlgeschlagen")
            QMessageBox.critical(
                self.window,
                "Import abgelehnt",
                f"Die Datei wurde nicht übernommen.\n\n{exc}",
            )
            return

        imported_settings = payload.get("settings")
        if isinstance(imported_settings, dict):
            self.settings.update(imported_settings)
            self.store.save(self.settings)
            self.apply_loaded_settings()

        self.window._refresh_collections()
        self.window.status_label.setText("OK · Import vor- und nachgeprüft")
        QMessageBox.information(
            self.window,
            "Import abgeschlossen",
            "Der virtuelle Zustand wurde sicher übernommen."
            f"\n\nVorheriger Zustand gesichert unter:\n{backup}",
        )
