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
from app.checkpoints import CheckpointRecorder
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
    recorder=CheckpointRecorder(workspace/"checkpoints"/"startup.jsonl")
    dialog.show()
    app.processEvents()

    def mark(index:int,name:str,ok:bool,detail:str)->None:
        dialog.checkpoint(index,6,name,ok,detail)
        recorder.add(name.casefold().replace(" ","-"),"green" if ok else "red",detail)
        app.processEvents()

    preliminary=[
        ("Projektordner", True, str(workspace)),
        ("Abhängigkeiten", True, "Portable Python-/Qt-Laufzeit ist geladen."),
    ]
    for index,(name,ok,detail) in enumerate(preliminary,1):
        mark(index,name,ok,detail)

    database=Database(workspace/"data"/"duplicate_finder.sqlite3")
    database.initialize()
    mark(3,"Datenbank",True,"Lokale Datenbank ist bereit.")

    checks=run_selftest(workspace,require_gui=True)
    fatal=[check for check in checks if not check.ok]
    mark(4,"Sicherheit",not fatal,"Schutzregeln und Arbeitsordner wurden geprüft.")

    if fatal:
        detail="\n".join(f"• {c.name}: {c.detail}" for c in fatal)
        logger.error("Startprüfung fehlgeschlagen: %s",detail)
        mark(5,"Start gestoppt",False,detail)
        QMessageBox.critical(None,"Startprüfung fehlgeschlagen","Das Programm wurde vorsorglich nicht gestartet.\n\n"+detail+f"\n\nProtokoll: {log_file}")
        return 2

    window=MainWindow(workspace,database)
    window._ui_enhancements=UiEnhancements(window,workspace,database)
    mark(5,"Oberfläche",True,"Fenster und Bedienhilfen sind vorbereitet.")
    window.show()
    mark(6,"Werkzeug",True,"PROVOWARE ist startbereit.")
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
