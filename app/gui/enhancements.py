from __future__ import annotations

from pathlib import Path
import sqlite3
from datetime import datetime
from math import ceil

from PySide6.QtCore import QEvent, QMimeData, QObject, QPoint, QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QDrag
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QFrame, QGridLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QTableView, QVBoxLayout

from app.gui.theme import ZOOM_STEPS, apply_accessible_theme
from app.startup.selftest import run_selftest
from app.core.scanner import ScanOptions
from app.cpu_limit import CpuLimiter
from app.settings_store import SettingsStore
from app.gui.resource_dashboard_controller import ResourceDashboardController
from app.gui.state_portability_controller import StatePortabilityController
from app.gui.status_feedback import set_status
from app.gui.error_feedback import report_ui_error

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
        self.resource_controller = ResourceDashboardController(self.window)
        self.portability_controller = StatePortabilityController(
            self.window,
            self.base_dir,
            self.database,
            self.store,
            self.settings,
            self._collect_settings,
            self._apply_loaded_settings,
        )
        self._configure_sorting()
        self._configure_drag_drop()
        self._add_dashboard_tools()
        self._adapt_to_screen()
        self._apply_loaded_settings()
        self.app = QApplication.instance()
        self.install_global_filter = install_global_filter
        if self.app is not None and self.install_global_filter:
            self.app.installEventFilter(self)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._autosave)
        self.autosave_timer.start(300_000)
        self.resource_timer = QTimer(self)
        self.resource_timer.timeout.connect(self.resource_controller.refresh)
        self.resource_timer.start(1_000)
        self.resource_controller.refresh()

    def _configure_sorting(self) -> None:
        for table_name in ("results", "duplicate_members", "collection_items_table"):
            table = getattr(self.window, table_name, None)
            if isinstance(table, QTableView):
                table.setSortingEnabled(True)
                table.horizontalHeader().setSectionsClickable(True)
                table.horizontalHeader().setSortIndicatorShown(True)
                table.setAlternatingRowColors(True)
                table.setShowGrid(False)
                table.setWordWrap(False)
                table.verticalHeader().setVisible(False)
                table.verticalHeader().setDefaultSectionSize(34)
                table.setToolTip(
                    "Virtuelle Liste: nur sichtbare Zeilen werden dargestellt. "
                    "Spaltenüberschrift anklicken, um zu sortieren."
                )
        if isinstance(getattr(self.window, "results", None), QTableView):
            header=self.window.results.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            self.window.results.setColumnWidth(2, 300)
        if isinstance(getattr(self.window, "duplicate_members", None), QTableView):
            header=self.window.duplicate_members.horizontalHeader()
            header.setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2,QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3,QHeaderView.ResizeMode.ResizeToContents)
        if isinstance(getattr(self.window, "collection_items_table", None), QTableView):
            header=self.window.collection_items_table.horizontalHeader()
            header.setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
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
        panel.setProperty("section", True)
        grid = QGridLayout(panel)
        grid.setContentsMargins(5, 3, 5, 3)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(2)

        screen = self.window.screen() or QApplication.primaryScreen()
        geometry = screen.availableGeometry() if screen else None
        screen_text = f"Bildschirm {geometry.width()} × {geometry.height()}" if geometry else "Bildschirm unbekannt"
        self.screen_info = QLabel(screen_text)
        self.screen_info.setToolTip("Automatisch erkannter nutzbarer Bildschirmbereich.")
        grid.addWidget(self.screen_info, 0, 0)

        self.zoom_combo = QComboBox()
        self.zoom_combo.setObjectName("zoom_selector")
        self.zoom_combo.setAccessibleName("Schrift- und Seitenzoom")
        for value in ZOOM_STEPS:
            self.zoom_combo.addItem(f"Zoom {value} %", value)
        self.zoom_combo.setCurrentText("Zoom 100 %")
        self.zoom_combo.currentIndexChanged.connect(self._zoom_from_combo)
        self.zoom_combo.setToolTip("Schrift-/Seitenzoom. Alternativ: Strg + Mausrad.")
        grid.addWidget(self.zoom_combo, 0, 1)

        self.size_combo = QComboBox()
        self.size_combo.setObjectName("size_selector")
        self.size_combo.setAccessibleName("Fenstergröße")
        self.size_combo.addItem("Fenster: Auto", None)
        for width, height in ((800, 600), (1024, 768), (1280, 800)):
            self.size_combo.addItem(f"Fenster {width}×{height}", (width, height))
        self.size_combo.currentIndexChanged.connect(self._size_from_combo)
        self.size_combo.setToolTip("Fenstergröße ohne Zahleneingabe auswählen.")
        grid.addWidget(self.size_combo, 0, 2)

        self.cpu_combo=QComboBox()
        self.cpu_combo.setObjectName("cpu_limiter")
        self.cpu_combo.setAccessibleName("Rechenleistung für dieses Programm")
        available=self.cpu_limiter.available
        self.cpu_combo.addItem(f"CPU: 100 % · {available}", 0)
        choices=[]
        for percent in (25,50,75):
            cores=max(1,min(available,ceil(available*percent/100)))
            if cores not in [value for _label,value in choices]:
                choices.append((f"CPU: {percent} % · {cores}",cores))
        for label,cores in choices:
            self.cpu_combo.addItem(label,cores)
        self.cpu_combo.currentIndexChanged.connect(self._cpu_changed)
        self.cpu_combo.setToolTip("Begrenzt nur PROVOWARE. Weniger Kerne lassen mehr Rechenleistung für andere Programme frei.")
        grid.addWidget(self.cpu_combo, 1, 0)

        tools_button=QPushButton("Werkzeuge")
        tools_button.setObjectName("dashboard_tools")
        tools_button.setProperty("compact", True)
        tools_button.setToolTip("Selbsttest, Protokolle, Export und Import öffnen.")
        tools_button.clicked.connect(self._open_tools_dialog)
        grid.addWidget(tools_button, 1, 1)

        self.autosave_info=QLabel("Autosicherung: alle 5 Minuten")
        self.autosave_info.setObjectName("autosave_info")
        self.autosave_info.setAccessibleName("Status der automatischen Sicherung")
        self.autosave_info.setToolTip("Fenster-, Zoom-, CPU- und Filtereinstellungen werden alle fünf Minuten gesichert. Markierungen und Sammlungen werden sofort in der lokalen Datenbank gespeichert.")
        if self.store.last_load_error:
            self.autosave_info.setText("Einstellungen zurückgesetzt")
            backup = str(self.store.corrupt_backup) if self.store.corrupt_backup else "keine Sicherung möglich"
            self.autosave_info.setToolTip(
                "Die Einstellungsdatei war beschädigt. Standardwerte wurden geladen. "
                f"Sicherung: {backup}. Fehler: {self.store.last_load_error}"
            )
        grid.addWidget(self.autosave_info, 1, 2)

        layout.insertWidget(max(1, layout.count() - 1), panel)

    def _open_tools_dialog(self) -> None:
        dialog=QDialog(self.window)
        dialog.setWindowTitle("Werkzeuge & Sicherung")
        dialog.setMinimumWidth(440)
        layout=QVBoxLayout(dialog)
        info=QLabel(
            "Diagnose und Sicherung betreffen nur PROVOWARE. "
            "Originaldateien werden weder verändert noch in den Export kopiert."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        selftest=QPushButton("Selbsttest ausführen")
        selftest.setObjectName("tools_selftest")
        selftest.clicked.connect(self._show_selftest)
        layout.addWidget(selftest)

        logs=QPushButton("Protokollordner öffnen")
        logs.setObjectName("tools_logs")
        logs.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.base_dir / "logs"))))
        layout.addWidget(logs)

        export_button=QPushButton("Zustand exportieren")
        export_button.setObjectName("dashboard_export")
        export_button.setToolTip("Exportiert Einstellungen, Markierungen und virtuelle Sammlungen als JSON.")
        export_button.clicked.connect(self.portability_controller.export)
        layout.addWidget(export_button)

        import_button=QPushButton("Zustand importieren")
        import_button.setObjectName("dashboard_import")
        import_button.setToolTip("Prüft und importiert nur PROVOWARE-Einstellungen und virtuelle Organisation.")
        import_button.clicked.connect(self.portability_controller.import_state)
        layout.addWidget(import_button)

        close=QPushButton("Schließen")
        close.setProperty("compact", True)
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()

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

    def _save_settings(self, *, show_dialog: bool) -> bool:
        try:
            self.store.save(self._collect_settings())
        except OSError as exc:
            report_ui_error(
                self.window,
                area="einstellungen",
                title="Einstellungen nicht gespeichert",
                lead="Die lokalen Programmeinstellungen konnten nicht geschrieben werden.",
                error=exc,
                show_dialog=show_dialog,
            )
            if hasattr(self, "autosave_info"):
                self.autosave_info.setText("Autosicherung fehlgeschlagen")
            return False
        return True

    def _autosave(self) -> None:
        self.settings = self._collect_settings()
        if not self._save_settings(show_dialog=False):
            return
        stamp = datetime.now().strftime("%H:%M")
        if hasattr(self, "autosave_info"):
            self.autosave_info.setText(f"Gesichert um {stamp}")
        if self.window._active_worker() is None:
            set_status(
                self.window.status_label,
                "OK · Einstellungen automatisch gesichert",
                "ok",
            )

    def _cpu_changed(self) -> None:
        requested=int(self.cpu_combo.currentData() or 0)
        active=self.cpu_limiter.apply(requested)
        self.settings["cpu_cores"] = requested
        self._save_settings(show_dialog=True)
        label = "alle verfügbaren" if requested == 0 else str(active)
        set_status(self.window.status_label, f"OK · CPU-Begrenzung: {label} Kern(e) für PROVOWARE", "ok")

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
        set_status(
            self.window.status_label,
            f"OK · Fenstergröße {width} × {height}",
            "ok",
        )
        self._save_settings(show_dialog=True)

    def _zoom_from_combo(self) -> None:
        value = self.zoom_combo.currentData()
        if isinstance(value, int):
            self._apply_zoom(value)

    def _apply_zoom(self, value: int) -> None:
        self.zoom = value
        self.window.setProperty("uiZoom", value)
        self.window._update_feature_layout()
        self.window._update_dashboard_card_layout()
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
            elif label.property("cardTitle"):
                font=label.font()
                font.setBold(True)
                font.setPointSize(max(11,round(8*value/100)))
                label.setFont(font)
            elif label.property("cardValue"):
                font=label.font()
                font.setBold(True)
                font.setPointSize(max(13,round(8*value/100)))
                label.setFont(font)
        index = self.zoom_combo.findData(value)
        if index >= 0 and self.zoom_combo.currentIndex() != index:
            self.zoom_combo.blockSignals(True)
            self.zoom_combo.setCurrentIndex(index)
            self.zoom_combo.blockSignals(False)
        set_status(self.window.status_label, f"OK · Seitenzoom {value} %", "ok")
        if hasattr(self, "cpu_combo"):
            self._save_settings(show_dialog=True)

    def _show_selftest(self) -> None:
        checks = run_selftest(self.base_dir, require_gui=True)
        bad = [c for c in checks if not c.ok]
        text = "\n".join(("OK · " if c.ok else "FEHLER · ") + f"{c.name}: {c.detail}" for c in checks)
        if bad:
            QMessageBox.warning(self.window, "Selbsttest – Prüfung nötig", text)
        else:
            QMessageBox.information(self.window, "Selbsttest – alles bereit", text)

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
                    index=self.window.results.currentIndex()
                    path=self.window.results_model.path_at(index.row()) if index.isValid() else None
                    if path is not None:
                        mime = QMimeData()
                        mime.setData(MIME_PATH, str(path).encode("utf-8"))
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
                    try:
                        self.database.add_collection_item(int(collection_id), path)
                        self.window._refresh_collections(select_id=int(collection_id))
                    except sqlite3.Error as exc:
                        report_ui_error(
                            self.window,
                            area="sammlungen",
                            title="Treffer nicht einsortiert",
                            lead="Der Treffer konnte nicht in die virtuelle Sammlung übernommen werden.",
                            error=exc,
                        )
                        return True
                    set_status(
                        self.window.status_label,
                        "OK · Treffer virtuell einsortiert",
                        "ok",
                    )
                    event.acceptProposedAction()
                return True
        return super().eventFilter(obj, event)

    def dispose(self) -> None:
        self._autosave()
        self.autosave_timer.stop()
        self.resource_timer.stop()
        if self.app is not None and self.install_global_filter:
            self.app.removeEventFilter(self)
        try:
            self.window.results.viewport().removeEventFilter(self)
            self.window.collection_list.viewport().removeEventFilter(self)
        except RuntimeError:
            pass
