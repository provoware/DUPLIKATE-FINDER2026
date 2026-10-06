from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QMessageBox


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
        state = self.window.database.virtual_item(path)
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
        self.window.database.set_virtual_item(
            path,
            marked,
            self.window.result_note.text(),
        )
        self.window.results_model.set_marked(path, marked)
        self.window.status_label.setText(
            "OK · Virtuelle Markierung gespeichert"
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

        self.window.database.add_collection_item(
            int(collection_id),
            path,
            self.window.result_note.text(),
        )
        self.window.collection_controller.show(
            self.window.collection_list.currentRow()
        )
        self.window.status_label.setText(
            "OK · Treffer virtuell zur Sammlung hinzugefügt"
        )
