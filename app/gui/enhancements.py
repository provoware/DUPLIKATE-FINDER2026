from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QMimeData, QObject, QPoint, QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QDrag
from PySide6.QtWidgets import QApplication, QComboBox, QFileDialog, QFrame, QGridLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget

from app.gui.theme import ZOOM_STEPS, apply_accessible_theme
from app.startup.selftest import run_selftest
from app.core.scanner import ScanOptions
from app.cpu_limit import CpuLimiter
from app.settings_store import SettingsStore
from app.state_portability import export_state, import_state

MIME_PATH = "application/x-provoware-path"


class UiEnhancements(QObject):
    def __init__(self, window, base_dir: Path, database, install_global_filter: bool = True) -> None:
        super().__init__(window)
        self.window = window
        self.base_dir = base_dir
        self.database = database
        self.drag_start: QPoint | None = None
        self.store = SettingsStore(base_dir / "config" / "benutzer-einstellungen.json")
        self.settings = self.store.load()
        self.cpu_limiter = CpuLimiter()
        self.zoom = int(self.settings.get("zoom_percent", 100))
        self._configure_sorting()
        self._configure_drag_drop()
        self._add_dashboard_tools()
        self._adapt_to_screen()
        self._apply_loaded_settings()
        self.app = QApplication.instance()
        self.install_global_filter = install_global_filter
        if self.app is not None and self.install_global_filter:
            self.app.installEventFilter(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_status_style)
        self.timer.start(300)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._autosave)
        self.autosave_timer.start(300_000)
        self._refresh_status_style()

    def _configure_sorting(self) -> None:
        for table_name in ("results", "duplicate_members", "collection_items_table"):
            table = getattr(self.window, table_name, None)
            if isinstance(table, QTableWidget):
                table.setSortingEnabled(True)
                table.horizontalHeader().setSectionsClickable(True)
                table.horizontalHeader().setSortIndicatorShown(True)
                table.setAlternatingRowColors(True)
                table.setShowGrid(False)
                table.setWordWrap(False)
                table.verticalHeader().setVisible(False)
                table.verticalHeader().setDefaultSectionSize(34)
                table.setToolTip("Spaltenüberschrift anklicken, um die Liste zu sortieren.")
        if isinstance(getattr(self.window, "results", None), QTableWidget):
            header=self.window.results.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            self.window.results.setColumnWidth(2, 300)
        for list_name in ("nav", "duplicate_group_list", "collection_list"):
            view=getattr(self.window, list_name, None)
            if view is not None:
                view.setAlternatingRowColors(True)

    def _configure_drag_drop(self) -> None:
        self.window.results.setDragEnabled(True)
        self.window.results.viewport().installEventFilter(self)
        self.window.collection_list.setAcceptDrops(True)
        self.window.collection_list.viewport().setAcceptDrops(True)
        self.window.collection_list.viewport().installEventFilter(self)
        self.window.collection_list.setToolTip("Treffer aus der Ergebnisliste hier auf eine Sammlung ziehen.")

    def _add_dashboard_tools(self) -> None:
        page = self.window.pages.widget(self.window.PAGE_DASHBOARD)
        layout = page.layout()
        panel = QFrame()
        panel.setObjectName("diagnostic_dashboard")
        panel.setProperty("card", True)
        grid = QGridLayout(panel)
        grid.setContentsMargins(6, 4, 6, 4)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)

        screen = self.window.screen() or QApplication.primaryScreen()
        geometry = screen.availableGeometry() if screen else None
        screen_text = f"🖥 {geometry.width()}×{geometry.height()}" if geometry else "🖥 unbekannt"
        self.screen_info = QLabel(screen_text)
        self.screen_info.setToolTip("Automatisch erkannter nutzbarer Bildschirmbereich.")
        grid.addWidget(self.screen_info, 0, 0)

        self.zoom_combo = QComboBox()
        self.zoom_combo.setObjectName("zoom_selector")
        for value in ZOOM_STEPS:
            self.zoom_combo.addItem(f"{value} %", value)
        self.zoom_combo.setCurrentText("100 %")
        self.zoom_combo.currentIndexChanged.connect(self._zoom_from_combo)
        self.zoom_combo.setToolTip("Schrift-/Seitenzoom. Alternativ: Strg + Mausrad.")
        grid.addWidget(self.zoom_combo, 0, 1)

        self.size_combo = QComboBox()
        self.size_combo.setObjectName("size_selector")
        self.size_combo.addItem("Auto-Größe", None)
        for width, height in ((800, 600), (1024, 768), (1280, 800)):
            self.size_combo.addItem(f"{width}×{height}", (width, height))
        self.size_combo.currentIndexChanged.connect(self._size_from_combo)
        self.size_combo.setToolTip("Fenstergröße ohne Zahleneingabe auswählen.")
        grid.addWidget(self.size_combo, 0, 2)

        self.selftest_button = QPushButton("🩺 Selbsttest")
        self.selftest_button.setObjectName("dashboard_selftest")
        self.selftest_button.clicked.connect(self._show_selftest)
        grid.addWidget(self.selftest_button, 1, 0, 1, 2)

        logs_button = QPushButton("📂 Protokolle")
        logs_button.setObjectName("dashboard_logs")
        logs_button.setToolTip(str(self.base_dir / "logs"))
        logs_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.base_dir / "logs"))))
        grid.addWidget(logs_button, 1, 2)

        cpu_label=QLabel("CPU-Kerne:")
        cpu_label.setToolTip("Begrenzt nur PROVOWARE, nicht den ganzen Rechner.")
        self.cpu_combo=QComboBox()
        self.cpu_combo.setObjectName("cpu_limiter")
        self.cpu_combo.addItem(f"Automatisch · alle {self.cpu_limiter.available}", 0)
        for cores in range(1, self.cpu_limiter.available + 1):
            self.cpu_combo.addItem(f"{cores} Kern" + ("" if cores == 1 else "e"), cores)
        self.cpu_combo.currentIndexChanged.connect(self._cpu_changed)
        self.cpu_combo.setToolTip("Weniger Kerne lassen mehr Rechenleistung für andere Programme frei.")
        grid.addWidget(cpu_label, 2, 0)
        grid.addWidget(self.cpu_combo, 2, 1, 1, 2)

        export_button=QPushButton("⬆ Zustand exportieren")
        export_button.setObjectName("dashboard_export")
        export_button.setToolTip("Exportiert Einstellungen, Markierungen und virtuelle Sammlungen als JSON. Originaldateien werden nicht kopiert.")
        export_button.clicked.connect(self._export_state)
        import_button=QPushButton("⬇ Zustand importieren")
        import_button.setObjectName("dashboard_import")
        import_button.setToolTip("Importiert nur PROVOWARE-Einstellungen und virtuelle Organisation nach Vorprüfung.")
        import_button.clicked.connect(self._import_state)
        grid.addWidget(export_button, 3, 0, 1, 2)
        grid.addWidget(import_button, 3, 2)

        autosave=QLabel("💾 Autosave: alle 5 Minuten · virtuelle Änderungen werden zusätzlich sofort gespeichert")
        autosave.setObjectName("autosave_info")
        autosave.setWordWrap(True)
        grid.addWidget(autosave, 4, 0, 1, 3)

        layout.insertWidget(max(1, layout.count() - 1), panel)

    def _apply_loaded_settings(self) -> None:
        zoom=int(self.settings.get("zoom_percent",100))
        if zoom in ZOOM_STEPS:
            self._apply_zoom(zoom)
        width=int(self.settings.get("window_width",1280))
        height=int(self.settings.get("window_height",800))
        screen=self.window.screen() or QApplication.primaryScreen()
        if screen:
            area=screen.availableGeometry()
            width=min(max(640,width),area.width())
            height=min(max(480,height),area.height())
        self.window.resize(width,height)

        extensions=frozenset(str(x) for x in self.settings.get("excluded_extensions",[]))
        exclude_python=bool(self.settings.get("exclude_python_project_dirs",True))
        self.window.scan_options=ScanOptions(
            exclude_python_project_dirs=exclude_python,
            excluded_extensions=extensions,
        )
        self.window.exclude_python_box.setChecked(exclude_python)
        if extensions:
            self.window.excluded_types_label.setText("Dateitypen ausgelassen: " + ", ".join(sorted(extensions)))

        wanted=int(self.settings.get("cpu_cores",0))
        index=self.cpu_combo.findData(wanted)
        if index >= 0:
            self.cpu_combo.setCurrentIndex(index)
        self.cpu_limiter.apply(wanted)

    def _collect_settings(self) -> dict:
        size=self.window.size()
        return {
            "schema_version":"1.0.0",
            "zoom_percent":self.zoom,
            "window_width":size.width(),
            "window_height":size.height(),
            "cpu_cores":int(self.cpu_combo.currentData() or 0),
            "exclude_python_project_dirs":self.window.exclude_python_box.isChecked(),
            "excluded_extensions":sorted(self.window.scan_options.excluded_extensions),
        }

    def _autosave(self) -> None:
        self.settings=self._collect_settings()
        self.store.save(self.settings)
        if self.window._active_worker() is None:
            self.window.status_label.setText("🟢 Autosave gespeichert")

    def _cpu_changed(self) -> None:
        requested=int(self.cpu_combo.currentData() or 0)
        active=self.cpu_limiter.apply(requested)
        self.settings["cpu_cores"]=requested
        self.store.save(self._collect_settings())
        label="alle verfügbaren" if requested == 0 else str(active)
        self.window.status_label.setText(f"🟢 CPU-Begrenzung: {label} Kern(e) für PROVOWARE")

    def _export_state(self) -> None:
        default=self.base_dir/"exports"/"PROVOWARE-Zustand.json"
        path,_=QFileDialog.getSaveFileName(
            self.window,"PROVOWARE-Zustand exportieren",str(default),"JSON-Datei (*.json)"
        )
        if not path:
            return
        target=Path(path)
        try:
            payload=export_state(self.database,target,self._collect_settings())
        except Exception as exc:
            QMessageBox.critical(self.window,"Export fehlgeschlagen",f"Der Export wurde sicher gestoppt.\n\n{exc}")
            return
        self.window.status_label.setText("🟢 Export geprüft und gespeichert")
        QMessageBox.information(
            self.window,"Export abgeschlossen",
            f"Virtuelle Organisation und Einstellungen wurden exportiert.\n\n{target}\n\nOriginaldateien wurden nicht kopiert."
        )

    def _import_state(self) -> None:
        path,_=QFileDialog.getOpenFileName(
            self.window,"PROVOWARE-Zustand importieren",str(self.base_dir/"exports"),"JSON-Datei (*.json)"
        )
        if not path:
            return
        answer=QMessageBox.question(
            self.window,"Import vorprüfen und übernehmen",
            "Importiert werden nur Einstellungen, Markierungen und virtuelle Sammlungen. "
            "Originaldateien werden nicht verändert.\n\nFortfahren?"
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            payload=import_state(self.database,Path(path))
        except Exception as exc:
            QMessageBox.critical(self.window,"Import abgelehnt",f"Die Datei wurde nicht übernommen.\n\n{exc}")
            return
        imported_settings=payload.get("settings")
        if isinstance(imported_settings,dict):
            self.settings.update(imported_settings)
            self.store.save(self.settings)
            self._apply_loaded_settings()
        self.window._refresh_collections()
        self.window.status_label.setText("🟢 Import vor- und nachgeprüft")
        QMessageBox.information(self.window,"Import abgeschlossen","Der virtuelle Zustand wurde sicher übernommen.")

    def _adapt_to_screen(self) -> None:
        screen = self.window.screen() or QApplication.primaryScreen()
        if screen is None:
            self.window.resize(800, 600)
            return
        area = screen.availableGeometry()
        width = min(1280, max(800, int(area.width() * 0.82)))
        height = min(900, max(600, int(area.height() * 0.82)))
        width = min(width, max(640, area.width()))
        height = min(height, max(480, area.height()))
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
        self.window.status_label.setText(f"🟢 Fenstergröße {width} × {height}")
        self.store.save(self._collect_settings())

    def _zoom_from_combo(self) -> None:
        value = self.zoom_combo.currentData()
        if isinstance(value, int):
            self._apply_zoom(value)

    def _apply_zoom(self, value: int) -> None:
        self.zoom = value
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
        self.window.status_label.setText(f"🟢 Seitenzoom {value} %")
        if hasattr(self, "cpu_combo"):
            self.store.save(self._collect_settings())

    def _show_selftest(self) -> None:
        checks = run_selftest(self.base_dir, require_gui=True)
        bad = [c for c in checks if not c.ok]
        text = "\n".join(("✅ " if c.ok else "❌ ") + f"{c.name}: {c.detail}" for c in checks)
        if bad:
            QMessageBox.warning(self.window, "Selbsttest – Prüfung nötig", text)
        else:
            QMessageBox.information(self.window, "Selbsttest – alles bereit", text)

    def _refresh_status_style(self) -> None:
        text = self.window.status_label.text()
        if text.startswith("🔴"):
            style = "font-weight:800; color:#a40000; background:#ffe9e9; padding:5px;"
        elif text.startswith("🟡"):
            style = "font-weight:800; color:#6b4b00; background:#fff4c2; padding:5px;"
        else:
            style = "font-weight:800; color:#075b2a; background:#e7f8ed; padding:5px;"
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
            elif event.type() == QEvent.Type.MouseMove and event.buttons() & Qt.MouseButton.LeftButton and self.drag_start is not None:
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
            if event.type() in (QEvent.Type.DragEnter, QEvent.Type.DragMove) and event.mimeData().hasFormat(MIME_PATH):
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
        self._autosave()
        self.autosave_timer.stop()
        self.timer.stop()
        if self.app is not None and self.install_global_filter:
            self.app.removeEventFilter(self)
        try:
            self.window.results.viewport().removeEventFilter(self)
            self.window.collection_list.viewport().removeEventFilter(self)
        except RuntimeError:
            pass
