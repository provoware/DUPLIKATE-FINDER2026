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
    app.setProperty("provowareUiZoom",active_zoom)
    point_size=max(9,round(11*active_zoom/100))
    app.setFont(QFont("Sans Serif",point_size))
    app.setStyleSheet("""
        QWidget { color:#f7fbff; background:#0b1118; }
        QLabel { background:transparent; }
        QCheckBox, QRadioButton { background:transparent; }
        QMainWindow, QDialog { background:#070d12; }

        QFrame[card="true"] {
            background:#152633;
            border:1px solid #4f7890;
            border-radius:10px;
            padding:4px;
        }
        QFrame[section="true"] {
            background:#102630;
            border:1px solid #4b7e92;
            border-left:5px solid #54e6e9;
            border-radius:9px;
            padding:8px;
        }
        QLabel[infoBox="true"] {
            background:#102936;
            border:1px solid #2f728c;
            border-radius:7px;
            padding:8px;
        }
        QLabel[hint="true"] { color:#d0e0e9; }
        QLabel[workflowGuide="true"] {
            background:#0d2c35;
            color:#f4feff;
            border:2px solid #54e6e9;
            border-radius:8px;
            padding:6px 8px;
            font-weight:800;
        }
        QLabel[cardTitle="true"] { color:#c0d0dc; font-size:0.92em; }
        QLabel[cardValue="true"] { color:#ffffff; font-weight:800; }

        QPushButton {
            background:#18303d;
            color:#ffffff;
            border:1px solid #6a94aa;
            border-radius:7px;
            padding:8px 12px;
            font-weight:800;
            min-height:40px;
        }
        QPushButton[primaryAction="true"] {
            background:#0b3f4d;
            border:2px solid #61f3f5;
        }
        QPushButton[primaryAction="true"]:hover {
            background:#105064;
            border:2px solid #8af3f4;
        }
        QPushButton[compact="true"] { min-height:40px; padding:7px 12px; }
        QPushButton:hover { background:#24485a; border-color:#9fe8ff; }
        QPushButton:pressed { background:#0d5365; }
        QPushButton:focus { border:3px solid #ffe45e; }
        QPushButton:disabled { color:#c0cbd3; background:#1b252d; border-color:#53616c; }
        QPushButton#process_cancel { border:2px solid #ff6688; background:#381827; }
        QPushButton#process_pause { border:2px solid #f5cf58; background:#332b14; color:#fff2bd; }

        QLineEdit, QComboBox, QSpinBox {
            background:#07131b;
            color:#ffffff;
            border:1px solid #6e98ac;
            border-radius:6px;
            padding:7px 9px;
            min-height:30px;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border:2px solid #45d8df; }

        QListWidget, QTableView, QTableWidget {
            background:#07131b;
            alternate-background-color:#102834;
            color:#f7fcff;
            border:1px solid #6b93a8;
            border-radius:8px;
            gridline-color:#294352;
            selection-background-color:#08758f;
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
            background:#081821;
            border:1px solid #416f84;
            padding:4px;
        }
        QListWidget#main_navigation::item { margin:3px 3px; padding:10px 9px; border-radius:6px; font-weight:800; }
        QListWidget#main_navigation::item:selected { background:#0a6074; border:2px solid #61f3f5; color:#ffffff; }
        QListWidget#main_navigation::item:hover { background:#173b49; }
        QTableView::item { padding:6px; border-bottom:1px solid #263b49; }
        QTableView::item:selected { background:#075f75; color:#ffffff; }

        QHeaderView::section {
            background:#183545;
            color:#ffffff;
            padding:9px;
            font-weight:900;
            border:0;
            border-right:1px solid #3d6277;
            border-bottom:2px solid #45d8df;
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
        QProgressBar::chunk { background:#19d6df; border-radius:6px; }

        QCheckBox { spacing:8px; }
        QCheckBox::indicator { width:22px; height:22px; }
        QCheckBox::indicator:unchecked { background:#0b151d; border:2px solid #8fa5b4; border-radius:4px; }
        QCheckBox::indicator:checked { background:#087989; border:2px solid #75eff1; border-radius:4px; }
        QCheckBox::indicator:disabled { background:#202b33; border-color:#8998a2; }

        QLabel[heading="true"] { font-weight:900; color:#ffffff; }
        QLabel#safety_banner {
            background:#102d23;
            color:#dbffe9;
            border:2px solid #4ddd9c;
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
            border:1px solid #45d8df;
            padding:7px;
        }
        QSplitter::handle { background:#294c5d; }
        QScrollBar:vertical, QScrollBar:horizontal { background:#0a131a; border:0; min-width:14px; min-height:14px; }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background:#345f73; border-radius:5px; min-height:24px; min-width:24px;
        }
    """)
    return active_zoom
