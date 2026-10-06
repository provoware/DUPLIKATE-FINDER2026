from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEvent, QMimeData, QObject, QPoint, QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QDrag
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
)

from app.gui.theme import ZOOM_STEPS, apply_accessible_theme
from app.settings import default_cpu_workers, detected_cpu_count
from app.startup.selftest import run_selftest

MIME_PATH = "application/x-provoware-path"


class UiEnhancements(QObject):
    def __init__(self, window, base_dir: Path, database, install_global_filter: bool = True) -> None:
        super().__init__(window)
        self.window = window
        self.base_dir = base_dir
        self.database = database
        self.drag_start: QPoint | None = None
        self.zoom = window.settings.zoom_percent
        self._configure_sorting()
        self._configure_drag_drop()
        self._add_dashboard_tools()
        self._adapt_to_screen()
        self.app = QApplication.instance()
        self.install_global_filter = install_global_filter
        if self.app is not None and self.install_global_filter:
            self.app.installEventFilter(self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_status_style)
        self.timer.start(300)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._autosave)
        self.autosave_timer.start(5 * 60 * 1000)

        self.refresh_from_settings()
        self._refresh_status_style()
        self._autosave_label("aktiv")

    def _configure_sorting(self) -> None:
        for table_name in ("results", "duplicate_members", "collection_items_table"):
            table = getattr(self.window, table_name, None)
            if isinstance(table, QTableWidget):
                table.setSortingEnabled(True)
                table.setAlternatingRowColors(True)
                table.setWordWrap(False)
                table.verticalHeader().setVisible(False)
                table.verticalHeader().setDefaultSectionSize(34)
                header = table.horizontalHeader()
                header.setSectionsClickable(True)
                header.setHighlightSections(True)
                header.setMinimumSectionSize(70)
                header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                table.setToolTip("Spaltenüberschrift anklicken, um die Liste zu sortieren.")

    def _configure_drag_drop(self) -> None:
        self.window.results.setDragEnabled(True)
        self.window.results.viewport().installEventFilter(self)
        self.window.collection_list.setAcceptDrops(True)
        self.window.collection_list.viewport().setAcceptDrops(True)
        self.window.collection_list.viewport().installEventFilter(self)
        self.window.collection_list.setToolTip(
            "Treffer aus der Ergebnisliste hier auf eine Sammlung ziehen."
        )

    def _add_dashboard_tools(self) -> None:
        page = self.window.pages.widget(self.window.PAGE_DASHBOARD)
        layout = page.layout()
        panel = QFrame()
        panel.setObjectName("diagnostic_dashboard")
        panel.setProperty("accentPanel", True)
        grid = QGridLayout(panel)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(5)

        screen = self.window.screen() or QApplication.primaryScreen()
        geometry = screen.availableGeometry() if screen else None
        screen_text = f"🖥 Bildschirm {geometry.width()}×{geometry.height()}" if geometry else "🖥 Bildschirm unbekannt"
        self.screen_info = QLabel(screen_text)
        self.screen_info.setToolTip("Automatisch erkannter nutzbarer Bildschirmbereich.")
        grid.addWidget(self.screen_info, 0, 0)

        self.zoom_combo = QComboBox()
        self.zoom_combo.setObjectName("zoom_selector")
        for value in ZOOM_STEPS:
            self.zoom_combo.addItem(f"Schrift {value} %", value)
        self.zoom_combo.currentIndexChanged.connect(self._zoom_from_combo)
        self.zoom_combo.setToolTip("Schrift-/Seitenzoom. Alternativ: Strg + Mausrad.")
        grid.addWidget(self.zoom_combo, 0, 1)

        self.size_combo = QComboBox()
        self.size_combo.setObjectName("size_selector")
        self.size_combo.addItem("Fenster: automatisch", None)
        for width, height in ((800, 600), (1024, 768), (1280, 800)):
            self.size_combo.addItem(f"Fenster {width}×{height}", (width, height))
        self.size_combo.currentIndexChanged.connect(self._size_from_combo)
        self.size_combo.setToolTip("Fenstergröße ohne Zahleneingabe auswählen.")
        grid.addWidget(self.size_combo, 0, 2)

        self.cpu_info = QLabel(f"🧠 CPU: {detected_cpu_count()} Kerne erkannt")
        self.cpu_info.setToolTip("Erkannte logische CPU-Kerne. Der Begrenzer betrifft die parallele Duplikatprüfung.")
        grid.addWidget(self.cpu_info, 1, 0)

        self.cpu_combo = QComboBox()
        self.cpu_combo.setObjectName("cpu_core_limit")
        cpu = detected_cpu_count()
        auto = default_cpu_workers()
        self.cpu_combo.addItem(f"CPU automatisch · {auto} Kerne", 0)
        if cpu <= 16:
            values = range(1, cpu + 1)
        else:
            values = sorted({1, 2, 4, 6, 8, 12, 16, max(1, cpu // 2), cpu})
        for value in values:
            self.cpu_combo.addItem(f"Maximal {value} Kern" + ("" if value == 1 else "e"), value)
        self.cpu_combo.currentIndexChanged.connect(self._cpu_changed)
        self.cpu_combo.setToolTip(
            "Begrenzt die gleichzeitig laufenden SHA-256-Prüfungen. Weniger Kerne = ruhigerer Rechner."
        )
        grid.addWidget(self.cpu_combo, 1, 1)

        filters = QPushButton("⚙ Prüfoptionen")
        filters.setObjectName("dashboard_filter_options")
        filters.clicked.connect(self.window._open_scan_options)
        grid.addWidget(filters, 1, 2)

        self.selftest_button = QPushButton("🩺 Selbsttest")
        self.selftest_button.setObjectName("dashboard_selftest")
        self.selftest_button.clicked.connect(self._show_selftest)
        grid.addWidget(self.selftest_button, 2, 0)

        logs_button = QPushButton("📂 Protokolle")
        logs_button.setObjectName("dashboard_logs")
        logs_button.setToolTip(str(self.base_dir / "logs"))
        logs_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.base_dir / "logs")))
        )
        grid.addWidget(logs_button, 2, 1)

        self.autosave_info = QLabel()
        self.autosave_info.setObjectName("autosave_info")
        self.autosave_info.setToolTip(
            "Einstellungen werden alle fünf Minuten zusätzlich gesichert. Virtuelle Änderungen landen sofort in SQLite."
        )
        grid.addWidget(self.autosave_info, 2, 2)

        export_button = QPushButton("📤 Zustand exportieren")
        export_button.setObjectName("dashboard_export")
        export_button.clicked.connect(self.window.export_provoware_state)
        export_button.setToolTip("Exportiert nur PROVOWARE-Einstellungen, Markierungen und virtuelle Sammlungen.")
        grid.addWidget(export_button, 3, 0)

        import_button = QPushButton("📥 Zustand importieren")
        import_button.setObjectName("dashboard_import")
        import_button.clicked.connect(self.window.import_provoware_state)
        import_button.setToolTip("Importiert nur PROVOWARE-Zustände. Originaldateien werden nicht verändert.")
        grid.addWidget(import_button, 3, 1)

        save_now = QPushButton("💾 Jetzt speichern")
        save_now.setObjectName("dashboard_save_now")
        save_now.clicked.connect(self._autosave)
        grid.addWidget(save_now, 3, 2)

        layout.insertWidget(max(1, layout.count() - 1), panel)

    def _cpu_changed(self) -> None:
        value = self.cpu_combo.currentData()
        if isinstance(value, int):
            self.window.settings.cpu_workers = value
            self.window.save_settings()
            self.window._update_filter_summaries()
            self.window.status_label.setText(
                f"🟢 CPU-Begrenzung: maximal {self.window.settings.resolved_cpu_workers()} Kerne"
            )

    def refresh_from_settings(self) -> None:
        zoom_index = self.zoom_combo.findData(self.window.settings.zoom_percent)
        if zoom_index < 0:
            zoom_index = self.zoom_combo.findData(100)
        self.zoom_combo.blockSignals(True)
        self.zoom_combo.setCurrentIndex(max(0, zoom_index))
        self.zoom_combo.blockSignals(False)
        self._apply_zoom(int(self.zoom_combo.currentData() or 100))

        cpu_index = self.cpu_combo.findData(self.window.settings.cpu_workers)
        if cpu_index < 0:
            cpu_index = self.cpu_combo.findData(0)
        self.cpu_combo.blockSignals(True)
        self.cpu_combo.setCurrentIndex(max(0, cpu_index))
        self.cpu_combo.blockSignals(False)

    def _adapt_to_screen(self) -> None:
        screen = self.window.screen() or QApplication.primaryScreen()
        if screen is None:
            self.window.resize(800, 600)
            return
        area = screen.availableGeometry()
        saved_w = self.window.settings.window_width
        saved_h = self.window.settings.window_height
        width = min(max(800, saved_w), max(640, area.width()))
        height = min(max(600, saved_h), max(480, area.height()))
        self.window.resize(width, height)
        frame = self.window.frameGeometry()
        frame.moveCenter(area.center())
        self.window.move(frame.topLeft())

    def _size_from_combo(self) -> None:
        value = self.size_combo.currentData()
        if value is None:
            self._adapt_to_screen()
            return
        width, height = value
        screen = self.window.screen() or QApplication.primaryScreen()
        if screen:
            area = screen.availableGeometry()
            width = min(width, area.width())
            height = min(height, area.height())
        self.window.resize(width, height)
        self.window.save_settings()
        self.window.status_label.setText(f"🟢 Fenstergröße {width} × {height}")

    def _zoom_from_combo(self) -> None:
        value = self.zoom_combo.currentData()
        if isinstance(value, int):
            self._apply_zoom(value)

    def _apply_zoom(self, value: int) -> None:
        self.zoom = value
        self.window.settings.zoom_percent = value
        app = QApplication.instance()
        if app is None:
            return
        apply_accessible_theme(app, value)
        for label in self.window.findChildren(QLabel):
            if label.property("heading"):
                font = label.font()
                font.setBold(True)
                font.setPointSize(max(12, round(14 * value / 100)))
                label.setFont(font)
        index = self.zoom_combo.findData(value)
        if index >= 0 and self.zoom_combo.currentIndex() != index:
            self.zoom_combo.blockSignals(True)
            self.zoom_combo.setCurrentIndex(index)
            self.zoom_combo.blockSignals(False)
        self.window.save_settings()
        self.window.status_label.setText(f"🟢 Seitenzoom {value} %")

    def _show_selftest(self) -> None:
        checks = run_selftest(self.base_dir, require_gui=True)
        bad = [c for c in checks if not c.ok]
        text = "\n".join(("✅ " if c.ok else "❌ ") + f"{c.name}: {c.detail}" for c in checks)
        if bad:
            QMessageBox.warning(self.window, "Selbsttest – Prüfung nötig", text)
        else:
            QMessageBox.information(self.window, "Selbsttest – alles bereit", text)

    def _autosave_label(self, state: str) -> None:
        now = datetime.now().strftime("%H:%M")
        self.autosave_info.setText(f"💾 Autospeichern 5 min · {state} · {now}")

    def _autosave(self) -> None:
        try:
            self.window.save_settings()
        except OSError:
            self._autosave_label("Fehler")
            return
        self._autosave_label("gesichert")

    def _refresh_status_style(self) -> None:
        text = self.window.status_label.text()
        if text.startswith("🔴"):
            style = "font-weight:800; color:#ffdfe7; background:#421622; padding:5px; border-radius:5px;"
        elif text.startswith("🟡"):
            style = "font-weight:800; color:#fff3bd; background:#3b2f0f; padding:5px; border-radius:5px;"
        else:
            style = "font-weight:800; color:#dffff0; background:#123527; padding:5px; border-radius:5px;"
        if self.window.status_label.styleSheet() != style:
            self.window.status_label.setStyleSheet(style)

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.Wheel and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            current = min(range(len(ZOOM_STEPS)), key=lambda i: abs(ZOOM_STEPS[i] - self.zoom))
            target = max(0, min(len(ZOOM_STEPS) - 1, current + (1 if delta > 0 else -1)))
            self._apply_zoom(ZOOM_STEPS[target])
            return True

        results_view = self.window.results.viewport()
        if obj is results_view:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self.drag_start = event.position().toPoint()
            elif (
                event.type() == QEvent.Type.MouseMove
                and event.buttons() & Qt.MouseButton.LeftButton
                and self.drag_start is not None
            ):
                distance = (event.position().toPoint() - self.drag_start).manhattanLength()
                if distance >= QApplication.startDragDistance():
                    row = self.window.results.currentRow()
                    item = self.window.results.item(row, 2) if row >= 0 else None
                    if item:
                        mime = QMimeData()
                        mime.setData(MIME_PATH, item.text().encode("utf-8"))
                        drag = QDrag(self.window.results)
                        drag.setMimeData(mime)
                        drag.exec(Qt.DropAction.CopyAction)
                        return True

        target_view = self.window.collection_list.viewport()
        if obj is target_view:
            if (
                event.type() in (QEvent.Type.DragEnter, QEvent.Type.DragMove)
                and event.mimeData().hasFormat(MIME_PATH)
            ):
                event.acceptProposedAction()
                return True
            if event.type() == QEvent.Type.Drop and event.mimeData().hasFormat(MIME_PATH):
                item = self.window.collection_list.itemAt(event.position().toPoint())
                if item is None:
                    return True
                collection_id = item.data(Qt.ItemDataRole.UserRole)
                raw = bytes(event.mimeData().data(MIME_PATH)).decode("utf-8", errors="replace")
                path = Path(raw)
                if collection_id is not None and path.exists():
                    self.database.add_collection_item(int(collection_id), path)
                    self.window._refresh_collections(select_id=int(collection_id))
                    self.window.status_label.setText("🟢 Treffer per Drag & Drop virtuell einsortiert")
                    event.acceptProposedAction()
                return True
        return super().eventFilter(obj, event)

    def dispose(self) -> None:
        self.timer.stop()
        self.autosave_timer.stop()
        try:
            self.window.save_settings()
        except OSError:
            pass
        if self.app is not None and self.install_global_filter:
            self.app.removeEventFilter(self)
        try:
            self.window.results.viewport().removeEventFilter(self)
            self.window.collection_list.viewport().removeEventFilter(self)
        except RuntimeError:
            pass
