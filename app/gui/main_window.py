from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.gui.workers import DuplicateWorker, SearchWorker
from app.models.entities import DuplicateGroup, SearchHit, SearchJob
from app.safety.policy import WRITE_FEATURES
from app.storage.database import Database
from app.validation import validate_scan_root, validate_search_request


class MainWindow(QMainWindow):
    PAGE_DASHBOARD = 0
    PAGE_SEARCH = 1
    PAGE_RESULTS = 2
    PAGE_DUPLICATES = 3
    PAGE_COLLECTIONS = 4
    PAGE_JOURNAL = 5
    PAGE_HELP = 6

    def __init__(self, base_dir: Path, database: Database) -> None:
        super().__init__()
        self.base_dir = base_dir
        self.database = database
        self.selected_root: Path | None = None
        self.search_worker: SearchWorker | None = None
        self.duplicate_worker: DuplicateWorker | None = None
        self.last_hits: list[SearchHit] = []
        self.duplicate_groups_cache: list[DuplicateGroup] = []

        self.setWindowTitle("PROVOWARE DUPLIKATE-FINDER 2026 – Nur-Lesen-Modus")
        self.resize(1280, 800)
        self.setMinimumSize(760, 520)
        self._build_ui()
        self._refresh_collections()
        self._refresh_duplicate_view_from_database()

    def _heading(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setProperty("heading", True)
        font = label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 3)
        label.setFont(font)
        label.setWordWrap(True)
        return label

    def _card(self, title: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setProperty("card", True)
        layout = QVBoxLayout(frame)
        a = QLabel(title)
        a.setStyleSheet("font-weight: 700;")
        b = QLabel(value)
        font = b.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        b.setFont(font)
        layout.addWidget(a)
        layout.addWidget(b)
        return frame

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 10)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = self._heading("PROVOWARE DUPLIKATE-FINDER 2026")
        title.setObjectName("app_title")
        title.setWordWrap(True)
        mode = QLabel("🔒 NUR LESEN · ORIGINALDATEIEN GESCHÜTZT")
        mode.setObjectName("safety_banner")
        mode.setWordWrap(True)
        mode.setStyleSheet("font-weight: 800; padding: 8px; border: 2px solid #555;")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(mode)
        root.addLayout(header)

        body = QHBoxLayout()
        self.nav = QListWidget()
        self.nav.setObjectName("main_navigation")
        self.nav.addItems([
            "🏠 Übersicht",
            "🔎 Textsuche",
            "📄 Ergebnisse",
            "🟰 Duplikate",
            "📁 Sammlungen",
            "🧾 Journal",
            "❔ Hilfe",
        ])
        self.nav.setCurrentRow(self.PAGE_DASHBOARD)
        self.nav.setSelectionMode(QAbstractItemView.SingleSelection)
        body.addWidget(self.nav, 0)

        self.pages = QStackedWidget()
        self.pages.setObjectName("page_stack")
        self.pages.addWidget(self._dashboard_page())
        self.pages.addWidget(self._search_page())
        self.pages.addWidget(self._results_page())
        self.pages.addWidget(self._duplicates_page())
        self.pages.addWidget(self._collections_page())
        self.pages.addWidget(self._journal_page())
        self.pages.addWidget(self._help_page())
        body.addWidget(self.pages, 1)
        root.addLayout(body, 1)

        footer = QHBoxLayout()
        self.status_label = QLabel("🟢 Bereit")
        self.status_label.setObjectName("status_label")
        self.status_label.setStyleSheet("font-weight: 800;")
        self.counter_label = QLabel("0 Dateien geprüft · 0 Treffer")
        self.counter_label.setObjectName("counter_label")
        footer.addWidget(self.status_label)
        footer.addStretch(1)
        footer.addWidget(self.counter_label)
        root.addLayout(footer)

        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.setCentralWidget(central)

    def _dashboard_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_dashboard")
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        layout.addWidget(self._heading("Übersicht"))

        cards = QGridLayout()
        cards.addWidget(self._card("Sicherheitsmodus", "🔒 Nur lesen"), 0, 0)
        cards.addWidget(self._card("Textsuche", "🟢 Bereit"), 0, 1)
        cards.addWidget(self._card("Duplikatprüfung", "🟢 SHA-256"), 1, 0)
        cards.addWidget(self._card("Datenbank", "🟢 Lokal · SQLite"), 1, 1)
        layout.addLayout(cards)

        feature_box = QFrame()
        feature_box.setObjectName("locked_write_features")
        feature_box.setProperty("card", True)
        feature_layout = QGridLayout(feature_box)
        label = QLabel("Vorbereitete Dateiaktionen – sichtbar, aber technisch gesperrt")
        label.setWordWrap(True)
        label.setStyleSheet("font-weight: 800;")
        feature_layout.addWidget(label, 0, 0, 1, 2)

        flags = {row["key"]: row for row in self.database.feature_flags()}
        for index, (key, text) in enumerate(WRITE_FEATURES.items(), start=1):
            checkbox = QCheckBox(text)
            checkbox.setObjectName(f"feature_{key}")
            checkbox.setChecked(bool(flags[key]["enabled"]))
            checkbox.setEnabled(False)
            checkbox.setToolTip("Vorbereitet, aber in Version 1 absichtlich gesperrt.")
            state = QLabel("🔒 AUS · gesperrt")
            feature_layout.addWidget(checkbox, index, 0)
            feature_layout.addWidget(state, index, 1)
        layout.addWidget(feature_box)

        quick = QGridLayout()
        go_search = QPushButton("🔎 Text suchen")
        go_search.setObjectName("dashboard_go_search")
        go_duplicates = QPushButton("🟰 Duplikate prüfen")
        go_duplicates.setObjectName("dashboard_go_duplicates")
        go_collections = QPushButton("📁 Sammlungen")
        go_collections.setObjectName("dashboard_go_collections")
        go_search.clicked.connect(lambda: self.nav.setCurrentRow(self.PAGE_SEARCH))
        go_duplicates.clicked.connect(lambda: self.nav.setCurrentRow(self.PAGE_DUPLICATES))
        go_collections.clicked.connect(lambda: self.nav.setCurrentRow(self.PAGE_COLLECTIONS))
        quick.addWidget(go_search, 0, 0)
        quick.addWidget(go_duplicates, 0, 1)
        quick.addWidget(go_collections, 1, 0, 1, 2)
        layout.addLayout(quick)
        layout.addStretch(1)
        return page

    def _root_selector(self) -> tuple[QHBoxLayout, QLineEdit, QPushButton]:
        row = QHBoxLayout()
        label = QLineEdit()
        label.setReadOnly(True)
        label.setPlaceholderText("Noch kein Ordner gewählt")
        choose = QPushButton("📁 Ordner wählen")
        choose.clicked.connect(self._choose_root)
        row.addWidget(label, 1)
        row.addWidget(choose)
        return row, label, choose

    def _search_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_search")
        layout = QVBoxLayout(page)
        layout.addWidget(self._heading("Textdateien durchsuchen"))

        root_row, self.root_label, choose = self._root_selector()
        self.root_label.setObjectName("search_root")
        choose.setObjectName("search_choose_root")
        layout.addLayout(root_row)

        query_grid = QGridLayout()
        self.query_edit = QLineEdit()
        self.query_edit.setObjectName("search_query")
        self.query_edit.setPlaceholderText("Suchbegriff")
        self.names_box = QCheckBox("Dateinamen")
        self.names_box.setObjectName("search_names")
        self.names_box.setChecked(True)
        self.contents_box = QCheckBox("Dateiinhalte")
        self.contents_box.setObjectName("search_contents")
        self.contents_box.setChecked(True)
        self.search_button = QPushButton("🔎 SUCHEN")
        self.search_button.setObjectName("search_start")
        self.search_button.clicked.connect(self._start_search)
        query_grid.addWidget(self.query_edit, 0, 0, 1, 3)
        query_grid.addWidget(self.names_box, 1, 0)
        query_grid.addWidget(self.contents_box, 1, 1)
        query_grid.addWidget(self.search_button, 1, 2)
        layout.addLayout(query_grid)

        info = QLabel(
            "ℹ️ Die Textsuche liest nur unterstützte Textformate. Symbolische Verknüpfungen "
            "und kritische Linux-Systembereiche werden nicht verfolgt."
        )
        info.setObjectName("search_info")
        info.setWordWrap(True)
        info.setProperty("card", True)
        layout.addWidget(info)
        layout.addStretch(1)
        return page

    def _results_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_results")
        layout = QVBoxLayout(page)

        head = QHBoxLayout()
        head.addWidget(self._heading("Ergebnisse"))
        self.result_info = QLabel("Noch keine Suche ausgeführt")
        self.result_info.setObjectName("result_info")
        head.addStretch(1)
        head.addWidget(self.result_info)
        layout.addLayout(head)

        self.results = QTableWidget(0, 5)
        self.results.setObjectName("results_table")
        self.results.setHorizontalHeaderLabels(["Markiert", "Quelle", "Datei", "Zeile", "Fundstelle"])
        self.results.horizontalHeader().setStretchLastSection(True)
        self.results.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results.itemSelectionChanged.connect(self._load_selected_result_state)
        layout.addWidget(self.results, 1)

        meta = QGridLayout()
        self.result_mark = QCheckBox("Treffer markieren")
        self.result_mark.setObjectName("result_mark")
        self.result_note = QLineEdit()
        self.result_note.setObjectName("result_note")
        self.result_note.setPlaceholderText("Notiz zum ausgewählten Treffer")
        save_meta = QPushButton("💾 Markierung + Notiz speichern")
        save_meta.setObjectName("result_save_meta")
        save_meta.clicked.connect(self._save_selected_result_state)
        self.result_collection = QComboBox()
        self.result_collection.setObjectName("result_collection")
        add_collection = QPushButton("➕ In Sammlung aufnehmen")
        add_collection.setObjectName("result_add_collection")
        add_collection.clicked.connect(self._add_selected_result_to_collection)
        meta.addWidget(self.result_mark, 0, 0)
        meta.addWidget(self.result_note, 0, 1, 1, 2)
        meta.addWidget(save_meta, 1, 0, 1, 3)
        meta.addWidget(QLabel("Sammlung:"), 2, 0)
        meta.addWidget(self.result_collection, 2, 1)
        meta.addWidget(add_collection, 2, 2)
        layout.addLayout(meta)
        return page

    def _duplicates_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_duplicates")
        layout = QVBoxLayout(page)

        top = QVBoxLayout()
        top.addWidget(self._heading("Duplikate – gruppiert und vollständig geprüft"))
        self.duplicate_start = QPushButton("🟰 Gewählten Ordner prüfen")
        self.duplicate_start.setObjectName("duplicate_start")
        self.duplicate_start.clicked.connect(self._start_duplicate_scan)
        top.addWidget(self.duplicate_start)
        layout.addLayout(top)

        self.duplicate_root = QLabel("Suchordner: noch nicht gewählt")
        self.duplicate_root.setObjectName("duplicate_root")
        self.duplicate_root.setWordWrap(True)
        layout.addWidget(self.duplicate_root)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("duplicate_splitter")
        self.duplicate_group_list = QListWidget()
        self.duplicate_group_list.setObjectName("duplicate_group_list")
        self.duplicate_group_list.currentRowChanged.connect(self._show_duplicate_group)
        splitter.addWidget(self.duplicate_group_list)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.duplicate_summary = QLabel("Noch keine Duplikatprüfung ausgeführt.")
        self.duplicate_summary.setObjectName("duplicate_summary")
        self.duplicate_summary.setWordWrap(True)
        right_layout.addWidget(self.duplicate_summary)
        self.duplicate_members = QTableWidget(0, 4)
        self.duplicate_members.setObjectName("duplicate_members")
        self.duplicate_members.setHorizontalHeaderLabels(["Datei", "Ordner", "Größe", "Geändert"])
        self.duplicate_members.horizontalHeader().setStretchLastSection(True)
        self.duplicate_members.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.duplicate_members.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.duplicate_members, 1)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter, 1)

        note = QLabel(
            "🔒 Diese Ansicht vergleicht nur. Es gibt hier absichtlich keinen Löschen-, "
            "Verschieben- oder Umbenennen-Knopf."
        )
        note.setObjectName("duplicate_safety_note")
        note.setWordWrap(True)
        note.setProperty("card", True)
        layout.addWidget(note)
        return page

    def _collections_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_collections")
        layout = QVBoxLayout(page)
        layout.addWidget(self._heading("Virtuelle Sammlungen"))

        create = QGridLayout()
        self.collection_name = QLineEdit()
        self.collection_name.setObjectName("collection_name")
        self.collection_name.setPlaceholderText("Name der neuen Sammlung")
        self.collection_note = QLineEdit()
        self.collection_note.setObjectName("collection_note")
        self.collection_note.setPlaceholderText("Optionale Beschreibung")
        create_button = QPushButton("➕ Sammlung anlegen")
        create_button.setObjectName("collection_create")
        create_button.clicked.connect(self._create_collection)
        create.addWidget(self.collection_name, 0, 0)
        create.addWidget(self.collection_note, 0, 1)
        create.addWidget(create_button, 1, 0, 1, 2)
        layout.addLayout(create)

        splitter = QSplitter(Qt.Horizontal)
        self.collection_list = QListWidget()
        self.collection_list.setObjectName("collection_list")
        self.collection_list.currentRowChanged.connect(self._show_collection)
        splitter.addWidget(self.collection_list)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.collection_summary = QLabel("Noch keine Sammlung ausgewählt.")
        self.collection_summary.setObjectName("collection_summary")
        self.collection_summary.setWordWrap(True)
        right_layout.addWidget(self.collection_summary)
        self.collection_items_table = QTableWidget(0, 3)
        self.collection_items_table.setObjectName("collection_items")
        self.collection_items_table.setHorizontalHeaderLabels(["Datei", "Ordner", "Notiz"])
        self.collection_items_table.horizontalHeader().setStretchLastSection(True)
        self.collection_items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.collection_items_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.collection_items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.collection_items_table, 1)
        remove = QPushButton("➖ Nur aus Sammlung entfernen")
        remove.setObjectName("collection_remove")
        remove.clicked.connect(self._remove_selected_collection_item)
        right_layout.addWidget(remove)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter, 1)

        safe = QLabel("ℹ️ Sammlungen sind rein virtuell. Die Dateien bleiben an ihrem Originalort.")
        safe.setObjectName("collection_safety_note")
        safe.setWordWrap(True)
        safe.setProperty("card", True)
        layout.addWidget(safe)
        return page

    def _journal_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_journal")
        layout = QVBoxLayout(page)
        layout.addWidget(self._heading("Änderungsjournal"))
        info = QLabel(
            "🟢 Version 1 führt keine physischen Dateiänderungen aus. Das Journal-Schema ist "
            "vorbereitet, bleibt für Originaldateien aber leer. Virtuelle Sammlungen und Notizen "
            "liegen getrennt in der lokalen Datenbank."
        )
        info.setObjectName("journal_info")
        info.setWordWrap(True)
        info.setProperty("card", True)
        layout.addWidget(info)
        layout.addStretch(1)
        return page

    def _help_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_help")
        layout = QVBoxLayout(page)
        layout.addWidget(self._heading("Hilfe – drei einfache Schritte"))
        for text in (
            "1. 📁 Ordner wählen – das Programm durchsucht nur diesen Bereich.",
            "2. 🔎 Text suchen oder 🟰 Duplikate prüfen.",
            "3. 📁 Treffer markieren, kommentieren und in virtuellen Sammlungen ordnen.",
        ):
            label = QLabel(text)
            label.setWordWrap(True)
            label.setProperty("card", True)
            layout.addWidget(label)
        safety = QLabel(
            "🔒 Originaldateien werden in Version 1 niemals gelöscht, verschoben, umbenannt oder überschrieben."
        )
        safety.setObjectName("help_safety")
        safety.setWordWrap(True)
        safety.setStyleSheet("font-weight: 800;")
        layout.addWidget(safety)
        layout.addStretch(1)
        return page

    def _choose_root(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Suchordner wählen", str(Path.home()))
        if not chosen:
            return
        validation = validate_scan_root(Path(chosen))
        if not validation.ok:
            QMessageBox.information(self, validation.title, validation.message)
            return
        self.selected_root = Path(chosen)
        self.root_label.setText(chosen)
        self.duplicate_root.setText(f"Suchordner: {chosen}")

    def _start_search(self) -> None:
        query = self.query_edit.text().strip()
        validation = validate_search_request(
            self.selected_root,
            query,
            self.names_box.isChecked(),
            self.contents_box.isChecked(),
        )
        if not validation.ok:
            QMessageBox.information(self, validation.title, validation.message)
            return

        job = SearchJob(
            root=self.selected_root,
            query=query,
            search_names=self.names_box.isChecked(),
            search_contents=self.contents_box.isChecked(),
        )
        self.search_button.setEnabled(False)
        self.status_label.setText("🟡 Textsuche läuft …")
        self.counter_label.setText("Suche wird vorbereitet …")
        self.search_worker = SearchWorker(job)
        self.search_worker.completed.connect(self._search_finished)
        self.search_worker.failed.connect(self._search_failed)
        self.search_worker.start()

    def _search_finished(self, job: SearchJob, hits: list[SearchHit]) -> None:
        self.last_hits = list(hits)
        sorting = self.results.isSortingEnabled()
        self.results.setSortingEnabled(False)
        self.results.setRowCount(0)
        for hit in hits:
            row = self.results.rowCount()
            self.results.insertRow(row)
            state = self.database.virtual_item(hit.path)
            mark_item = QTableWidgetItem("★" if state.marked else "")
            mark_item.setData(Qt.UserRole, str(hit.path))
            self.results.setItem(row, 0, mark_item)
            self.results.setItem(row, 1, QTableWidgetItem(hit.source))
            self.results.setItem(row, 2, QTableWidgetItem(str(hit.path)))
            self.results.setItem(row, 3, QTableWidgetItem("" if hit.line_number is None else str(hit.line_number)))
            self.results.setItem(row, 4, QTableWidgetItem(hit.excerpt))
        self.results.setSortingEnabled(sorting)
        self.search_button.setEnabled(True)
        self.status_label.setText("🟢 Textsuche abgeschlossen")
        self.counter_label.setText(f"{job.scanned_files} Textdateien geprüft · {len(hits)} Treffer")
        self.result_info.setText(f"{len(hits)} Treffer")
        self.nav.setCurrentRow(self.PAGE_RESULTS)

    def _search_failed(self, message: str) -> None:
        self.search_button.setEnabled(True)
        self.status_label.setText("🔴 Textsuche gestoppt")
        QMessageBox.critical(self, "Suche gestoppt", f"Die Suche wurde sicher beendet.\n\n{message}")

    def _selected_result_path(self) -> Path | None:
        row = self.results.currentRow()
        if row < 0:
            return None
        item = self.results.item(row, 2)
        return Path(item.text()) if item else None

    def _load_selected_result_state(self) -> None:
        path = self._selected_result_path()
        if path is None:
            return
        state = self.database.virtual_item(path)
        self.result_mark.setChecked(state.marked)
        self.result_note.setText(state.note)

    def _save_selected_result_state(self) -> None:
        path = self._selected_result_path()
        if path is None:
            QMessageBox.information(self, "Kein Treffer", "Bitte zuerst einen Treffer auswählen.")
            return
        self.database.set_virtual_item(path, self.result_mark.isChecked(), self.result_note.text())
        row = self.results.currentRow()
        self.results.item(row, 0).setText("★" if self.result_mark.isChecked() else "")
        self.status_label.setText("🟢 Virtuelle Markierung gespeichert")

    def _add_selected_result_to_collection(self) -> None:
        path = self._selected_result_path()
        collection_id = self.result_collection.currentData()
        if path is None:
            QMessageBox.information(self, "Kein Treffer", "Bitte zuerst einen Treffer auswählen.")
            return
        if collection_id is None:
            QMessageBox.information(self, "Keine Sammlung", "Bitte zuerst eine Sammlung anlegen.")
            return
        self.database.add_collection_item(int(collection_id), path, self.result_note.text())
        self._show_collection(self.collection_list.currentRow())
        self.status_label.setText("🟢 Treffer virtuell zur Sammlung hinzugefügt")

    def _start_duplicate_scan(self) -> None:
        validation = validate_scan_root(self.selected_root)
        if not validation.ok:
            QMessageBox.information(self, validation.title, validation.message)
            return
        self.duplicate_start.setEnabled(False)
        self.status_label.setText("🟡 Duplikatprüfung läuft …")
        self.duplicate_summary.setText("Dateigrößen werden gruppiert; nur Kandidaten werden vollständig gehasht.")
        self.duplicate_worker = DuplicateWorker(self.selected_root)
        self.duplicate_worker.completed.connect(self._duplicate_scan_finished)
        self.duplicate_worker.failed.connect(self._duplicate_scan_failed)
        self.duplicate_worker.start()

    def _duplicate_scan_finished(self, scanned: int, groups: list[DuplicateGroup]) -> None:
        self.database.replace_duplicate_groups(groups)
        self.duplicate_groups_cache = list(groups)
        self._fill_duplicate_groups()
        self.duplicate_start.setEnabled(True)
        duplicates = sum(len(group.paths) for group in groups)
        self.status_label.setText("🟢 Duplikatprüfung abgeschlossen")
        self.counter_label.setText(f"{scanned} Dateien geprüft · {len(groups)} Gruppen · {duplicates} Dateien")
        self.duplicate_summary.setText(
            f"{len(groups)} sichere Duplikatgruppen gefunden. Jede Gruppe besitzt identische Größe und SHA-256-Prüfsumme."
        )

    def _duplicate_scan_failed(self, message: str) -> None:
        self.duplicate_start.setEnabled(True)
        self.status_label.setText("🔴 Duplikatprüfung gestoppt")
        QMessageBox.critical(
            self,
            "Duplikatprüfung gestoppt",
            f"Die Prüfung wurde sicher beendet.\n\n{message}",
        )

    def _refresh_duplicate_view_from_database(self) -> None:
        self.duplicate_groups_cache = [group for _, group in self.database.duplicate_groups()]
        self._fill_duplicate_groups()

    def _fill_duplicate_groups(self) -> None:
        self.duplicate_group_list.clear()
        for index, group in enumerate(self.duplicate_groups_cache, start=1):
            wasted = group.size * (len(group.paths) - 1)
            text = f"Gruppe {index} · {len(group.paths)} Dateien · {self._human_size(wasted)} mehrfach"
            self.duplicate_group_list.addItem(text)
        if self.duplicate_groups_cache:
            self.duplicate_group_list.setCurrentRow(0)
        else:
            self.duplicate_members.setRowCount(0)

    def _show_duplicate_group(self, row: int) -> None:
        if row < 0 or row >= len(self.duplicate_groups_cache):
            return
        group = self.duplicate_groups_cache[row]
        sorting = self.duplicate_members.isSortingEnabled()
        self.duplicate_members.setSortingEnabled(False)
        self.duplicate_members.setRowCount(0)
        for path in group.paths:
            table_row = self.duplicate_members.rowCount()
            self.duplicate_members.insertRow(table_row)
            try:
                stat = path.stat()
                modified = str(int(stat.st_mtime))
            except OSError:
                modified = "nicht verfügbar"
            self.duplicate_members.setItem(table_row, 0, QTableWidgetItem(path.name))
            self.duplicate_members.setItem(table_row, 1, QTableWidgetItem(str(path.parent)))
            self.duplicate_members.setItem(table_row, 2, QTableWidgetItem(self._human_size(group.size)))
            self.duplicate_members.setItem(table_row, 3, QTableWidgetItem(modified))
        self.duplicate_members.setSortingEnabled(sorting)
        self.duplicate_summary.setText(
            f"Gruppe {row + 1}: {len(group.paths)} vollständig identische Dateien · "
            f"je {self._human_size(group.size)} · SHA-256 {group.sha256[:16]}…"
        )

    def _create_collection(self) -> None:
        name = self.collection_name.text().strip()
        note = self.collection_note.text().strip()
        try:
            collection_id = self.database.create_collection(name, note)
        except ValueError as exc:
            QMessageBox.information(self, "Name fehlt", str(exc))
            return
        except Exception as exc:
            QMessageBox.information(self, "Sammlung nicht angelegt", f"{exc}")
            return
        self.collection_name.clear()
        self.collection_note.clear()
        self._refresh_collections(select_id=collection_id)
        self.status_label.setText("🟢 Virtuelle Sammlung angelegt")

    def _refresh_collections(self, select_id: int | None = None) -> None:
        collections = self.database.collections()
        self.collection_list.clear()
        self.result_collection.clear()
        target_row = -1
        for row, collection in enumerate(collections):
            item = QListWidgetItem(collection.name)
            item.setData(Qt.UserRole, collection.id)
            item.setToolTip(collection.note)
            self.collection_list.addItem(item)
            self.result_collection.addItem(collection.name, collection.id)
            if collection.id == select_id:
                target_row = row
        if collections:
            self.collection_list.setCurrentRow(target_row if target_row >= 0 else 0)
        else:
            self.collection_summary.setText("Noch keine Sammlung angelegt.")
            self.collection_items_table.setRowCount(0)

    def _current_collection_id(self) -> int | None:
        item = self.collection_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        return int(value) if value is not None else None

    def _show_collection(self, _row: int) -> None:
        collection_id = self._current_collection_id()
        if collection_id is None:
            return
        collection = next((c for c in self.database.collections() if c.id == collection_id), None)
        if collection is None:
            return
        items = self.database.collection_items(collection_id)
        suffix = f" · {collection.note}" if collection.note else ""
        self.collection_summary.setText(f"{collection.name} · {len(items)} Einträge{suffix}")
        sorting = self.collection_items_table.isSortingEnabled()
        self.collection_items_table.setSortingEnabled(False)
        self.collection_items_table.setRowCount(0)
        for entry in items:
            row = self.collection_items_table.rowCount()
            self.collection_items_table.insertRow(row)
            path_item = QTableWidgetItem(entry.path.name)
            path_item.setData(Qt.UserRole, str(entry.path))
            self.collection_items_table.setItem(row, 0, path_item)
            self.collection_items_table.setItem(row, 1, QTableWidgetItem(str(entry.path.parent)))
            self.collection_items_table.setItem(row, 2, QTableWidgetItem(entry.note))
        self.collection_items_table.setSortingEnabled(sorting)

    def _remove_selected_collection_item(self) -> None:
        collection_id = self._current_collection_id()
        row = self.collection_items_table.currentRow()
        if collection_id is None or row < 0:
            QMessageBox.information(self, "Keine Auswahl", "Bitte einen Sammlungseintrag auswählen.")
            return
        item = self.collection_items_table.item(row, 0)
        raw_path = item.data(Qt.UserRole) if item else None
        if not raw_path:
            return
        self.database.remove_collection_item(collection_id, Path(str(raw_path)))
        self._show_collection(self.collection_list.currentRow())
        self.status_label.setText("🟢 Eintrag nur aus der virtuellen Sammlung entfernt")

    @staticmethod
    def _human_size(size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024.0 or unit == "TB":
                return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
            value /= 1024.0
        return f"{size} B"
