from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QMessageBox

from app.gui.error_feedback import report_ui_error
from app.gui.status_feedback import set_status


class ResultController:
    """Kapselt virtuelle Markierungen, Notizen und Sammlungszuordnung von Treffern."""

    def __init__(self, window: Any) -> None:
        self.window = window

    def selected_path(self) -> Path | None:
        index = self.window.results.currentIndex()
        return (
            self.window.results_model.path_at(index.row())
            if index.isValid()
            else None
        )

    def load_selected_state(self) -> None:
        path = self.selected_path()
        if path is None:
            return
        try:
            state = self.window.database.virtual_item(path)
        except Exception as exc:
            report_ui_error(
                self.window,
                area="ergebnisstatus",
                title="Trefferstatus nicht geladen",
                lead="Die virtuelle Markierung oder Notiz konnte nicht geladen werden.",
                error=exc,
            )
            return
        self.window.result_mark.setChecked(state.marked)
        self.window.result_note.setText(state.note)

    def save_selected_state(self) -> None:
        path = self.selected_path()
        if path is None:
            QMessageBox.information(
                self.window,
                "Kein Treffer",
                "Bitte zuerst einen Treffer auswählen.",
            )
            return

        marked = self.window.result_mark.isChecked()
        try:
            self.window.database.set_virtual_item(
                path,
                marked,
                self.window.result_note.text(),
            )
        except Exception as exc:
            report_ui_error(
                self.window,
                area="ergebnisstatus",
                title="Markierung nicht gespeichert",
                lead="Die virtuelle Markierung und Notiz wurden nicht gespeichert.",
                error=exc,
            )
            return
        self.window.results_model.set_marked(path, marked)
        set_status(
            self.window.status_label,
            "OK · Virtuelle Markierung gespeichert",
            "ok",
        )

    def add_selected_to_collection(self) -> None:
        path = self.selected_path()
        collection_id = self.window.result_collection.currentData()
        if path is None:
            QMessageBox.information(
                self.window,
                "Kein Treffer",
                "Bitte zuerst einen Treffer auswählen.",
            )
            return
        if collection_id is None:
            QMessageBox.information(
                self.window,
                "Keine Sammlung",
                "Bitte zuerst eine Sammlung anlegen.",
            )
            return

        try:
            self.window.database.add_collection_item(
                int(collection_id),
                path,
                self.window.result_note.text(),
            )
            self.window.collection_controller.show(
                self.window.collection_list.currentRow()
            )
        except Exception as exc:
            report_ui_error(
                self.window,
                area="sammlungszuordnung",
                title="Treffer nicht zugeordnet",
                lead="Der Treffer konnte nicht zur virtuellen Sammlung hinzugefügt werden.",
                error=exc,
            )
            return
        set_status(
            self.window.status_label,
            "OK · Treffer virtuell zur Sammlung hinzugefügt",
            "ok",
        )
