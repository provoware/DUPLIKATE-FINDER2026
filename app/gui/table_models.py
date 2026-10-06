from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.formatting import format_bytes
from app.models.entities import CollectionItem, DuplicateGroup, SearchHit
from app.storage.database import Database


class _PagedTableModel(QAbstractTableModel):
    """Gemeinsamer Vertrag für SQLite-seitenweise Tabellenmodelle."""

    HEADERS: tuple[str, ...] = ()

    def __init__(
        self,
        parent=None,
        *,
        page_size: int = 200,
        max_pages: int = 8,
    ) -> None:
        super().__init__(parent)
        self.page_size = max(25, int(page_size))
        self.max_pages = max(2, int(max_pages))
        self._count = 0
        self._sort_column = 0
        self._descending = False
        self._pages: OrderedDict[int, list[Any]] = OrderedDict()

    @property
    def cached_row_count(self) -> int:
        return sum(len(page) for page in self._pages.values())

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else self._count

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(
        self,
        section,
        orientation,
        role=Qt.ItemDataRole.DisplayRole,
    ):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(self.HEADERS)
        ):
            return self.HEADERS[section]
        return None

    def _cached_page(self, page_number: int):
        if page_number not in self._pages:
            return None
        page = self._pages.pop(page_number)
        self._pages[page_number] = page
        return page

    def _remember_page(self, page_number: int, page):
        self._pages[page_number] = page
        while len(self._pages) > self.max_pages:
            self._pages.popitem(last=False)
        return page

    def _row(self, row: int):
        if row < 0 or row >= self._count:
            return None
        page = self._load_page(row // self.page_size)
        local = row % self.page_size
        return page[local] if local < len(page) else None

    def _load_page(self, page_number: int):
        raise NotImplementedError

    def _set_sort_state(
        self,
        column: int,
        order: Qt.SortOrder,
    ) -> None:
        self._sort_column = max(0, min(len(self.HEADERS) - 1, int(column)))
        self._descending = order == Qt.SortOrder.DescendingOrder


class SearchResultsModel(_PagedTableModel):
    """Echte Treffer-Virtualisierung: SQLite + kleiner Seitenpuffer."""

    HEADERS = ("Markiert", "Quelle", "Datei", "Zeile", "Fundstelle")

    def __init__(
        self,
        database: Database,
        parent=None,
        page_size: int = 200,
        max_pages: int = 8,
    ) -> None:
        super().__init__(
            parent,
            page_size=page_size,
            max_pages=max_pages,
        )
        self.database = database
        self._job_id: int | None = None
        self._sort_column = 2

    def set_job(self, job_id: int | None, hit_count: int | None = None) -> None:
        self.beginResetModel()
        self._job_id = job_id
        self._count = (
            self.database.search_hit_count(job_id)
            if job_id is not None and hit_count is None
            else max(0, int(hit_count or 0))
        )
        self._pages.clear()
        self.endResetModel()

    def _load_page(self, page_number: int) -> list[tuple[SearchHit, bool]]:
        if self._job_id is None:
            return []
        cached = self._cached_page(page_number)
        if cached is not None:
            return cached
        page = self.database.search_hits_page(
            self._job_id,
            offset=page_number * self.page_size,
            limit=self.page_size,
            sort_column=self._sort_column,
            descending=self._descending,
        )
        return self._remember_page(page_number, page)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._row(index.row())
        if row is None:
            return None
        hit, marked = row
        path = hit.path
        if role == Qt.ItemDataRole.UserRole:
            return str(path)
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(path) if index.column() != 4 else hit.excerpt
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() in (0, 3):
            return int(Qt.AlignmentFlag.AlignCenter)
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if index.column() == 0:
            return "Ja" if marked else ""
        if index.column() == 1:
            return hit.source
        if index.column() == 2:
            return str(path)
        if index.column() == 3:
            return "" if hit.line_number is None else str(hit.line_number)
        if index.column() == 4:
            return hit.excerpt
        return None

    def hit_at(self, row: int) -> SearchHit | None:
        value = self._row(row)
        return value[0] if value else None

    def path_at(self, row: int) -> Path | None:
        hit = self.hit_at(row)
        return hit.path if hit else None

    def set_marked(self, path: Path, marked: bool) -> None:
        changed_rows: list[int] = []
        for page_number, page in list(self._pages.items()):
            changed = False
            updated = []
            for local_row, (hit, current) in enumerate(page):
                new_value = bool(marked) if hit.path == path else current
                changed = changed or (new_value != current)
                updated.append((hit, new_value))
                if new_value != current:
                    changed_rows.append(page_number * self.page_size + local_row)
            if changed:
                self._pages[page_number] = updated
        for row in changed_rows:
            self.dataChanged.emit(
                self.index(row, 0),
                self.index(row, 0),
                [Qt.ItemDataRole.DisplayRole],
            )

    def sort(
        self,
        column: int,
        order: Qt.SortOrder = Qt.SortOrder.AscendingOrder,
    ) -> None:
        self.layoutAboutToBeChanged.emit()
        self._set_sort_state(column, order)
        self._pages.clear()
        self.layoutChanged.emit()


class DuplicateMembersModel(_PagedTableModel):
    """Produktiv SQLite-seitenweise; Legacy-set_group bleibt für kleine API-Tests."""

    HEADERS = ("Datei", "Ordner", "Größe", "Geändert")

    def __init__(
        self,
        database: Database | None = None,
        parent=None,
        page_size: int = 200,
        max_pages: int = 8,
    ) -> None:
        super().__init__(
            parent,
            page_size=page_size,
            max_pages=max_pages,
        )
        self.database = database
        self._group_id: int | None = None
        self._group_size = 0
        self._legacy_paths: list[Path] = []

    def set_group_id(
        self,
        group_id: int | None,
        *,
        size: int = 0,
        count: int | None = None,
    ) -> None:
        self.beginResetModel()
        self._group_id = group_id
        self._group_size = int(size)
        self._legacy_paths = []
        self._pages.clear()
        self._count = (
            self.database.duplicate_member_count(group_id)
            if self.database is not None and group_id is not None and count is None
            else max(0, int(count or 0))
        )
        self.endResetModel()

    def set_group(self, group: DuplicateGroup | None) -> None:
        self.beginResetModel()
        self._group_id = None
        self._pages.clear()
        self._legacy_paths = list(group.paths) if group else []
        self._group_size = int(group.size) if group else 0
        self._count = len(self._legacy_paths)
        self.endResetModel()

    def _load_page(self, page_number: int) -> list[tuple[Path, int, int]]:
        if self.database is None or self._group_id is None:
            start = page_number * self.page_size
            return [
                (path, self._group_size, 0)
                for path in self._legacy_paths[start : start + self.page_size]
            ]
        cached = self._cached_page(page_number)
        if cached is not None:
            return cached
        page = self.database.duplicate_members_page(
            self._group_id,
            offset=page_number * self.page_size,
            limit=self.page_size,
            sort_column=self._sort_column,
            descending=self._descending,
        )
        return self._remember_page(page_number, page)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._row(index.row())
        if row is None:
            return None
        path, size, mtime_ns = row
        if role == Qt.ItemDataRole.UserRole:
            return str(path)
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(path)
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if index.column() == 0:
            return path.name
        if index.column() == 1:
            return str(path.parent)
        if index.column() == 2:
            return format_bytes(size or self._group_size)
        if index.column() == 3:
            return (
                datetime.fromtimestamp(mtime_ns / 1_000_000_000).strftime(
                    "%Y-%m-%d %H:%M"
                )
                if mtime_ns
                else "nicht verfügbar"
            )
        return None

    def path_at(self, row: int) -> Path | None:
        value = self._row(row)
        return value[0] if value else None

    def sort(
        self,
        column: int,
        order: Qt.SortOrder = Qt.SortOrder.AscendingOrder,
    ) -> None:
        self.layoutAboutToBeChanged.emit()
        self._set_sort_state(column, order)
        if self.database is not None and self._group_id is not None:
            self._pages.clear()
        else:
            self._legacy_paths.sort(
                key=lambda path: (
                    path.name.casefold()
                    if self._sort_column == 0
                    else str(path).casefold()
                ),
                reverse=self._descending,
            )
        self.layoutChanged.emit()


class CollectionItemsModel(_PagedTableModel):
    """Produktiv SQLite-seitenweise; set_items bleibt als kleine Kompatibilitätsschicht."""

    HEADERS = ("Datei", "Ordner", "Notiz")

    def __init__(
        self,
        database: Database | None = None,
        parent=None,
        page_size: int = 200,
        max_pages: int = 8,
    ) -> None:
        super().__init__(
            parent,
            page_size=page_size,
            max_pages=max_pages,
        )
        self.database = database
        self._collection_id: int | None = None
        self._legacy_items: list[CollectionItem] = []

    def set_collection(self, collection_id: int | None) -> None:
        self.beginResetModel()
        self._collection_id = collection_id
        self._legacy_items = []
        self._pages.clear()
        self._count = (
            self.database.collection_item_count(collection_id)
            if self.database is not None and collection_id is not None
            else 0
        )
        self.endResetModel()

    def set_items(self, items: list[CollectionItem]) -> None:
        self.beginResetModel()
        self._collection_id = None
        self._pages.clear()
        self._legacy_items = list(items)
        self._count = len(self._legacy_items)
        self.endResetModel()

    def _load_page(self, page_number: int) -> list[CollectionItem]:
        if self.database is None or self._collection_id is None:
            start = page_number * self.page_size
            return self._legacy_items[start : start + self.page_size]
        cached = self._cached_page(page_number)
        if cached is not None:
            return cached
        page = self.database.collection_items_page(
            self._collection_id,
            offset=page_number * self.page_size,
            limit=self.page_size,
            sort_column=self._sort_column,
            descending=self._descending,
        )
        return self._remember_page(page_number, page)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        item = self._row(index.row())
        if item is None:
            return None
        if role == Qt.ItemDataRole.UserRole:
            return str(item.path)
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(item.path)
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if index.column() == 0:
            return item.path.name
        if index.column() == 1:
            return str(item.path.parent)
        if index.column() == 2:
            return item.note
        return None

    def path_at(self, row: int) -> Path | None:
        item = self._row(row)
        return item.path if item else None

    def sort(
        self,
        column: int,
        order: Qt.SortOrder = Qt.SortOrder.AscendingOrder,
    ) -> None:
        self.layoutAboutToBeChanged.emit()
        self._set_sort_state(column, order)
        if self.database is not None and self._collection_id is not None:
            self._pages.clear()
        else:
            def key(item: CollectionItem):
                if self._sort_column == 0:
                    return item.path.name.casefold()
                if self._sort_column == 1:
                    return str(item.path.parent).casefold()
                return item.note.casefold()

            self._legacy_items.sort(
                key=key,
                reverse=self._descending,
            )
        self.layoutChanged.emit()
