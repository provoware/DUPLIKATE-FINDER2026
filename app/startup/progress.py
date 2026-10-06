from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout

from app.gui.design_tokens import BASE_SPACING, OUTER_MARGIN


@dataclass(frozen=True)
class StartupStep:
    name: str
    ok: bool
    detail: str


class StartupProgressDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PROVOWARE startet")
        self.setModal(False)
        self.setMinimumWidth(520)
        layout=QVBoxLayout(self)
        layout.setContentsMargins(OUTER_MARGIN,OUTER_MARGIN,OUTER_MARGIN,OUTER_MARGIN)
        layout.setSpacing(BASE_SPACING)
        self.title=QLabel("Startprüfung")
        self.title.setStyleSheet("font-weight:800; font-size:16px;")
        self.activity=QLabel("Prüfung wird vorbereitet …")
        self.activity.setWordWrap(True)
        self.progress=QProgressBar()
        self.progress.setRange(0,100)
        self.progress.setValue(0)
        self.status=QLabel("Hinweis · Startprüfung läuft")
        self.status.setWordWrap(True)
        self.details=QLabel("")
        self.details.setWordWrap(True)
        layout.addWidget(self.title)
        layout.addWidget(self.activity)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addWidget(self.details)

    def checkpoint(self, index:int, total:int, name:str, ok:bool, detail:str) -> None:
        self.activity.setText(name)
        self.progress.setValue(round(index/total*100))
        state="OK" if ok else "FEHLER"
        self.status.setText(f"{state} · {name}")
        self.details.setText(detail)

    def ready(self) -> None:
        self.progress.setValue(100)
        self.activity.setText("Start abgeschlossen")
        self.status.setText("OK · Alles bereit")
