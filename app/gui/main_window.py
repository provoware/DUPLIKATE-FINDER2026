from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QDialog,
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
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.gui.workers import DuplicateWorker, SearchWorker
from app.gui.process_controller import ProcessUiController
from app.gui.table_models import CollectionItemsModel, DuplicateMembersModel, SearchResultsModel
from app.core.scanner import ScanOptions
from app.models.entities import DuplicateGroup, SearchHit, SearchJob
from app.safety.policy import WRITE_FEATURES
from app.storage.database import Database
from app.validation import validate_scan_root, validate_search_request
from app.gui.design_tokens import BASE_SPACING, OUTER_MARGIN
from app.texts import text as ui_text
from app.error_management import record_error
from app.formatting import format_bytes
from app.file_browser.widget import FileBrowserWidget


class MainWindow(QMainWindow):
    PAGE_DASHBOARD = 0
    PAGE_SEARCH = 1
    PAGE_RESULTS = 2
    PAGE_DUPLICATES = 3
    PAGE_COLLECTIONS = 4
    PAGE_FILES = 5
    PAGE_JOURNAL = 6
    PAGE_HELP = 7

    def __init__(self, base_dir: Path, database: Database) -> None:
        super().__init__()
        self.base_dir = base_dir
        self.database = database
        self.selected_root: Path | None = None
        self.search_worker: SearchWorker | None = None
        self.duplicate_worker: DuplicateWorker | None = None
        self.last_search_job_id: int | None = None
        self.duplicate_groups_cache: list[tuple[int, str, int, int]] = []
        self.results_model = SearchResultsModel(database, self)
        self.duplicate_members_model = DuplicateMembersModel(database, self)
        self.collection_items_model = CollectionItemsModel(database, self)
        self.scan_options = ScanOptions()
        self.process_controller = ProcessUiController(self)

        self.setWindowTitle("PROVOWARE DUPLIKATE-FINDER 2026 – Nur-Lesen-Modus")
        app = QApplication.instance()
        self.setProperty("uiZoom", int(app.property("provowareUiZoom") or 100) if app else 100)
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

    def _build_card(
        self,
        title: str,
        value: str,
        *,
        object_name: str | None = None,
        live: bool = False,
    ) -> tuple[QFrame, QLabel]:
        frame = QFrame()
        frame.setProperty("card", True)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        heading = QLabel(title)
        heading.setProperty("cardTitle", True)
        heading.setStyleSheet("font-weight:700;")
        heading.setWordWrap(True)

        label = QLabel(value)
        label.setProperty("cardValue", True)
        label.setWordWrap(True)
        if object_name:
            label.setObjectName(object_name)
        if live:
            label.setToolTip("Wird während laufender Vorgänge automatisch aktualisiert.")

        font = label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        label.setFont(font)
        layout.addWidget(heading)
        layout.addWidget(label)
        return frame, label

    def _card(self, title: str, value: str) -> QFrame:
        frame, _label = self._build_card(title, value)
        return frame

    def _live_card(self, title: str, value: str, object_name: str) -> tuple[QFrame, QLabel]:
        return self._build_card(
            title,
            value,
            object_name=object_name,
            live=True,
        )

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(OUTER_MARGIN, OUTER_MARGIN, OUTER_MARGIN, 4)
        root.setSpacing(BASE_SPACING - 2)

        header = QHBoxLayout()
        title = self._heading("DUPLIKATE-FINDER 2026")
        title.setObjectName("app_title")
        title.setWordWrap(True)
        title.setAccessibleName("PROVOWARE Duplikate-Finder 2026")
        title.setAccessibleDescription("Lokales Werkzeug für Textsuche und Duplikatprüfung.")
        mode = QLabel("NUR LESEN · ORIGINALDATEIEN BLEIBEN UNVERÄNDERT")
        mode.setObjectName("safety_banner")
        mode.setWordWrap(True)
        mode.setAccessibleName("Sicherheit: Originaldateien bleiben unverändert")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(mode)
        root.addLayout(header)

        self.compact_nav = QComboBox()
        self.compact_nav.setObjectName("compact_navigation")
        self.compact_nav.setAccessibleName("Bereich auswählen")
        self.compact_nav.setToolTip("Wähle den Programmteil, den du öffnen möchtest.")
        self.compact_nav.setMaximumWidth(210)
        nav_items = ["Übersicht", "Textsuche", "Ergebnisse", "Duplikate", "Sammlungen", "Dateien & Vorschau", "Journal", "Hilfe"]
        nav_colors = ["#74d9ff", "#6ee7ff", "#9ce6ff", "#ff7e9d", "#d59bff", "#ffbf69", "#74e39a", "#b8c4ff"]
        self.compact_nav.addItems(nav_items)
        for index, color in enumerate(nav_colors):
            self.compact_nav.setItemData(index, QColor(color), Qt.ItemDataRole.ForegroundRole)
        header.addWidget(self.compact_nav)

        body = QHBoxLayout()
        self.nav = QListWidget()
        self.nav.setObjectName("main_navigation")
        self.nav.setAccessibleName("Hauptnavigation")
        self.nav.addItems(nav_items)
        for index, color in enumerate(nav_colors):
            self.nav.item(index).setForeground(QColor(color))
        self.compact_nav.currentIndexChanged.connect(self.nav.setCurrentRow)
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
        self.file_browser = FileBrowserWidget(self.database, self)
        self.pages.addWidget(self.file_browser)
        self.pages.addWidget(self._journal_page())
        self.pages.addWidget(self._help_page())
        body.addWidget(self.pages, 1)
        root.addLayout(body, 1)

        footer = QVBoxLayout()
        footer.setSpacing(3)

        status_row = QGridLayout()
        status_row.setHorizontalSpacing(6)
        status_row.setVerticalSpacing(2)
        self.process_status_row = status_row
        self.status_label = QLabel("OK · Bereit")
        self.status_label.setObjectName("status_label")
        self.status_label.setAccessibleName("Vorgangsstatus")
        self.status_label.setStyleSheet("font-weight: 800;")
        self.activity_label = QLabel("Aktivität: bereit")
        self.activity_label.setObjectName("activity_label")
        self.activity_label.setAccessibleName("Aktuelle Aktivität")
        self.activity_label.setToolTip("Zeigt an, woran das Programm gerade arbeitet.")
        self.activity_label.setWordWrap(True)
        self.step_label = QLabel("Schritt: bereit")
        self.step_label.setObjectName("step_label")
        self.step_label.setAccessibleName("Aktueller Schritt")
        self.step_label.setToolTip("Aktueller Arbeitsschritt.")
        self.step_label.setWordWrap(True)
        self.eta_label = QLabel("Restzeit: –")
        self.eta_label.setObjectName("eta_label")
        self.eta_label.setAccessibleName("Geschätzte Restzeit")
        self.eta_label.setToolTip("Grobe Schätzung auf Basis der bisherigen Geschwindigkeit.")
        self.eta_label.setWordWrap(True)
        self._update_process_status_layout()
        footer.addLayout(status_row)

        control_row = QHBoxLayout()
        control_row.setSpacing(6)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("activity_progress")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("%p %")
        self.progress_bar.setMinimumWidth(180)
        self.progress_bar.setAccessibleName("Fortschritt des Vorgangs")
        self.progress_bar.setAccessibleDescription("Zeigt den Anteil der bereits geprüften Dateien.")
        self.pause_button = QPushButton("Pause")
        self.pause_button.setObjectName("process_pause")
        self.pause_button.setProperty("compact", True)
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.process_controller.toggle_pause)
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.setObjectName("process_cancel")
        self.cancel_button.setProperty("compact", True)
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.process_controller.cancel_active_process)
        self.counter_label = QLabel("0 Dateien geprüft · 0 Treffer")
        self.counter_label.setObjectName("counter_label")
        self.counter_label.setAccessibleName("Geprüfte Dateien und gefundene Treffer")
        control_row.addWidget(self.progress_bar, 1)
        control_row.addWidget(self.pause_button)
        control_row.addWidget(self.cancel_button)
        control_row.addStretch(1)
        control_row.addWidget(self.counter_label)
        footer.addLayout(control_row)
        root.addLayout(footer)

        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.currentRowChanged.connect(self._sync_compact_navigation)
        self.setCentralWidget(central)
        self._update_navigation_layout()

    def _sync_compact_navigation(self, row: int) -> None:
        if self.compact_nav.currentIndex() != row:
            self.compact_nav.setCurrentIndex(row)

    def _update_navigation_layout(self) -> None:
        compact = self.width() < 960
        self.compact_nav.setVisible(compact)
        self.nav.setVisible(not compact)
        self._update_feature_layout()
        self._update_dashboard_card_layout()
        self._update_process_status_layout()

    def _update_process_status_layout(self) -> None:
        if not hasattr(self, "process_status_row"):
            return
        while self.process_status_row.count():
            self.process_status_row.takeAt(0)
        if self.width() >= 960:
            self.process_status_row.addWidget(self.status_label, 0, 0)
            self.process_status_row.addWidget(self.activity_label, 0, 1)
            self.process_status_row.addWidget(self.step_label, 0, 2)
            self.process_status_row.addWidget(self.eta_label, 0, 3)
        else:
            self.process_status_row.addWidget(self.status_label, 0, 0)
            self.process_status_row.addWidget(self.activity_label, 0, 1, 1, 2)
            self.process_status_row.addWidget(self.step_label, 1, 0, 1, 2)
            self.process_status_row.addWidget(self.eta_label, 1, 2)

    def _update_feature_layout(self) -> None:
        if not hasattr(self, "feature_layout"):
            return
        columns = 2 if self.width() < 960 or int(self.property("uiZoom") or 100) >= 150 else 4
        self.feature_layout.removeWidget(self.feature_heading)
        self.feature_layout.addWidget(self.feature_heading, 0, 0, 1, columns)
        for index, checkbox in enumerate(self.feature_checks):
            self.feature_layout.removeWidget(checkbox)
            self.feature_layout.addWidget(checkbox, 1 + index // columns, index % columns)

    def _update_dashboard_card_layout(self) -> None:
        if not hasattr(self, "dashboard_card_layout"):
            return
        zoom = int(self.property("uiZoom") or 100)
        columns = 2 if zoom >= 150 else 4
        if hasattr(self, "workflow_guide"):
            self.workflow_guide.setText(
                "Ordner → Prüfen → Treffer → Sammlung"
                if zoom >= 150
                else "Ablauf: Ordner → Prüfen → Treffer → Sammlung"
            )
        for index, card in enumerate(self.dashboard_cards):
            self.dashboard_card_layout.removeWidget(card)
            self.dashboard_card_layout.addWidget(card, index // columns, index % columns)
        for column in range(4):
            self.dashboard_card_layout.setColumnStretch(column, 1 if column < columns else 0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "compact_nav"):
            self._update_navigation_layout()

    def _dashboard_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_dashboard")
        page.setProperty("area", "dashboard")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        dashboard_head = QHBoxLayout()
        dashboard_head.addWidget(self._heading("Übersicht"))
        dashboard_head.addStretch(1)
        self.workflow_guide = QLabel("Ablauf: Ordner → Prüfen → Treffer → Sammlung")
        self.workflow_guide.setObjectName("workflow_guide")
        self.workflow_guide.setProperty("workflowGuide", True)
        self.workflow_guide.setWordWrap(False)
        self.workflow_guide.setAccessibleName("Kurzanleitung für den Arbeitsablauf")
        self.workflow_guide.setToolTip(
            "1. Ordner wählen · 2. Suche oder Duplikatprüfung starten · "
            "3. Treffer ansehen · 4. Virtuell organisieren"
        )
        dashboard_head.addWidget(self.workflow_guide)
        layout.addLayout(dashboard_head)

        cards = QGridLayout()
        self.dashboard_card_layout = cards
        self.dashboard_cards = [self._card("Sicherheitsmodus", "Nur lesen")]
        process_card, self.dashboard_process_value = self._live_card(
            "Vorgang", "Bereit", "dashboard_process_metrics"
        )
        resource_card, self.dashboard_resource_value = self._live_card(
            "Ressourcen", "CPU – · RAM – · SWAP –", "dashboard_resource_metrics"
        )
        self.dashboard_cards.extend((process_card, resource_card, self._card("Datenbank", "Lokal · SQLite")))
        self._update_dashboard_card_layout()
        layout.addLayout(cards)

        feature_box = QFrame()
        feature_box.setObjectName("locked_write_features")
        feature_box.setProperty("card", True)
        feature_layout = QGridLayout(feature_box)
        feature_layout.setContentsMargins(10, 8, 10, 8)
        feature_layout.setHorizontalSpacing(8)
        feature_layout.setVerticalSpacing(4)
        label = QLabel("Dateiaktionen – im Nur-Lesen-Modus gesperrt")
        label.setObjectName("locked_features_heading")
        self.feature_layout = feature_layout
        self.feature_heading = label
        label.setWordWrap(True)
        label.setStyleSheet("font-weight: 800;")
        feature_layout.addWidget(label, 0, 0, 1, 4)

        flags = {row["key"]: row for row in self.database.feature_flags()}
        self.feature_checks = []
        for index, (key, text) in enumerate(WRITE_FEATURES.items()):
            checkbox = QCheckBox(text)
            checkbox.setObjectName(f"feature_{key}")
            checkbox.setText(f"{text} · gesperrt")
            checkbox.setChecked(bool(flags[key]["enabled"]))
            checkbox.setEnabled(False)
            checkbox.setAccessibleDescription("Technisch gesperrt. Originaldateien bleiben unverändert.")
            checkbox.setToolTip("In diesem Sicherheitsstand nicht verfügbar. Originaldateien bleiben unverändert.")
            self.feature_checks.append(checkbox)
        layout.addWidget(feature_box)
        self._update_feature_layout()

        quick = QGridLayout()
        go_search = QPushButton("Text suchen")
        go_search.setObjectName("dashboard_go_search")
        go_search.setProperty("primaryAction", True)
        go_duplicates = QPushButton("Duplikate prüfen")
        go_duplicates.setObjectName("dashboard_go_duplicates")
        go_duplicates.setProperty("primaryAction", True)
        go_collections = QPushButton("Sammlungen")
        go_collections.setObjectName("dashboard_go_collections")
        go_collections.setProperty("primaryAction", True)
        go_files = QPushButton("Dateien & Vorschau")
        go_files.setObjectName("dashboard_go_files")
        go_files.setProperty("primaryAction", True)
        go_search.clicked.connect(lambda: self.nav.setCurrentRow(self.PAGE_SEARCH))
        go_duplicates.clicked.connect(lambda: self.nav.setCurrentRow(self.PAGE_DUPLICATES))
        go_collections.clicked.connect(lambda: self.nav.setCurrentRow(self.PAGE_COLLECTIONS))
        go_files.clicked.connect(lambda: self.nav.setCurrentRow(self.PAGE_FILES))
        quick.addWidget(go_search, 0, 0)
        quick.addWidget(go_duplicates, 0, 1)
        quick.addWidget(go_collections, 0, 2)
        quick.addWidget(go_files, 0, 3)
        layout.addLayout(quick)
        layout.addStretch(1)
        return page

    def _root_selector(self) -> tuple[QHBoxLayout, QLineEdit, QPushButton]:
        row = QHBoxLayout()
        label = QLineEdit()
        label.setReadOnly(True)
        label.setPlaceholderText("Noch kein Ordner gewählt")
        choose = QPushButton("Ordner wählen")
        choose.clicked.connect(self._choose_root)
        row.addWidget(label, 1)
        row.addWidget(choose)
        return row, label, choose

    def _search_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_search")
        page.setProperty("area", "search")
        layout = QVBoxLayout(page)
        layout.addWidget(self._heading("Textdateien durchsuchen"))

        root_row, self.root_label, choose = self._root_selector()
        self.root_label.setObjectName("search_root")
        self.root_label.setAccessibleName("Gewählter Suchordner")
        choose.setObjectName("search_choose_root")
        layout.addLayout(root_row)

        query_grid = QGridLayout()
        self.query_edit = QLineEdit()
        self.query_edit.setObjectName("search_query")
        self.query_edit.setAccessibleName("Suchbegriff")
        self.query_edit.setPlaceholderText("Suchbegriff")
        self.query_edit.setToolTip("Gib das Wort oder den Text ein, den du finden möchtest.")
        self.names_box = QCheckBox("Dateinamen")
        self.names_box.setObjectName("search_names")
        self.names_box.setAccessibleName("In Dateinamen suchen")
        self.names_box.setChecked(True)
        self.contents_box = QCheckBox("Dateiinhalte")
        self.contents_box.setObjectName("search_contents")
        self.contents_box.setAccessibleName("In Dateiinhalten suchen")
        self.contents_box.setChecked(True)
        self.search_button = QPushButton("Suche starten")
        self.search_button.setObjectName("search_start")
        self.search_button.setProperty("primaryAction", True)
        self.search_button.clicked.connect(self._start_search)
        self.search_button.setToolTip("Startet eine reine Lese-Suche. Originaldateien werden nicht verändert.")
        query_grid.addWidget(self.query_edit, 0, 0, 1, 3)
        query_grid.addWidget(self.names_box, 1, 0)
        query_grid.addWidget(self.contents_box, 1, 1)
        query_grid.addWidget(self.search_button, 1, 2)
        layout.addLayout(query_grid)

        filters = QFrame()
        filters.setProperty("section", True)
        filter_layout = QGridLayout(filters)
        filter_title = QLabel("Ausschlüsse")
        filter_title.setStyleSheet("font-weight:800;")
        self.exclude_python_box = QCheckBox("Python-/Entwicklungsordner automatisch auslassen")
        self.exclude_python_box.setObjectName("exclude_python_dirs")
        self.exclude_python_box.setChecked(True)
        self.exclude_python_box.setToolTip("Lässt z. B. .venv, __pycache__, build, dist, .git und Laufzeitordner aus.")
        self.exclude_python_box.toggled.connect(self._refresh_filter_summary)
        self.excluded_types_label = QLabel("Dateitypen: keine zusätzlichen Ausschlüsse")
        self.excluded_types_label.setObjectName("excluded_types_label")
        self.excluded_types_label.setWordWrap(True)
        self.excluded_types_button = QPushButton("Dateitypen auswählen")
        self.excluded_types_button.setObjectName("excluded_types_button")
        self.excluded_types_button.clicked.connect(self._choose_excluded_types)
        filter_layout.addWidget(filter_title, 0, 0, 1, 2)
        filter_layout.addWidget(self.exclude_python_box, 1, 0, 1, 2)
        filter_layout.addWidget(self.excluded_types_label, 2, 0)
        filter_layout.addWidget(self.excluded_types_button, 2, 1)
        layout.addWidget(filters)

        info = QLabel(
            "Die Textsuche liest nur unterstützte Textformate. Symbolische Verknüpfungen "
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
        page.setProperty("area", "results")
        layout = QVBoxLayout(page)

        head = QHBoxLayout()
        head.addWidget(self._heading("Ergebnisse"))
        self.result_info = QLabel("Noch keine Suche ausgeführt")
        self.result_info.setObjectName("result_info")
        head.addStretch(1)
        head.addWidget(self.result_info)
        layout.addLayout(head)

        self.results = QTableView()
        self.results.setObjectName("results_table")
        self.results.setAccessibleName("Suchergebnisse")
        self.results.setAccessibleDescription("Virtuelle Liste. Mit den Pfeiltasten kannst du Treffer auswählen.")
        self.results.setModel(self.results_model)
        self.results.setSortingEnabled(True)
        self.results.horizontalHeader().setStretchLastSection(True)
        self.results.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results.selectionModel().selectionChanged.connect(
            lambda _selected, _deselected: self._load_selected_result_state()
        )
        layout.addWidget(self.results, 1)

        meta = QGridLayout()
        self.result_mark = QCheckBox("Treffer markieren")
        self.result_mark.setObjectName("result_mark")
        self.result_note = QLineEdit()
        self.result_note.setObjectName("result_note")
        self.result_note.setPlaceholderText("Notiz zum ausgewählten Treffer")
        save_meta = QPushButton("Markierung und Notiz speichern")
        save_meta.setObjectName("result_save_meta")
        save_meta.clicked.connect(self._save_selected_result_state)
        self.result_collection = QComboBox()
        self.result_collection.setObjectName("result_collection")
        add_collection = QPushButton("In Sammlung aufnehmen")
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
        page.setProperty("area", "duplicates")
        layout = QVBoxLayout(page)

        top = QVBoxLayout()
        top.addWidget(self._heading("Duplikate – gruppiert und vollständig geprüft"))
        self.duplicate_start = QPushButton("Gewählten Ordner prüfen")
        self.duplicate_start.setObjectName("duplicate_start")
        self.duplicate_start.setProperty("primaryAction", True)
        self.duplicate_start.clicked.connect(self._start_duplicate_scan)
        top.addWidget(self.duplicate_start)
        layout.addLayout(top)

        self.duplicate_root = QLabel("Suchordner: noch nicht gewählt")
        self.duplicate_root.setObjectName("duplicate_root")
        self.duplicate_root.setWordWrap(True)
        layout.addWidget(self.duplicate_root)
        self.duplicate_filter_info = QLabel("Ausschlüsse: Python-/Entwicklungsordner aktiv · keine zusätzlichen Dateitypen")
        self.duplicate_filter_info.setObjectName("duplicate_filter_info")
        self.duplicate_filter_info.setWordWrap(True)
        self.duplicate_filter_info.setProperty("section", True)
        layout.addWidget(self.duplicate_filter_info)

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
        self.duplicate_members = QTableView()
        self.duplicate_members.setObjectName("duplicate_members")
        self.duplicate_members.setAccessibleName("Dateien in der ausgewählten Duplikatgruppe")
        self.duplicate_members.setModel(self.duplicate_members_model)
        self.duplicate_members.setSortingEnabled(True)
        self.duplicate_members.horizontalHeader().setStretchLastSection(True)
        self.duplicate_members.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.duplicate_members.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.duplicate_members, 1)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter, 1)

        note = QLabel(
            "Diese Ansicht vergleicht nur. Es gibt hier absichtlich keinen Löschen-, "
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
        page.setProperty("area", "collections")
        layout = QVBoxLayout(page)
        layout.addWidget(self._heading("Virtuelle Sammlungen"))

        create = QGridLayout()
        self.collection_name = QLineEdit()
        self.collection_name.setObjectName("collection_name")
        self.collection_name.setPlaceholderText("Name der neuen Sammlung")
        self.collection_note = QLineEdit()
        self.collection_note.setObjectName("collection_note")
        self.collection_note.setPlaceholderText("Optionale Beschreibung")
        create_button = QPushButton("Sammlung anlegen")
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
        self.collection_items_table = QTableView()
        self.collection_items_table.setObjectName("collection_items")
        self.collection_items_table.setAccessibleName("Dateien in der ausgewählten Sammlung")
        self.collection_items_table.setModel(self.collection_items_model)
        self.collection_items_table.setSortingEnabled(True)
        self.collection_items_table.horizontalHeader().setStretchLastSection(True)
        self.collection_items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.collection_items_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.collection_items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.collection_items_table, 1)
        remove = QPushButton("Nur aus Sammlung entfernen")
        remove.setObjectName("collection_remove")
        remove.clicked.connect(self._remove_selected_collection_item)
        right_layout.addWidget(remove)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter, 1)

        safe = QLabel("Sammlungen sind rein virtuell. Die Dateien bleiben an ihrem Originalort.")
        safe.setObjectName("collection_safety_note")
        safe.setWordWrap(True)
        safe.setProperty("card", True)
        layout.addWidget(safe)
        return page

    def _journal_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page_journal")
        page.setProperty("area", "journal")
        layout = QVBoxLayout(page)
        layout.addWidget(self._heading("Änderungsjournal"))
        info = QLabel(
            "Der Nur-Lesen-Modus führt keine physischen Dateiänderungen aus. Das Journal-Schema ist "
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
        page.setProperty("area", "help")
        layout = QVBoxLayout(page)
        layout.addWidget(self._heading("Hilfe – drei Stufen"))

        level1 = QLabel("1. Kurz erklärt: Ordner wählen → Suche oder Duplikatprüfung starten → Treffer virtuell ordnen.")
        level1.setWordWrap(True)
        level1.setProperty("card", True)
        layout.addWidget(level1)

        level2 = QLabel("2. Direkt am Bedienelement: Fahre mit der Maus über einen Knopf oder ein Feld. Ein Tooltip erklärt die Funktion und mögliche Folgen.")
        level2.setWordWrap(True)
        level2.setProperty("card", True)
        layout.addWidget(level2)

        level3 = QLabel(
            "3. Ausführliche Hilfe:\n"
            "• Textsuche: " + ui_text("help.search_short") + "\n"
            "• Duplikate: " + ui_text("help.duplicates_short") + "\n"
            "• Sammlungen: " + ui_text("help.collections_short") + "\n"
            "Bei einem Fehler zeigt das Programm einen sicheren Abbruch, eine verständliche Meldung und den Protokollordner."
        )
        level3.setWordWrap(True)
        level3.setProperty("card", True)
        layout.addWidget(level3)

        safety = QLabel(
            "Originaldateien werden in diesem Sicherheitsstand niemals gelöscht, verschoben, umbenannt oder überschrieben."
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
        self.status_label.setText("Hinweis · Textsuche läuft …")
        self.activity_label.setText("Aktivität: Dateiliste wird vorbereitet")
        self.step_label.setText("Schritt: Dateien inventarisieren")
        self.eta_label.setText("Restzeit: wird ermittelt")
        self.progress_bar.setRange(0, 0)
        self.counter_label.setText("Dateien werden ermittelt …")
        self.scan_options = ScanOptions(
            exclude_python_project_dirs=self.exclude_python_box.isChecked(),
            excluded_extensions=self.scan_options.excluded_extensions,
        )
        self.search_worker = SearchWorker(job, self.database, self.scan_options)
        self.process_controller.connect_worker_controls(self.search_worker)
        self.search_worker.completed.connect(self._search_finished)
        self.search_worker.failed.connect(self._search_failed)
        self.search_worker.start()

    def _search_finished(
        self,
        job: SearchJob,
        job_id: int,
        hit_count: int,
        error_count: int,
    ) -> None:
        self.last_search_job_id = job_id
        self.results_model.set_job(job_id, hit_count)
        self.search_button.setEnabled(True)
        self._set_process_idle()
        if error_count:
            self.status_label.setText(
                f"Hinweis · Textsuche abgeschlossen · {error_count} Datei(en) übersprungen"
            )
        else:
            self.status_label.setText("OK · Textsuche abgeschlossen")
        self.activity_label.setText("Aktivität: Suche abgeschlossen")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.counter_label.setText(
            f"{job.scanned_files} Textdateien geprüft · {hit_count} Treffer · "
            f"{error_count} übersprungen"
        )
        self.result_info.setText(
            f"{hit_count} Treffer · {error_count} Lesefehler · SQLite-Seiten · "
            f"max. {self.results_model.page_size * self.results_model.max_pages} "
            "Zeilen im GUI-Puffer"
        )
        self.dashboard_process_value.setText(
            f"Fertig · {job.scanned_files} Dateien · {hit_count} Treffer · "
            f"{error_count} übersprungen"
        )
        self.nav.setCurrentRow(self.PAGE_RESULTS)

    def _search_failed(self, message: str) -> None:
        entry = record_error(self.base_dir / "logs", "textsuche", message)
        self.search_button.setEnabled(True)
        self._set_process_idle()
        self.status_label.setText("Fehler · Textsuche gestoppt")
        self.activity_label.setText("Aktivität: sicher gestoppt")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Suche gestoppt", f"Die Suche wurde sicher beendet.\n\n{message}\n\nLösung: {entry['solution']}")

    def _set_process_idle(self) -> None:
        """Kompatibilitätsbrücke für bestehende Abschluss- und Regressionstests."""
        self.process_controller.set_idle()

    def _choose_excluded_types(self) -> None:
        from app.gui.exclusion_dialog import ExclusionDialog
        dialog=ExclusionDialog(self.scan_options.excluded_extensions, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected=dialog.selected_extensions()
        self.scan_options=ScanOptions(
            exclude_python_project_dirs=self.exclude_python_box.isChecked(),
            excluded_extensions=frozenset(selected),
        )
        if selected:
            self.excluded_types_label.setText("Dateitypen ausgelassen: " + ", ".join(sorted(selected)))
        else:
            self.excluded_types_label.setText("Dateitypen: keine zusätzlichen Ausschlüsse")
        self._refresh_filter_summary()

    def _refresh_filter_summary(self) -> None:
        python_text = "Python-/Entwicklungsordner aktiv" if self.exclude_python_box.isChecked() else "Python-/Entwicklungsordner werden mit geprüft"
        extensions = sorted(self.scan_options.excluded_extensions)
        type_text = ", ".join(extensions) if extensions else "keine zusätzlichen Dateitypen"
        if hasattr(self, "duplicate_filter_info"):
            self.duplicate_filter_info.setText(f"Ausschlüsse: {python_text} · {type_text}")

    def _selected_result_path(self) -> Path | None:
        index = self.results.currentIndex()
        return self.results_model.path_at(index.row()) if index.isValid() else None

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
        marked=self.result_mark.isChecked()
        self.database.set_virtual_item(path, marked, self.result_note.text())
        self.results_model.set_marked(path,marked)
        self.status_label.setText("OK · Virtuelle Markierung gespeichert")

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
        self.status_label.setText("OK · Treffer virtuell zur Sammlung hinzugefügt")

    def _start_duplicate_scan(self) -> None:
        validation = validate_scan_root(self.selected_root)
        if not validation.ok:
            QMessageBox.information(self, validation.title, validation.message)
            return
        self.duplicate_start.setEnabled(False)
        self.status_label.setText("Hinweis · Duplikatprüfung läuft …")
        self.activity_label.setText("Aktivität: Dateiliste wird vorbereitet")
        self.step_label.setText("Schritt: Dateien inventarisieren")
        self.eta_label.setText("Restzeit: wird ermittelt")
        self.progress_bar.setRange(0, 0)
        self.duplicate_summary.setText("Dateigrößen werden gruppiert; nur Kandidaten werden vollständig gehasht.")
        self.scan_options = ScanOptions(
            exclude_python_project_dirs=self.exclude_python_box.isChecked(),
            excluded_extensions=self.scan_options.excluded_extensions,
        )
        self.duplicate_worker = DuplicateWorker(
            self.selected_root,
            self.database,
            self.scan_options,
        )
        self.process_controller.connect_worker_controls(self.duplicate_worker)
        self.duplicate_worker.completed.connect(self._duplicate_scan_finished)
        self.duplicate_worker.failed.connect(self._duplicate_scan_failed)
        self.duplicate_worker.start()

    def _duplicate_scan_finished(
        self,
        scanned: int,
        group_count: int,
        error_count: int,
    ) -> None:
        self._refresh_duplicate_view_from_database()
        self.duplicate_start.setEnabled(True)
        self._set_process_idle()
        duplicates = sum(item[3] for item in self.duplicate_groups_cache)
        if error_count:
            self.status_label.setText(
                f"Hinweis · Duplikatprüfung abgeschlossen · {error_count} Datei(en) übersprungen"
            )
        else:
            self.status_label.setText("OK · Duplikatprüfung abgeschlossen")
        self.activity_label.setText("Aktivität: Duplikatprüfung abgeschlossen")
        self.step_label.setText("Schritt: abgeschlossen")
        self.eta_label.setText("Restzeit: 0 s")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.counter_label.setText(
            f"{scanned} Dateien inventarisiert · {group_count} Gruppen · "
            f"{duplicates} Duplikatdateien · {error_count} übersprungen"
        )
        self.duplicate_summary.setText(
            f"{group_count} sichere Duplikatgruppen gefunden. "
            "Die Schnellprüfung dient nur als Vorfilter; jede angezeigte Gruppe "
            "wurde vollständig mit SHA-256 bestätigt."
        )
        self.dashboard_process_value.setText(
            f"Fertig · {scanned} Dateien · {group_count} Gruppen · "
            f"{error_count} übersprungen"
        )

    def _duplicate_scan_failed(self, message: str) -> None:
        entry = record_error(self.base_dir / "logs", "duplikatpruefung", message)
        self.duplicate_start.setEnabled(True)
        self._set_process_idle()
        self.status_label.setText("Fehler · Duplikatprüfung gestoppt")
        self.activity_label.setText("Aktivität: sicher gestoppt")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        QMessageBox.critical(
            self,
            "Duplikatprüfung gestoppt",
            f"Die Prüfung wurde sicher beendet.\n\n{message}\n\nLösung: {entry['solution']}",
        )

    def _refresh_duplicate_view_from_database(self) -> None:
        self.duplicate_groups_cache = self.database.duplicate_group_summaries()
        self._fill_duplicate_groups()

    def _fill_duplicate_groups(self) -> None:
        self.duplicate_group_list.clear()
        for index, (_group_id, _digest, size, members) in enumerate(
            self.duplicate_groups_cache,
            start=1,
        ):
            wasted = size * (members - 1)
            text = (
                f"Gruppe {index} · {members} Dateien · "
                f"{format_bytes(wasted)} mehrfach"
            )
            self.duplicate_group_list.addItem(text)
        if self.duplicate_groups_cache:
            self.duplicate_group_list.setCurrentRow(0)
        else:
            self.duplicate_members_model.set_group_id(None)

    def _show_duplicate_group(self, row: int) -> None:
        if row < 0 or row >= len(self.duplicate_groups_cache):
            self.duplicate_members_model.set_group_id(None)
            return
        group_id, digest, size, members = self.duplicate_groups_cache[row]
        self.duplicate_members_model.set_group_id(
            group_id,
            size=size,
            count=members,
        )
        self.duplicate_summary.setText(
            f"Gruppe {row + 1}: {members} vollständig identische Dateien · "
            f"je {format_bytes(size)} · SHA-256 {digest[:16]}…"
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
        self.status_label.setText("OK · Virtuelle Sammlung angelegt")

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
            self.collection_items_model.set_collection(None)

    def _current_collection_id(self) -> int | None:
        item = self.collection_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        return int(value) if value is not None else None

    def _show_collection(self, _row: int) -> None:
        collection_id = self._current_collection_id()
        if collection_id is None:
            self.collection_items_model.set_collection(None)
            return
        collection = next(
            (c for c in self.database.collections() if c.id == collection_id),
            None,
        )
        if collection is None:
            self.collection_items_model.set_collection(None)
            return
        count = self.database.collection_item_count(collection_id)
        suffix = f" · {collection.note}" if collection.note else ""
        self.collection_summary.setText(
            f"{collection.name} · {count} Einträge{suffix}"
        )
        self.collection_items_model.set_collection(collection_id)

    def _remove_selected_collection_item(self) -> None:
        collection_id = self._current_collection_id()
        index=self.collection_items_table.currentIndex()
        path=self.collection_items_model.path_at(index.row()) if index.isValid() else None
        if collection_id is None or path is None:
            QMessageBox.information(self, "Keine Auswahl", "Bitte einen Sammlungseintrag auswählen.")
            return
        self.database.remove_collection_item(collection_id,path)
        self._show_collection(self.collection_list.currentRow())
        self.status_label.setText("OK · Eintrag nur aus der virtuellen Sammlung entfernt")

