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
        QWidget {
            color:#ecf7ff;
            background:#101820;
        }
        QMainWindow, QDialog { background:#0b1118; }
        QFrame[card="true"], QFrame[section="true"] {
            background:#16222d;
            border:1px solid #37566b;
            border-radius:9px;
            padding:7px;
        }
        QFrame[section="true"] { border-left:4px solid #00e5ff; }
        QPushButton {
            background:#172733;
            color:#f4fbff;
            border:2px solid #00e5ff;
            border-radius:7px;
            padding:8px 12px;
            font-weight:800;
            min-height:40px;
        }
        QPushButton[compact="true"] {
            min-height:30px;
            padding:5px 10px;
        }
        QPushButton:hover {
            background:#123849;
            border-color:#62f3ff;
        }
        QPushButton:pressed { background:#0d5365; }
        QPushButton:focus {
            border:3px solid #ffe45e;
        }
        QPushButton:disabled {
            color:#8595a3;
            background:#172027;
            border-color:#52606a;
        }
        QPushButton#process_cancel {
            border-color:#ff4d79;
        }
        QPushButton#process_pause {
            border-color:#ffe45e;
        }
        QLineEdit, QComboBox, QSpinBox {
            background:#0c151d;
            color:#f6fbff;
            border:2px solid #52738a;
            border-radius:6px;
            padding:7px 9px;
            min-height:30px;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
            border:3px solid #00e5ff;
        }
        QListWidget, QTableWidget {
            background:#0c151d;
            alternate-background-color:#14232e;
            color:#edf8ff;
            border:1px solid #45677d;
            border-radius:7px;
            gridline-color:#2f4b5d;
            selection-background-color:#006d83;
            selection-color:#ffffff;
        }
        QListWidget::item, QTableWidget::item {
            padding:7px;
            border-bottom:1px solid #203744;
        }
        QListWidget::item:hover, QTableWidget::item:hover {
            background:#183b4a;
        }
        QListWidget::item:selected, QTableWidget::item:selected {
            background:#006d83;
            color:#ffffff;
        }
        QHeaderView::section {
            background:#1b3341;
            color:#ffffff;
            padding:8px;
            font-weight:900;
            border:0;
            border-right:1px solid #45677d;
            border-bottom:2px solid #00e5ff;
        }
        QProgressBar {
            background:#0a1218;
            color:#ffffff;
            border:1px solid #52738a;
            border-radius:6px;
            min-height:22px;
            text-align:center;
            font-weight:800;
        }
        QProgressBar::chunk {
            background:#00cfe8;
            border-radius:5px;
        }
        QCheckBox { spacing:8px; }
        QCheckBox::indicator { width:22px; height:22px; }
        QLabel[heading="true"] {
            font-weight:900;
            color:#ffffff;
        }
        QLabel#safety_banner {
            background:#123126;
            color:#d9ffe7;
            border:2px solid #39e58c;
            border-radius:7px;
            padding:8px;
            font-weight:900;
        }
        QToolTip {
            background:#071017;
            color:#ffffff;
            border:1px solid #00e5ff;
            padding:6px;
        }
        QSplitter::handle { background:#294555; }
    """)
    return active_zoom
