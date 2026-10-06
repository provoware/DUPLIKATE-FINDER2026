from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.gui.enhancements import UiEnhancements
from app.gui.main_window import MainWindow
from app.gui.theme import apply_accessible_theme
from app.logging_setup import configure_logging, install_exception_hook
from app.startup.selftest import run_selftest
from app.storage.database import Database


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    base = project_root()
    log_file = configure_logging(base)
    install_exception_hook(log_file)
    logger = logging.getLogger(__name__)
    logger.info("Programmstart")

    database = Database(base / "data" / "duplicate_finder.sqlite3")
    database.initialize()

    app = QApplication(sys.argv)
    app.setApplicationName("PROVOWARE DUPLIKATE-FINDER 2026")
    app.setOrganizationName("PROVOWARE")
    apply_accessible_theme(app)

    checks = run_selftest(base, require_gui=True)
    fatal = [check for check in checks if not check.ok]
    if fatal:
        detail = "\n".join(f"• {c.name}: {c.detail}" for c in fatal)
        logger.error("Startprüfung fehlgeschlagen: %s", detail)
        QMessageBox.critical(
            None,
            "Startprüfung fehlgeschlagen",
            "Das Programm wurde vorsorglich nicht gestartet.\n\n"
            + detail
            + f"\n\nProtokoll: {log_file}",
        )
        return 2

    window = MainWindow(base, database)
    window._ui_enhancements = UiEnhancements(window, base, database)
    window.show()
    logger.info("Oberfläche bereit")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
