from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, QSortFilterProxyModel, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFileSystemModel,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.file_browser.classification import classify_path
from app.file_browser.preview import build_preview
from app.safety.policy import SafetyPolicy, SafetyViolation
from app.storage.database import Database


class FileFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._query = ""
        self._kind = "all"
        self.setDynamicSortFilter(True)

    def set_query(self, value: str) -> None:
        self._query = value.casefold().strip()
        self.invalidateFilter()

    def set_kind(self, value: str) -> None:
        self._kind = value
        self.invalidateFilter()

    def filterAcceptsRow(self, row: int, parent: QModelIndex) -> bool:
        source = self.sourceModel()
        index = source.index(row, 0, parent)
        if not index.isValid():
            return False
        path = Path(source.filePath(index))
        if source.isDir(index):
            return True
        if self._query and self._query not in path.name.casefold():
            return False
        if self._kind != "all" and classify_path(path, is_dir=False).key != self._kind:
            return False
        return True


class FileBrowserWidget(QWidget):
    def __init__(self, database: Database, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.setObjectName("file_browser")
        self.setProperty("area", "files")
        self._root: Path | None = None
        self._current_path: Path | None = None

        self.model = QFileSystemModel(self)
        self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
        self.model.setReadOnly(True)
        self.model.setRootPath("")

        self.proxy = FileFilterProxy(self)
        self.proxy.setSourceModel(self.model)
        self.setLayout(self._build_layout())

    def _build_layout(self) -> QVBoxLayout:
        root = QVBoxLayout()
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(6)

        controls = QGridLayout()
        self.root_label = QLineEdit()
        self.root_label.setObjectName("file_browser_root")
        self.root_label.setReadOnly(True)
        self.root_label.setPlaceholderText("Noch kein Ordner oder Datenträger gewählt")
        self.root_label.setAccessibleName("Aktueller Dateiordner")

        choose = QPushButton("Ordner wählen")
        choose.setObjectName("file_browser_choose")
        choose.setProperty("primaryAction", True)
        choose.setAccessibleName("Ordner oder externen Datenträger auswählen")
        choose.clicked.connect(self.choose_root)

        up = QPushButton("Hoch")
        up.setObjectName("file_browser_up")
        up.clicked.connect(self.go_up)

        refresh = QPushButton("Neu laden")
        refresh.setObjectName("file_browser_refresh")
        refresh.clicked.connect(self.refresh_view)

        self.query = QLineEdit()
        self.query.setObjectName("file_browser_query")
        self.query.setPlaceholderText("Dateiname filtern")
        self.query.setAccessibleName("Dateiliste nach Dateiname filtern")
        self.query.textChanged.connect(self.proxy.set_query)

        self.kind = QComboBox()
        self.kind.setObjectName("file_browser_kind")
        self.kind.setAccessibleName("Dateityp filtern")
        self.kind.addItem("Alle Dateitypen", "all")
        self.kind.addItem("Text", "text")
        self.kind.addItem("Bilder", "image")
        self.kind.addItem("PDF", "pdf")
        self.kind.addItem("Video", "video")
        self.kind.addItem("Audio", "audio")
        self.kind.addItem("Andere Dateien", "other")
        self.kind.currentIndexChanged.connect(
            lambda _index: self.proxy.set_kind(str(self.kind.currentData()))
        )

        controls.addWidget(self.root_label, 0, 0, 1, 3)
        controls.addWidget(choose, 0, 3)
        controls.addWidget(self.query, 1, 0, 1, 2)
        controls.addWidget(self.kind, 1, 2)
        compact_tools = QHBoxLayout()
        compact_tools.setSpacing(4)
        compact_tools.addWidget(up)
        compact_tools.addWidget(refresh)
        controls.addLayout(compact_tools, 1, 3)
        root.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("file_browser_splitter")

        self.table = QTableView()
        self.table.setObjectName("file_browser_table")
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMinimumWidth(0)
        self.table.doubleClicked.connect(self._activate_index)
        self.table.selectionModel().currentChanged.connect(self._selection_changed)
        self.table.horizontalHeader().setStretchLastSection(True)
        splitter.addWidget(self.table)

        preview_frame = QFrame()
        preview_frame.setObjectName("file_preview_panel")
        preview_frame.setMinimumWidth(0)
        preview_frame.setProperty("section", True)
        preview_layout = QVBoxLayout(preview_frame)

        self.preview_title = QLabel("Keine Datei ausgewählt")
        self.preview_title.setObjectName("file_preview_title")
        self.preview_title.setWordWrap(True)
        self.preview_title.setProperty("heading", True)
        preview_layout.addWidget(self.preview_title)

        self.preview_image = QLabel("Vorschau")
        self.preview_image.setObjectName("file_preview_image")
        self.preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image.setMinimumHeight(36)
        self.preview_image.setWordWrap(True)
        preview_layout.addWidget(self.preview_image, 2)

        self.preview_text = QTextBrowser()
        self.preview_text.setObjectName("file_preview_text")
        self.preview_text.setOpenExternalLinks(False)
        self.preview_text.setVisible(False)
        preview_layout.addWidget(self.preview_text, 2)

        self.preview_details = QLabel("Metadaten erscheinen hier.")
        self.preview_details.setObjectName("file_preview_details")
        self.preview_details.setWordWrap(True)
        self.preview_details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        preview_layout.addWidget(self.preview_details)

        actions = QGridLayout()
        self.open_button = QPushButton("Öffnen")
        self.open_button.setObjectName("file_browser_open")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_current)

        self.show_button = QPushButton("Ordner")
        self.show_button.setObjectName("file_browser_show")
        self.show_button.setEnabled(False)
        self.show_button.clicked.connect(self.show_current_folder)

        self.copy_button = QPushButton("Pfad kopieren")
        self.copy_button.setObjectName("file_browser_copy")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy_current_path)

        self.mark_button = QPushButton("Markieren")
        self.mark_button.setObjectName("file_browser_mark")
        self.mark_button.setEnabled(False)
        self.mark_button.clicked.connect(self.toggle_mark)

        self.collection_button = QPushButton("Zu Sammlung")
        self.collection_button.setObjectName("file_browser_collection")
        self.collection_button.setEnabled(False)
        self.collection_button.clicked.connect(self.add_to_collection)

        actions.addWidget(self.open_button, 0, 0)
        actions.addWidget(self.show_button, 0, 1)
        actions.addWidget(self.copy_button, 0, 2)
        actions.addWidget(self.mark_button, 1, 0)
        actions.addWidget(self.collection_button, 1, 1, 1, 2)
        preview_layout.addLayout(actions)

        splitter.addWidget(preview_frame)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

        note = QLabel(
            "Nur lesen: Vorschau und externe Öffnung verändern keine Dateien. "
            "Löschen, Verschieben, Umbenennen und Überschreiben bleiben gesperrt."
        )
        note.setObjectName("file_browser_safety")
        note.setProperty("card", True)
        note.setWordWrap(True)
        root.addWidget(note)
        return root

    def choose_root(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Ordner oder Datenträger wählen", str(self._root or Path.home()))
        if chosen:
            self.set_root(Path(chosen))

    def go_up(self) -> None:
        if self._root is None:
            return
        parent = self._root.parent
        if parent != self._root:
            self.set_root(parent)

    def refresh_view(self) -> None:
        if self._root is None:
            return
        current = self._root
        self.model.setRootPath("")
        self.set_root(current)

    def set_root(self, root: Path) -> bool:
        try:
            safe = SafetyPolicy().ensure_scan_root_allowed(root)
        except SafetyViolation as exc:
            QMessageBox.information(self, "Ordner gesperrt", str(exc))
            return False
        if not safe.is_dir():
            QMessageBox.information(self, "Kein Ordner", "Der gewählte Pfad ist kein lesbarer Ordner.")
            return False
        source_index = self.model.setRootPath(str(safe))
        proxy_index = self.proxy.mapFromSource(source_index)
        self.table.setRootIndex(proxy_index)
        self.root_label.setText(str(safe))
        self._root = safe
        self._clear_preview("Ordner gewählt. Datei anklicken, um die Vorschau zu öffnen.")
        return True

    def _path_for_proxy_index(self, index: QModelIndex) -> Path | None:
        if not index.isValid():
            return None
        source_index = self.proxy.mapToSource(index.siblingAtColumn(0))
        if not source_index.isValid():
            return None
        return Path(self.model.filePath(source_index))

    def _selection_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        path = self._path_for_proxy_index(current)
        if path is not None:
            self.show_preview(path)

    def _activate_index(self, index: QModelIndex) -> None:
        path = self._path_for_proxy_index(index)
        if path is None:
            return
        if path.is_dir():
            self.set_root(path)
        else:
            self.show_preview(path)

    def show_preview(self, path: Path) -> None:
        self._current_path = path
        exists = path.exists()
        is_link = path.is_symlink()
        self.open_button.setEnabled(exists and not is_link)
        self.show_button.setEnabled(exists)
        self.copy_button.setEnabled(True)
        self.mark_button.setEnabled(exists and not path.is_dir() and not is_link)
        self.collection_button.setEnabled(exists and not path.is_dir() and not is_link)

        if is_link:
            self.preview_title.setText(path.name)
            self.preview_image.clear()
            self.preview_image.setText("Symbolische Verknüpfung – Vorschau und externes Öffnen sind aus Sicherheitsgründen deaktiviert.")
            self.preview_image.setVisible(True)
            self.preview_text.setVisible(False)
            self.preview_details.setText(f"Pfad: {path}\nTyp: symbolische Verknüpfung")
            return

        if path.is_dir():
            self._clear_preview("Ordner – doppelklicken, um hineinzuwechseln.")
            self.preview_title.setText(path.name or str(path))
            self.preview_details.setText(f"Pfad: {path}")
            return

        data = build_preview(path)
        self.preview_title.setText(data.title)
        self.preview_details.setText(data.details)
        state = self.database.virtual_item(path)
        self.mark_button.setText("Markierung entfernen" if state.marked else "Markieren")

        if data.image is not None:
            pixmap = QPixmap.fromImage(data.image)
            target = self.preview_image.size()
            if target.width() > 40 and target.height() > 40:
                pixmap = pixmap.scaled(
                    target,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            self.preview_image.setPixmap(pixmap)
            self.preview_image.setText("")
            self.preview_image.setVisible(True)
            self.preview_text.setVisible(False)
        else:
            self.preview_image.clear()
            self.preview_image.setVisible(False)
            self.preview_text.setPlainText(data.text or "Keine Vorschau verfügbar.")
            self.preview_text.setVisible(True)

    def _clear_preview(self, message: str) -> None:
        self._current_path = None
        self.preview_title.setText("Keine Datei ausgewählt")
        self.preview_image.clear()
        self.preview_image.setText(message)
        self.preview_image.setVisible(True)
        self.preview_text.clear()
        self.preview_text.setVisible(False)
        self.preview_details.setText("Metadaten erscheinen hier.")
        self.open_button.setEnabled(False)
        self.show_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.mark_button.setEnabled(False)
        self.collection_button.setEnabled(False)
        self.mark_button.setText("Markieren")

    def open_current(self) -> None:
        if self._current_path and self._current_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._current_path)))

    def show_current_folder(self) -> None:
        if not self._current_path:
            return
        folder = self._current_path if self._current_path.is_dir() else self._current_path.parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def copy_current_path(self) -> None:
        if self._current_path:
            QGuiApplication.clipboard().setText(str(self._current_path))


    def toggle_mark(self) -> None:
        if not self._current_path or self._current_path.is_dir() or self._current_path.is_symlink():
            return
        state = self.database.virtual_item(self._current_path)
        self.database.set_virtual_item(self._current_path, not state.marked, state.note)
        self.mark_button.setText("Markierung entfernen" if not state.marked else "Markieren")

    def add_to_collection(self) -> None:
        if not self._current_path or self._current_path.is_dir() or self._current_path.is_symlink():
            return
        collections = self.database.collections()
        if not collections:
            QMessageBox.information(
                self,
                "Keine Sammlung vorhanden",
                "Lege zuerst im Bereich „Sammlungen“ eine virtuelle Sammlung an.",
            )
            return
        names = [item.name for item in collections]
        name, ok = QInputDialog.getItem(
            self,
            "Zu Sammlung hinzufügen",
            "Sammlung:",
            names,
            0,
            False,
        )
        if not ok:
            return
        selected = next((item for item in collections if item.name == name), None)
        if selected is None:
            return
        self.database.add_collection_item(selected.id, self._current_path)
        QMessageBox.information(
            self,
            "Virtuell hinzugefügt",
            f"Die Datei wurde der Sammlung „{selected.name}“ zugeordnet.\nDie Originaldatei blieb unverändert.",
        )
