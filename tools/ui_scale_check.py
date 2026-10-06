from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton, QLineEdit, QCheckBox, QComboBox, QWidget  # noqa: E402

from app.gui.main_window import MainWindow  # noqa: E402
from app.gui.theme import apply_accessible_theme  # noqa: E402
from app.storage.database import Database  # noqa: E402
from app.gui.enhancements import UiEnhancements  # noqa: E402


CRITICAL_BY_PAGE = {
    0: ["safety_banner", "locked_write_features", "dashboard_go_search", "dashboard_go_duplicates", "dashboard_go_collections", "dashboard_go_files"],
    1: ["search_root", "search_choose_root", "search_query", "search_names", "search_contents", "search_start", "search_info"],
    2: ["results_table", "result_mark", "result_note", "result_save_meta", "result_collection", "result_add_collection"],
    3: ["duplicate_start", "duplicate_root", "duplicate_group_list", "duplicate_members", "duplicate_safety_note"],
    4: ["collection_name", "collection_note", "collection_create", "collection_list", "collection_items", "collection_remove", "collection_safety_note"],
    5: ["file_browser_root", "file_browser_choose", "file_browser_query", "file_browser_kind", "file_browser_table", "file_preview_title", "file_preview_image", "file_browser_safety"],
    6: ["journal_info"],
    7: ["help_safety"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zoom", type=int, choices=(100, 150, 200), required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = QApplication(sys.argv)
    apply_accessible_theme(app, args.zoom)

    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp)
        for name in ("data", "logs", "recovery"):
            (base / name).mkdir(parents=True, exist_ok=True)
        db = Database(base / "data" / "ui.sqlite3")
        db.initialize()
        window = MainWindow(base, db)
        enhancements = UiEnhancements(window, base, db, install_global_filter=False)
        enhancements._apply_zoom(args.zoom)
        window.resize(1280, 800)
        window.show()
        app.processEvents()

        failures: list[str] = []
        if window.minimumSizeHint().width() > 1280 or window.minimumSizeHint().height() > 800:
            failures.append(
                f"Fenster-Mindestbedarf {window.minimumSizeHint().width()}x{window.minimumSizeHint().height()} überschreitet 1280x800"
            )
            for index in range(window.pages.count()):
                hint = window.pages.widget(index).minimumSizeHint()
                print(f"DIAGNOSE: Seite {index} Mindestbedarf {hint.width()}x{hint.height()}")

        for page_index, names in CRITICAL_BY_PAGE.items():
            window.nav.setCurrentRow(page_index)
            app.processEvents()
            for name in names:
                widget = window.findChild(QWidget, name)
                if widget is None:
                    failures.append(f"Seite {page_index}: Element fehlt: {name}")
                    continue
                if not widget.isVisible():
                    failures.append(f"Seite {page_index}: Element nicht sichtbar: {name}")
                    continue
                if widget.width() <= 0 or widget.height() <= 0:
                    failures.append(f"Seite {page_index}: Element ohne nutzbare Größe: {name}")
                if isinstance(widget, (QPushButton, QLineEdit, QCheckBox, QComboBox)):
                    hint = widget.sizeHint()
                    if widget.width() + 2 < min(hint.width(), 520):
                        failures.append(f"Seite {page_index}: vermutlich horizontal gekürzt: {name}")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        window.nav.setCurrentRow(0)
        app.processEvents()
        window.grab().save(str(args.output))
        enhancements.dispose()
        window.close()

        if failures:
            for failure in failures:
                print(f"FEHLER: {failure}")
            return 1

    print(f"OK: Oberfläche bei {args.zoom}% geprüft")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
