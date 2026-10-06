from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from app.gui.enhancements import UiEnhancements
from app.gui.main_window import MainWindow
from app.gui.theme import apply_accessible_theme
from app.logging_setup import configure_logging, install_exception_hook
from app.startup.progress import StartupProgressDialog
from app.startup.selftest import run_selftest
from app.storage.database import Database
from app.workspace import ensure_workspace


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    code_root=project_root()
    workspace=ensure_workspace()
    log_file=configure_logging(workspace)
    install_exception_hook(log_file)
    logger=logging.getLogger(__name__)
    logger.info("Programmstart | code=%s | workspace=%s",code_root,workspace)

    app=QApplication(sys.argv)
    app.setApplicationName("PROVOWARE DUPLIKATE-FINDER 2026")
    app.setOrganizationName("PROVOWARE")
    apply_accessible_theme(app)

    dialog=StartupProgressDialog()
    dialog.show()
    app.processEvents()

    preliminary=[
        ("Projektordner", True, str(workspace)),
        ("Abhängigkeiten", True, "Portable Python-/Qt-Laufzeit ist geladen."),
    ]
    for index,(name,ok,detail) in enumerate(preliminary,1):
        dialog.checkpoint(index,6,name,ok,detail)
        app.processEvents()

    database=Database(workspace/"data"/"duplicate_finder.sqlite3")
    database.initialize()
    dialog.checkpoint(3,6,"Datenbank",True,"Lokale Datenbank ist bereit.")
    app.processEvents()

    checks=run_selftest(workspace,require_gui=True)
    fatal=[check for check in checks if not check.ok]
    dialog.checkpoint(4,6,"Sicherheit",not fatal,"Schutzregeln und Arbeitsordner wurden geprüft.")
    app.processEvents()

    if fatal:
        detail="\n".join(f"• {c.name}: {c.detail}" for c in fatal)
        logger.error("Startprüfung fehlgeschlagen: %s",detail)
        dialog.checkpoint(5,6,"Start gestoppt",False,detail)
        QMessageBox.critical(None,"Startprüfung fehlgeschlagen","Das Programm wurde vorsorglich nicht gestartet.\n\n"+detail+f"\n\nProtokoll: {log_file}")
        return 2

    window=MainWindow(workspace,database)
    window._ui_enhancements=UiEnhancements(window,workspace,database)
    dialog.checkpoint(5,6,"Oberfläche",True,"Fenster und Bedienhilfen sind vorbereitet.")
    app.processEvents()
    window.show()
    dialog.checkpoint(6,6,"Werkzeug",True,"PROVOWARE ist startbereit.")
    dialog.ready()
    app.processEvents()
    QTimer.singleShot(350,dialog.close)
    logger.info("Oberfläche bereit")

    if os.environ.get("PROVOWARE_SMOKE_TEST")=="1":
        logger.info("Interner GUI-Starttest aktiv")
        QTimer.singleShot(700,app.quit)

    exit_code=app.exec()
    window._ui_enhancements.dispose()
    window.close()
    logger.info("Oberfläche sauber beendet")
    return exit_code


if __name__=="__main__":
    raise SystemExit(main())
