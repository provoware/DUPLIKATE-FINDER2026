from __future__ import annotations

import os

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


ZOOM_STEPS=(80,90,100,110,125,150,175,200)
SUPPORTED_ZOOM=ZOOM_STEPS


def requested_zoom()->int:
    raw=os.environ.get("PROVOWARE_UI_ZOOM","100")
    try:
        zoom=int(raw)
    except ValueError:
        return 100
    return zoom if zoom in SUPPORTED_ZOOM else 100


def apply_accessible_theme(app:QApplication,zoom:int|None=None)->int:
    active_zoom=zoom or requested_zoom()
    point_size=max(9,round(11*active_zoom/100))
    app.setFont(QFont("Sans Serif",point_size))
    app.setStyleSheet("""
        QWidget { color:#eef8ff; background:#0e151d; }
        QMainWindow, QDialog { background:#080e14; }

        QFrame[card="true"] {
            background:#15222d;
            border:1px solid #35576d;
            border-radius:10px;
            padding:8px;
        }
        QFrame[section="true"] {
            background:#111e28;
            border:1px solid #34596f;
            border-left:5px solid #00e5ff;
            border-radius:9px;
            padding:8px;
        }
        QLabel[infoBox="true"] {
            background:#102936;
            border:1px solid #2f728c;
            border-radius:7px;
            padding:8px;
        }
        QLabel[hint="true"] { color:#b8cfde; }

        QPushButton {
            background:#182934;
            color:#f6fcff;
            border:1px solid #55798f;
            border-radius:7px;
            padding:8px 12px;
            font-weight:800;
            min-height:40px;
        }
        QPushButton[primaryAction="true"] {
            background:#0d3441;
            border:2px solid #00e5ff;
        }
        QPushButton[primaryAction="true"]:hover {
            background:#105064;
            border:2px solid #6ff5ff;
        }
        QPushButton[compact="true"] { min-height:30px; padding:5px 10px; }
        QPushButton:hover { background:#203a49; border-color:#86b7d0; }
        QPushButton:pressed { background:#0d5365; }
        QPushButton:focus { border:3px solid #ffe45e; }
        QPushButton:disabled { color:#778997; background:#151d24; border-color:#3d4d58; }
        QPushButton#process_cancel { border:2px solid #ff4d79; background:#321521; }
        QPushButton#process_pause { border:2px solid #ffe45e; background:#30290f; color:#fff4b8; }

        QLineEdit, QComboBox, QSpinBox {
            background:#09131b;
            color:#f7fcff;
            border:1px solid #54768b;
            border-radius:6px;
            padding:7px 9px;
            min-height:30px;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border:2px solid #00e5ff; }

        QListWidget, QTableWidget {
            background:#09131b;
            alternate-background-color:#112330;
            color:#f0f9ff;
            border:1px solid #466b82;
            border-radius:8px;
            gridline-color:#294352;
            selection-background-color:#075f75;
            selection-color:#ffffff;
        }
        QListWidget::item, QTableWidget::item {
            padding:8px;
            border-bottom:1px solid #203a49;
        }
        QListWidget::item:hover, QTableWidget::item:hover {
            background:#183d4c;
            border-bottom-color:#3d7188;
        }
        QListWidget::item:selected, QTableWidget::item:selected {
            background:#075f75;
            color:#ffffff;
            border-left:3px solid #61f3ff;
        }
        QListWidget#main_navigation {
            background:#0b1821;
            border:1px solid #294f63;
        }
        QListWidget#main_navigation::item { margin:2px 3px; border-radius:5px; }

        QHeaderView::section {
            background:#183545;
            color:#ffffff;
            padding:9px;
            font-weight:900;
            border:0;
            border-right:1px solid #3d6277;
            border-bottom:2px solid #00e5ff;
        }

        QProgressBar {
            background:#071017;
            color:#ffffff;
            border:1px solid #4e768e;
            border-radius:7px;
            min-height:24px;
            text-align:center;
            font-weight:900;
        }
        QProgressBar::chunk { background:#00bcd4; border-radius:6px; }

        QCheckBox { spacing:8px; }
        QCheckBox::indicator { width:22px; height:22px; }

        QLabel[heading="true"] { font-weight:900; color:#ffffff; }
        QLabel#safety_banner {
            background:#102d23;
            color:#dbffe9;
            border:2px solid #39e58c;
            border-radius:8px;
            padding:8px;
            font-weight:900;
        }
        QLabel#step_label, QLabel#eta_label, QLabel#activity_label {
            color:#c9dce8;
        }

        QToolTip {
            background:#061018;
            color:#ffffff;
            border:1px solid #00e5ff;
            padding:7px;
        }
        QSplitter::handle { background:#294c5d; }
        QScrollBar:vertical, QScrollBar:horizontal { background:#0a131a; border:0; }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background:#345f73; border-radius:5px; min-height:24px; min-width:24px;
        }
    """)
    return active_zoom
