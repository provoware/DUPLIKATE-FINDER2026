from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.gui.main_window import MainWindow
from app.gui.theme import apply_accessible_theme
from app.startup.selftest import run_selftest
from app.storage.database import Database


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    base = project_root()
    database = Database(base / "data" / "duplicate_finder.sqlite3")
    database.initialize()

    app = QApplication(sys.argv)
    app.setApplicationName("PROVOWARE DUPLIKATE-FINDER 2026")
    app.setOrganizationName("PROVOWARE")
    apply_accessible_theme(app)

    checks = run_selftest(base)
    fatal = [check for check in checks if not check.ok]
    if fatal:
        detail = "\n".join(f"• {c.name}: {c.detail}" for c in fatal)
        QMessageBox.critical(
            None,
            "Sicherheitsprüfung fehlgeschlagen",
            "Das Programm wurde vorsorglich nicht gestartet.\n\n" + detail,
        )
        return 2

    window = MainWindow(base, database)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
