from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem, QMessageBox

from app.texts import text as ui_text
from app.gui.error_feedback import report_ui_error
from app.gui.status_feedback import set_status


class CollectionController:
    """Kapselt Verwaltung und Anzeige virtueller Sammlungen."""

    def __init__(self, window: Any) -> None:
        self.window = window

    def create(self) -> None:
        name = self.window.collection_name.text().strip()
        note = self.window.collection_note.text().strip()
        try:
            collection_id = self.window.database.create_collection(name, note)
        except ValueError as exc:
            QMessageBox.information(
                self.window,
                ui_text("collections.error_name_title", "Name fehlt"),
                str(exc),
            )
            return
        except Exception as exc:
            report_ui_error(
                self.window,
                area="sammlungen",
                title=ui_text("collections.error_create_title", "Sammlung nicht angelegt"),
                lead="Die virtuelle Sammlung konnte nicht gespeichert werden.",
                error=exc,
            )
            return

        self.window.collection_name.clear()
        self.window.collection_note.clear()
        self.refresh(select_id=collection_id)
        set_status(
            self.window.status_label,
            ui_text("collections.status_created", "OK · Virtuelle Sammlung angelegt"),
            "ok",
        )

    def refresh(self, select_id: int | None = None) -> None:
        try:
            collections = self.window.database.collections()
        except Exception as exc:
            report_ui_error(
                self.window,
                area="sammlungen",
                title="Sammlungen nicht geladen",
                lead="Die virtuellen Sammlungen konnten nicht aus der Datenbank gelesen werden.",
                error=exc,
            )
            return
        self.window.collection_list.clear()
        self.window.result_collection.clear()
        target_row = -1

        for row, collection in enumerate(collections):
            item = QListWidgetItem(collection.name)
            item.setData(Qt.UserRole, collection.id)
            item.setToolTip(collection.note)
            self.window.collection_list.addItem(item)
            self.window.result_collection.addItem(collection.name, collection.id)
            if collection.id == select_id:
                target_row = row

        if collections:
            self.window.collection_list.setCurrentRow(
                target_row if target_row >= 0 else 0
            )
        else:
            self.window.collection_summary.setText(
                ui_text(
                    "collections.none_created",
                    "Noch keine Sammlung angelegt.",
                )
            )
            self.window.collection_items_model.set_collection(None)

    def current_id(self) -> int | None:
        item = self.window.collection_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        return int(value) if value is not None else None

    def show(self, _row: int) -> None:
        collection_id = self.current_id()
        if collection_id is None:
            self.window.collection_items_model.set_collection(None)
            return

        try:
            collections = self.window.database.collections()
        except Exception as exc:
            report_ui_error(
                self.window,
                area="sammlungen",
                title="Sammlung nicht geladen",
                lead="Die ausgewählte virtuelle Sammlung konnte nicht gelesen werden.",
                error=exc,
            )
            self.window.collection_items_model.set_collection(None)
            return

        collection = next(
            (
                candidate
                for candidate in collections
                if candidate.id == collection_id
            ),
            None,
        )
        if collection is None:
            self.window.collection_items_model.set_collection(None)
            return

        try:
            count = self.window.database.collection_item_count(collection_id)
        except Exception as exc:
            report_ui_error(
                self.window,
                area="sammlungen",
                title="Sammlungsinhalt nicht geladen",
                lead="Die Anzahl der Einträge konnte nicht gelesen werden.",
                error=exc,
            )
            self.window.collection_items_model.set_collection(None)
            return
        suffix = f" · {collection.note}" if collection.note else ""
        self.window.collection_summary.setText(
            f"{collection.name} · {count} Einträge{suffix}"
        )
        self.window.collection_items_model.set_collection(collection_id)

    def remove_selected_item(self) -> None:
        collection_id = self.current_id()
        index = self.window.collection_items_table.currentIndex()
        path = (
            self.window.collection_items_model.path_at(index.row())
            if index.isValid()
            else None
        )
        if collection_id is None or path is None:
            QMessageBox.information(
                self.window,
                ui_text("collections.no_selection_title", "Keine Auswahl"),
                ui_text(
                    "collections.no_selection_message",
                    "Bitte einen Sammlungseintrag auswählen.",
                ),
            )
            return

        try:
            self.window.database.remove_collection_item(collection_id, path)
            self.show(self.window.collection_list.currentRow())
        except Exception as exc:
            report_ui_error(
                self.window,
                area="sammlungen",
                title="Eintrag nicht entfernt",
                lead="Der virtuelle Sammlungseintrag konnte nicht entfernt werden.",
                error=exc,
            )
            return
        set_status(
            self.window.status_label,
            ui_text(
                "collections.status_removed",
                "OK · Eintrag nur aus der virtuellen Sammlung entfernt",
            ),
            "ok",
        )
