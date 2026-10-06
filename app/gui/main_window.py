from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QCloseEvent, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
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
    QProgressBar,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.scanner import ScanOptions
from app.error_management import record_error
from app.gui.design_tokens import BASE_SPACING, OUTER_MARGIN
from app.gui.filter_dialog import ScanOptionsDialog
from app.gui.workers import DuplicateWorker, ManagedWorker, SearchWorker
from app.models.entities import DuplicateGroup, SearchHit, SearchJob
from app.safety.policy import WRITE_FEATURES
from app.settings import AppSettings, SettingsStore
from app.state_transfer import StateImportError, build_export, validate_import
from app.storage.database import Database
from app.texts import text as ui_text
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
        self.settings_store = SettingsStore(base_dir / "config" / "ui-settings.json")
        self.settings = self.settings_store.load()
        self.selected_root: Path | None = None
        self.search_worker: SearchWorker | None = None
        self.duplicate_worker: DuplicateWorker | None = None
        self.last_hits: list[SearchHit] = []
        self.duplicate_groups_cache: list[DuplicateGroup] = []
        self._last_phase = "bereit"

        self.setWindowTitle("PROVOWARE DUPLIKATE-FINDER 2026 – Nur-Lesen-Modus")
        self.resize(self.settings.window_width, self.settings.window_height)
        self.setMinimumSize(760, 520)
        self._build_ui()
        self._restore_last_root()
        self._refresh_collections()
        self._refresh_duplicate_view_from_database()
        self._update_filter_summaries()

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
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)
        a = QLabel(title)
        a.setProperty("cardTitle", True)
        b = QLabel(value)
        b.setProperty("cardValue", True)
        layout.addWidget(a)
        layout.addWidget(b)
        return frame

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(OUTER_MARGIN, OUTER_MARGIN, OUTER_MARGIN, 10)
        root.setSpacing(BASE_SPACING)

        header_frame = QFrame()
        header_frame.setProperty("headerPanel", True)
        header = QHBoxLayout(header_frame)
        title = self._heading("PROVOWARE DUPLIKATE-FINDER 2026")
        title.setObjectName("app_title")
        title.setWordWrap(True)
        mode = QLabel("🔒 NUR LESEN · ORIGINALDATEIEN GESCHÜTZT")
        mode.setObjectName("safety_banner")
        mode.setProperty("safetyBanner", True)
        mode.setWordWrap(True)
        header.addWidget(title, 1)
        header.addWidget(mode)
        root.addWidget(header_frame)

        body = QHBoxLayout()
        body.setSpacing(BASE_SPACING)
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
        self.nav.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.nav.setMaximumWidth(190)
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

        process_panel = QFrame()
        process_panel.setObjectName("process_panel")
        process_panel.setProperty("processPanel", True)
        process = QGridLayout(process_panel)
        process.setContentsMargins(8, 6, 8, 6)
        process.setHorizontalSpacing(10)
        process.setVerticalSpacing(4)

        self.status_label = QLabel("🟢 Bereit")
        self.status_label.setObjectName("status_label")
        self.activity_label = QLabel("Aktueller Schritt: bereit")
        self.activity_label.setObjectName("activity_label")
        self.activity_label.setToolTip("Zeigt den aktuell ausgeführten Arbeitsschritt.")
        self.eta_label = QLabel("Restzeit: –")
        self.eta_label.setObjectName("activity_eta")
        self.eta_label.setToolTip("Ungefähre Restzeit aus dem bisherigen Durchsatz.")

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("activity_progress")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Bereit")
        self.progress_bar.setMinimumWidth(220)

        self.pause_button = QPushButton("⏸ Pause")
        self.pause_button.setObjectName("activity_pause")
        self.pause_button.setProperty("warning", True)
        self.pause_button.setEnabled(False)
        self.pause_button.setToolTip("Hält den laufenden Auftrag an einem sicheren Prüfpunkt an.")
        self.pause_button.clicked.connect(self._pause_or_resume)

        self.cancel_button = QPushButton("■ Abbrechen")
        self.cancel_button.setObjectName("activity_cancel")
        self.cancel_button.setProperty("danger", True)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setToolTip("Fordert einen sicheren Abbruch an. Originaldateien bleiben unverändert.")
        self.cancel_button.clicked.connect(self._cancel_active_process)

        self.counter_label = QLabel("0 Dateien geprüft · 0 Treffer")
        self.counter_label.setObjectName("counter_label")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        process.addWidget(self.status_label, 0, 0)
        process.addWidget(self.activity_label, 0, 1, 1, 2)
        process.addWidget(self.eta_label, 0, 3)
        process.addWidget(self.progress_bar, 1, 0, 1, 2)
        process.addWidget(self.pause_button, 1, 2)
        process.addWidget(self.cancel_button, 1, 3)
        process.addWidget(self.counter_label, 1, 4)
        process.setColumnStretch(1, 1)
        process.setColumnStretch(4, 1)
        root.addWidget(process_panel)

        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.setCentralWidget(central)

    def _dashboard_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_dashboard")
        page.setProperty("pagePanel", True)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(self._heading("Übersicht"))

        cards = QGridLayout()
        cards.setSpacing(8)
        cards.addWidget(self._card("Sicherheitsmodus", "🔒 Nur lesen"), 0, 0)
        cards.addWidget(self._card("Textsuche", "🟢 Bereit"), 0, 1)
        cards.addWidget(self._card("Duplikatprüfung", "🟢 SHA-256"), 1, 0)
        cards.addWidget(self._card("Datenbank", "🟢 Lokal · SQLite"), 1, 1)
        layout.addLayout(cards)

        feature_box = QFrame()
        feature_box.setObjectName("locked_write_features")
        feature_box.setProperty("lockedPanel", True)
        feature_layout = QGridLayout(feature_box)
        label = QLabel("Vorbereitete Dateiaktionen – sichtbar, aber technisch gesperrt")
        label.setWordWrap(True)
        label.setProperty("sectionTitle", True)
        feature_layout.addWidget(label, 0, 0, 1, 4)

        flags = {row["key"]: row for row in self.database.feature_flags()}
        for index, (key, text) in enumerate(WRITE_FEATURES.items()):
            checkbox = QCheckBox(text)
            checkbox.setObjectName(f"feature_{key}")
            checkbox.setChecked(bool(flags[key]["enabled"]))
            checkbox.setEnabled(False)
            checkbox.setToolTip("Vorbereitet, aber absichtlich gesperrt.")
            state = QLabel("🔒 AUS")
            state.setToolTip("Technisch gesperrt. Originaldateien bleiben unverändert.")
            row = 1 + index // 2
            column = (index % 2) * 2
            feature_layout.addWidget(checkbox, row, column)
            feature_layout.addWidget(state, row, column + 1)
        layout.addWidget(feature_box)

        quick = QGridLayout()
        quick.setSpacing(8)
        go_search = QPushButton("🔎 Text suchen")
        go_search.setObjectName("dashboard_go_search")
        go_search.setProperty("accent", True)
        go_duplicates = QPushButton("🟰 Duplikate prüfen")
        go_duplicates.setObjectName("dashboard_go_duplicates")
        go_duplicates.setProperty("accent", True)
        go_collections = QPushButton("📁 Sammlungen")
        go_collections.setObjectName("dashboard_go_collections")
        go_search.clicked.connect(lambda: self.nav.setCurrentRow(self.PAGE_SEARCH))
        go_duplicates.clicked.connect(lambda: self.nav.setCurrentRow(self.PAGE_DUPLICATES))
        go_collections.clicked.connect(lambda: self.nav.setCurrentRow(self.PAGE_COLLECTIONS))
        quick.addWidget(go_search, 0, 0)
        quick.addWidget(go_duplicates, 0, 1)
        quick.addWidget(go_collections, 0, 2)
        layout.addLayout(quick)
        layout.addStretch(1)
        return page

    def _root_selector(self) -> tuple[QHBoxLayout, QLineEdit, QPushButton]:
        row = QHBoxLayout()
        label = QLineEdit()
        label.setReadOnly(True)
        label.setPlaceholderText("Noch kein Ordner gewählt")
        choose = QPushButton("📁 Ordner wählen")
        choose.setProperty("accent", True)
        choose.clicked.connect(self._choose_root)
        row.addWidget(label, 1)
        row.addWidget(choose)
        return row, label, choose

    def _search_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_search")
        page.setProperty("pagePanel", True)
        layout = QVBoxLayout(page)
        layout.setSpacing(8)
        layout.addWidget(self._heading("Textdateien durchsuchen"))

        root_row, self.root_label, choose = self._root_selector()
        self.root_label.setObjectName("search_root")
        choose.setObjectName("search_choose_root")
        layout.addLayout(root_row)

        filter_panel = QFrame()
        filter_panel.setProperty("section", True)
        filter_layout = QHBoxLayout(filter_panel)
        self.search_filter_summary = QLabel()
        self.search_filter_summary.setObjectName("search_filter_summary")
        self.search_filter_summary.setWordWrap(True)
        filter_button = QPushButton("⚙ Prüfoptionen")
        filter_button.setObjectName("search_filter_options")
        filter_button.clicked.connect(self._open_scan_options)
        filter_layout.addWidget(self.search_filter_summary, 1)
        filter_layout.addWidget(filter_button)
        layout.addWidget(filter_panel)

        query_panel = QFrame()
        query_panel.setProperty("section", True)
        query_grid = QGridLayout(query_panel)
        self.query_edit = QLineEdit()
        self.query_edit.setObjectName("search_query")
        self.query_edit.setPlaceholderText("Suchbegriff")
        self.query_edit.setToolTip("Gib das Wort oder den Text ein, den du finden möchtest.")
        self.names_box = QCheckBox("Dateinamen")
        self.names_box.setObjectName("search_names")
        self.names_box.setChecked(True)
        self.contents_box = QCheckBox("Dateiinhalte")
        self.contents_box.setObjectName("search_contents")
        self.contents_box.setChecked(True)
        self.search_button = QPushButton("🔎 SUCHEN")
        self.search_button.setObjectName("search_start")
        self.search_button.setProperty("accent", True)
        self.search_button.clicked.connect(self._start_search)
        self.search_button.setToolTip("Startet eine reine Lese-Suche. Originaldateien werden nicht verändert.")
        query_grid.addWidget(self.query_edit, 0, 0, 1, 3)
        query_grid.addWidget(self.names_box, 1, 0)
        query_grid.addWidget(self.contents_box, 1, 1)
        query_grid.addWidget(self.search_button, 1, 2)
        layout.addWidget(query_panel)

        info = QLabel(
            "ℹ️ Textsuche liest nur unterstützte Textformate. Technische Projektordner können "
            "automatisch ausgelassen werden. Symbolische Verknüpfungen und kritische Linux-Systembereiche "
            "werden nicht verfolgt."
        )
        info.setObjectName("search_info")
        info.setWordWrap(True)
        info.setProperty("infoPanel", True)
        layout.addWidget(info)
        layout.addStretch(1)
        return page

    def _results_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_results")
        page.setProperty("pagePanel", True)
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
        self.results.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results.itemSelectionChanged.connect(self._load_selected_result_state)
        layout.addWidget(self.results, 1)

        meta_panel = QFrame()
        meta_panel.setProperty("section", True)
        meta = QGridLayout(meta_panel)
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
        copy_path = QPushButton("📋 Pfad kopieren")
        copy_path.setObjectName("result_copy_path")
        copy_path.clicked.connect(self._copy_selected_result_path)
        open_folder = QPushButton("📂 Ordner öffnen")
        open_folder.setObjectName("result_open_folder")
        open_folder.clicked.connect(self._open_selected_result_folder)
        meta.addWidget(self.result_mark, 0, 0)
        meta.addWidget(self.result_note, 0, 1, 1, 3)
        meta.addWidget(save_meta, 1, 0, 1, 2)
        meta.addWidget(copy_path, 1, 2)
        meta.addWidget(open_folder, 1, 3)
        meta.addWidget(QLabel("Sammlung:"), 2, 0)
        meta.addWidget(self.result_collection, 2, 1, 1, 2)
        meta.addWidget(add_collection, 2, 3)
        layout.addWidget(meta_panel)
        return page

    def _duplicates_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_duplicates")
        page.setProperty("pagePanel", True)
        layout = QVBoxLayout(page)

        top_panel = QFrame()
        top_panel.setProperty("section", True)
        top = QGridLayout(top_panel)
        top.addWidget(self._heading("Duplikate – gruppiert und vollständig geprüft"), 0, 0, 1, 2)
        self.duplicate_filter_summary = QLabel()
        self.duplicate_filter_summary.setObjectName("duplicate_filter_summary")
        self.duplicate_filter_summary.setWordWrap(True)
        options = QPushButton("⚙ Prüfoptionen")
        options.setObjectName("duplicate_filter_options")
        options.clicked.connect(self._open_scan_options)
        self.duplicate_start = QPushButton("🟰 Gewählten Ordner prüfen")
        self.duplicate_start.setObjectName("duplicate_start")
        self.duplicate_start.setProperty("accent", True)
        self.duplicate_start.clicked.connect(self._start_duplicate_scan)
        top.addWidget(self.duplicate_filter_summary, 1, 0)
        top.addWidget(options, 1, 1)
        top.addWidget(self.duplicate_start, 2, 0, 1, 2)
        layout.addWidget(top_panel)

        self.duplicate_root = QLabel("Suchordner: noch nicht gewählt")
        self.duplicate_root.setObjectName("duplicate_root")
        self.duplicate_root.setWordWrap(True)
        self.duplicate_root.setProperty("infoPanel", True)
        layout.addWidget(self.duplicate_root)

        splitter = QSplitter(Qt.Orientation.Horizontal)
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
        self.duplicate_members.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.duplicate_members.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
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
        note.setProperty("infoPanel", True)
        layout.addWidget(note)
        return page

    def _collections_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_collections")
        page.setProperty("pagePanel", True)
        layout = QVBoxLayout(page)
        layout.addWidget(self._heading("Virtuelle Sammlungen"))

        create_panel = QFrame()
        create_panel.setProperty("section", True)
        create = QGridLayout(create_panel)
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
        layout.addWidget(create_panel)

        splitter = QSplitter(Qt.Orientation.Horizontal)
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
        self.collection_items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.collection_items_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.collection_items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
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
        safe.setProperty("infoPanel", True)
        layout.addWidget(safe)
        return page

    def _journal_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_journal")
        page.setProperty("pagePanel", True)
        layout = QVBoxLayout(page)
        layout.addWidget(self._heading("Änderungsjournal"))
        info = QLabel(
            "🟢 Originaldateien werden nicht verändert. Markierungen, Notizen, Sammlungen, "
            "Einstellungen und Autospeicherstände liegen getrennt im PROVOWARE-Projektordner."
        )
        info.setObjectName("journal_info")
        info.setWordWrap(True)
        info.setProperty("infoPanel", True)
        layout.addWidget(info)
        layout.addStretch(1)
        return page

    def _help_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_help")
        page.setProperty("pagePanel", True)
        layout = QVBoxLayout(page)
        layout.addWidget(self._heading("Hilfe – drei Stufen"))

        for text in (
            "1. Kurz erklärt: Ordner wählen → Prüfoptionen kontrollieren → Suche oder Duplikatprüfung starten.",
            "2. Direkt am Bedienelement: Maus über Knopf oder Feld bewegen. Der Tooltip erklärt Funktion und Folgen.",
            "3. Prozesssteuerung: Laufende Prüfungen können sicher pausiert, fortgesetzt und abgebrochen werden. "
            "Die Restzeit ist eine Schätzung aus dem bisherigen Durchsatz.",
        ):
            label = QLabel(text)
            label.setWordWrap(True)
            label.setProperty("infoPanel", True)
            layout.addWidget(label)

        level3 = QLabel(
            "Weitere Hilfe:\n"
            "• Textsuche: " + ui_text("help.search_short") + "\n"
            "• Duplikate: " + ui_text("help.duplicates_short") + "\n"
            "• Sammlungen: " + ui_text("help.collections_short") + "\n"
            "• Export/Import: überträgt nur PROVOWARE-Einstellungen und virtuelle Organisation.\n"
            "• Autospeichern: Einstellungen alle fünf Minuten; virtuelle Änderungen werden sofort gespeichert."
        )
        level3.setWordWrap(True)
        level3.setProperty("infoPanel", True)
        layout.addWidget(level3)

        safety = QLabel(
            "🔒 Originaldateien werden in diesem Sicherheitsstand niemals gelöscht, verschoben, umbenannt oder überschrieben."
        )
        safety.setObjectName("help_safety")
        safety.setWordWrap(True)
        safety.setProperty("safetyBanner", True)
        layout.addWidget(safety)
        layout.addStretch(1)
        return page

    def _restore_last_root(self) -> None:
        raw = self.settings.last_root.strip()
        if not raw:
            return
        validation = validate_scan_root(Path(raw))
        if validation.ok:
            self._set_selected_root(Path(raw))

    def _set_selected_root(self, path: Path) -> None:
        resolved = path.expanduser().resolve(strict=False)
        self.selected_root = resolved
        self.settings.last_root = str(resolved)
        self.root_label.setText(str(resolved))
        self.duplicate_root.setText(f"Suchordner: {resolved}")
        self.save_settings()

    def _choose_root(self) -> None:
        start = str(self.selected_root or Path.home())
        chosen = QFileDialog.getExistingDirectory(self, "Suchordner wählen", start)
        if not chosen:
            return
        validation = validate_scan_root(Path(chosen))
        if not validation.ok:
            QMessageBox.information(self, validation.title, validation.message)
            return
        self._set_selected_root(Path(chosen))

    def _current_scan_options(self) -> ScanOptions:
        return ScanOptions(
            skip_python_project_dirs=self.settings.skip_python_project_dirs,
            skip_hidden_dirs=self.settings.skip_hidden_dirs,
            excluded_extensions=frozenset(self.settings.excluded_extensions),
        )

    def _filter_summary_text(self) -> str:
        project = (
            "Entwicklungsordner werden ausgelassen"
            if self.settings.skip_python_project_dirs
            else "Entwicklungsordner werden mitgeprüft"
        )
        hidden = (
            "versteckte Ordner werden ausgelassen"
            if self.settings.skip_hidden_dirs
            else "versteckte Ordner werden mitgeprüft"
        )
        count = len(self.settings.excluded_extensions)
        return f"Filter: {project} · {hidden} · {count} Dateitypen ausgeschlossen"

    def _update_filter_summaries(self) -> None:
        text = self._filter_summary_text()
        if hasattr(self, "search_filter_summary"):
            self.search_filter_summary.setText(text)
        if hasattr(self, "duplicate_filter_summary"):
            self.duplicate_filter_summary.setText(
                text + f" · SHA-256 parallel: max. {self.settings.resolved_cpu_workers()} Kerne"
            )

    def _open_scan_options(self) -> None:
        dialog = ScanOptionsDialog(
            self,
            skip_python_project_dirs=self.settings.skip_python_project_dirs,
            skip_hidden_dirs=self.settings.skip_hidden_dirs,
            excluded_extensions=set(self.settings.excluded_extensions),
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        self.settings.skip_python_project_dirs = dialog.python_dirs.isChecked()
        self.settings.skip_hidden_dirs = dialog.hidden_dirs.isChecked()
        self.settings.excluded_extensions = sorted(dialog.excluded_extensions())
        self.save_settings()
        self._update_filter_summaries()
        self.status_label.setText("🟢 Prüfoptionen gespeichert")

    def _active_worker(self) -> ManagedWorker | None:
        for worker in (self.search_worker, self.duplicate_worker):
            if worker is not None and worker.isRunning():
                return worker
        return None

    def _begin_process(self, phase: str) -> None:
        self.search_button.setEnabled(False)
        self.duplicate_start.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.pause_button.setText("⏸ Pause")
        self.cancel_button.setEnabled(True)
        self._last_phase = phase
        self.status_label.setText("🟡 Verarbeitung läuft")
        self.activity_label.setText(f"Aktueller Schritt: {phase}")
        self.eta_label.setText("Restzeit: wird berechnet")

    def _finish_process(self) -> None:
        self.search_button.setEnabled(True)
        self.duplicate_start.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("⏸ Pause")
        self.cancel_button.setEnabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("100 %")
        self.eta_label.setText("Restzeit: 0 s")

    def _connect_worker(self, worker: ManagedWorker) -> None:
        worker.progress.connect(self._process_progress)
        worker.pause_changed.connect(self._process_pause_changed)
        worker.cancelled.connect(self._process_cancelled)

    def _process_progress(self, current: int, total: int, phase: str, eta_seconds: int) -> None:
        self._last_phase = phase
        self.activity_label.setText(f"Aktueller Schritt: {phase}")
        if total <= 0:
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFormat("wird ermittelt …")
            self.counter_label.setText(f"{current} Dateien entdeckt")
        else:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(min(current, total))
            percent = round((current / total) * 100) if total else 0
            self.progress_bar.setFormat(f"{current} / {total} · {percent} %")
        self.eta_label.setText(self._eta_text(eta_seconds))

    @staticmethod
    def _eta_text(seconds: int) -> str:
        if seconds < 0:
            return "Restzeit: wird berechnet"
        if seconds < 60:
            return f"Restzeit: ca. {seconds} s"
        minutes, rest = divmod(seconds, 60)
        if minutes < 60:
            return f"Restzeit: ca. {minutes} min {rest:02d} s"
        hours, minutes = divmod(minutes, 60)
        return f"Restzeit: ca. {hours} h {minutes:02d} min"

    def _pause_or_resume(self) -> None:
        worker = self._active_worker()
        if worker is None:
            return
        if worker.control.paused:
            worker.request_resume()
        else:
            worker.request_pause()

    def _process_pause_changed(self, paused: bool) -> None:
        if paused:
            self.status_label.setText("🟡 Pausiert")
            self.activity_label.setText(f"Aktueller Schritt: pausiert · {self._last_phase}")
            self.eta_label.setText("Restzeit: nach Fortsetzen")
            self.pause_button.setText("▶ Fortsetzen")
        else:
            self.status_label.setText("🟡 Verarbeitung läuft")
            self.activity_label.setText(f"Aktueller Schritt: {self._last_phase}")
            self.pause_button.setText("⏸ Pause")

    def _cancel_active_process(self) -> None:
        worker = self._active_worker()
        if worker is None:
            return
        worker.request_cancel()
        self.cancel_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.status_label.setText("🟡 Abbruch angefordert")
        self.activity_label.setText("Aktueller Schritt: sicherer Abbruch wird abgeschlossen")
        self.eta_label.setText("Restzeit: wenige Augenblicke")

    def _process_cancelled(self, message: str) -> None:
        self._finish_process()
        self.status_label.setText("🟡 Vorgang abgebrochen · Originaldateien unverändert")
        self.activity_label.setText("Aktueller Schritt: abgebrochen")
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Abgebrochen")
        self.eta_label.setText("Restzeit: –")
        self.counter_label.setText(message)

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
        if self._active_worker() is not None:
            QMessageBox.information(self, "Prüfung läuft", "Bitte zuerst den laufenden Vorgang beenden.")
            return

        job = SearchJob(
            root=self.selected_root,
            query=query,
            search_names=self.names_box.isChecked(),
            search_contents=self.contents_box.isChecked(),
        )
        self.counter_label.setText("Suche wird vorbereitet …")
        self._begin_process("Dateiliste wird vorbereitet")
        self.search_worker = SearchWorker(job, self._current_scan_options())
        self._connect_worker(self.search_worker)
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
            mark_item.setData(Qt.ItemDataRole.UserRole, str(hit.path))
            self.results.setItem(row, 0, mark_item)
            self.results.setItem(row, 1, QTableWidgetItem(hit.source))
            self.results.setItem(row, 2, QTableWidgetItem(str(hit.path)))
            self.results.setItem(row, 3, QTableWidgetItem("" if hit.line_number is None else str(hit.line_number)))
            self.results.setItem(row, 4, QTableWidgetItem(hit.excerpt))
        self.results.setSortingEnabled(sorting)
        self._finish_process()
        self.status_label.setText("🟢 Textsuche abgeschlossen")
        self.activity_label.setText("Aktueller Schritt: Ergebnisse bereit")
        self.counter_label.setText(f"{job.scanned_files} Textdateien geprüft · {len(hits)} Treffer")
        self.result_info.setText(f"{len(hits)} Treffer")
        self.nav.setCurrentRow(self.PAGE_RESULTS)

    def _search_failed(self, message: str) -> None:
        entry = record_error(self.base_dir / "logs", "textsuche", message)
        self._finish_process()
        self.status_label.setText("🔴 Textsuche gestoppt")
        self.activity_label.setText("Aktueller Schritt: sicher gestoppt")
        self.progress_bar.setValue(0)
        self.eta_label.setText("Restzeit: –")
        QMessageBox.critical(
            self,
            "Suche gestoppt",
            f"Die Suche wurde sicher beendet.\n\n{message}\n\nLösung: {entry['solution']}",
        )

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
        item = self.results.item(row, 0)
        if item:
            item.setText("★" if self.result_mark.isChecked() else "")
        self.status_label.setText("🟢 Virtuelle Markierung gespeichert")

    def _copy_selected_result_path(self) -> None:
        path = self._selected_result_path()
        if path is None:
            QMessageBox.information(self, "Kein Treffer", "Bitte zuerst einen Treffer auswählen.")
            return
        QApplication.clipboard().setText(str(path))
        self.status_label.setText("🟢 Pfad in die Zwischenablage kopiert")

    def _open_selected_result_folder(self) -> None:
        path = self._selected_result_path()
        if path is None:
            QMessageBox.information(self, "Kein Treffer", "Bitte zuerst einen Treffer auswählen.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))

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
        if self._active_worker() is not None:
            QMessageBox.information(self, "Prüfung läuft", "Bitte zuerst den laufenden Vorgang beenden.")
            return

        workers = self.settings.resolved_cpu_workers()
        self.duplicate_summary.setText(
            f"Dateigrößen werden gruppiert; nur Kandidaten werden vollständig gehasht. "
            f"CPU-Begrenzung: maximal {workers} Kerne."
        )
        self._begin_process("Dateiliste wird vorbereitet")
        self.duplicate_worker = DuplicateWorker(
            self.selected_root,
            self._current_scan_options(),
            max_workers=workers,
        )
        self._connect_worker(self.duplicate_worker)
        self.duplicate_worker.completed.connect(self._duplicate_scan_finished)
        self.duplicate_worker.failed.connect(self._duplicate_scan_failed)
        self.duplicate_worker.start()

    def _duplicate_scan_finished(self, scanned: int, groups: list[DuplicateGroup]) -> None:
        self.database.replace_duplicate_groups(groups)
        self.duplicate_groups_cache = list(groups)
        self._fill_duplicate_groups()
        duplicates = sum(len(group.paths) for group in groups)
        self._finish_process()
        self.status_label.setText("🟢 Duplikatprüfung abgeschlossen")
        self.activity_label.setText("Aktueller Schritt: Duplikatgruppen bereit")
        self.counter_label.setText(f"{scanned} Dateien geprüft · {len(groups)} Gruppen · {duplicates} Dateien")
        self.duplicate_summary.setText(
            f"{len(groups)} sichere Duplikatgruppen gefunden. Jede Gruppe besitzt identische Größe und SHA-256-Prüfsumme."
        )

    def _duplicate_scan_failed(self, message: str) -> None:
        entry = record_error(self.base_dir / "logs", "duplikatpruefung", message)
        self._finish_process()
        self.status_label.setText("🔴 Duplikatprüfung gestoppt")
        self.activity_label.setText("Aktueller Schritt: sicher gestoppt")
        self.progress_bar.setValue(0)
        self.eta_label.setText("Restzeit: –")
        QMessageBox.critical(
            self,
            "Duplikatprüfung gestoppt",
            f"Die Prüfung wurde sicher beendet.\n\n{message}\n\nLösung: {entry['solution']}",
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
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
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
            item.setData(Qt.ItemDataRole.UserRole, collection.id)
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
        value = item.data(Qt.ItemDataRole.UserRole)
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
            path_item.setData(Qt.ItemDataRole.UserRole, str(entry.path))
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
        raw_path = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not raw_path:
            return
        self.database.remove_collection_item(collection_id, Path(str(raw_path)))
        self._show_collection(self.collection_list.currentRow())
        self.status_label.setText("🟢 Eintrag nur aus der virtuellen Sammlung entfernt")

    def save_settings(self) -> Path:
        self.settings.window_width = self.width()
        self.settings.window_height = self.height()
        if self.selected_root is not None:
            self.settings.last_root = str(self.selected_root)
        return self.settings_store.save(self.settings)

    def autosave_provoware_state(self) -> Path:
        self.save_settings()
        payload = build_export(self.settings.to_dict(), self.database.export_virtual_state())
        validate_import(payload)
        target = self.base_dir / "recovery" / "autosave-state.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        validate_import(json.loads(target.read_text(encoding="utf-8")))
        return target

    def export_provoware_state(self) -> None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M")
        default = self.base_dir / "exports" / f"provoware-zustand-{stamp}.json"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "PROVOWARE-Zustand exportieren",
            str(default),
            "PROVOWARE-Zustand (*.json)",
        )
        if not path:
            return
        payload = build_export(self.settings.to_dict(), self.database.export_virtual_state())
        try:
            validate_import(payload)
            Path(path).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            validate_import(json.loads(Path(path).read_text(encoding="utf-8")))
        except OSError as exc:
            QMessageBox.critical(self, "Export fehlgeschlagen", str(exc))
            return
        self.status_label.setText("🟢 PROVOWARE-Zustand exportiert")

    def import_provoware_state(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "PROVOWARE-Zustand importieren",
            str(self.base_dir / "exports"),
            "PROVOWARE-Zustand (*.json)",
        )
        if not path:
            return
        try:
            payload = validate_import(json.loads(Path(path).read_text(encoding="utf-8")))
            imported_settings = AppSettings.from_dict(payload["settings"])
            virtual_state = payload["virtual_state"]
        except (OSError, ValueError, TypeError, StateImportError) as exc:
            QMessageBox.critical(self, "Import abgelehnt", f"Die Datei wurde nicht übernommen.\n\n{exc}")
            return

        answer = QMessageBox.question(
            self,
            "Import bestätigen",
            "Der Import ersetzt nur PROVOWARE-Einstellungen, Markierungen und virtuelle Sammlungen.\n"
            "Originaldateien werden nicht verändert.\n\nJetzt übernehmen?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            collections, items = self.database.import_virtual_state(virtual_state)
        except Exception as exc:
            QMessageBox.critical(self, "Import sicher gestoppt", str(exc))
            return

        self.settings = imported_settings
        self.save_settings()
        self._restore_last_root()
        self._refresh_collections()
        self._update_filter_summaries()
        enhancements = getattr(self, "_ui_enhancements", None)
        if enhancements is not None:
            enhancements.refresh_from_settings()
        self.status_label.setText(
            f"🟢 Import abgeschlossen · {collections} Sammlungen · {items} Einträge"
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        worker = self._active_worker()
        if worker is not None:
            answer = QMessageBox.question(
                self,
                "Vorgang läuft",
                "Ein Prüfauftrag läuft noch. Soll er sicher abgebrochen und das Programm beendet werden?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            worker.request_cancel()
            if not worker.wait(2500):
                QMessageBox.information(
                    self,
                    "Abbruch läuft",
                    "Der Auftrag beendet gerade einen sicheren Prüfschritt. "
                    "Bitte das Fenster danach erneut schließen.",
                )
                event.ignore()
                return
        self.save_settings()
        event.accept()

    @staticmethod
    def _human_size(size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024.0 or unit == "TB":
                return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
            value /= 1024.0
        return f"{size} B"
