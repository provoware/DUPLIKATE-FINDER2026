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
        QWidget { color:#f7fbff; background:#091018; }
        QLabel { background:transparent; }
        QCheckBox, QRadioButton { background:transparent; }
        QMainWindow, QDialog { background:#050a0f; }

        /* Bereichsfarben: gleiche dunkle Basis, klar getrennte Akzente. */
        QWidget[area="dashboard"] { border-top:3px solid #54e6e9; }
        QWidget[area="search"] { border-top:3px solid #59a8ff; }
        QWidget[area="results"] { border-top:3px solid #8fd3ff; }
        QWidget[area="duplicates"] { border-top:3px solid #ff6688; }
        QWidget[area="collections"] { border-top:3px solid #c78cff; }
        QWidget[area="files"] { border-top:3px solid #ffb35c; }
        QWidget[area="journal"] { border-top:3px solid #69df9d; }
        QWidget[area="help"] { border-top:3px solid #aab5ff; }

        QFrame[card="true"] {
            background:#132630;
            border:1px solid #5c8396;
            border-radius:10px;
            padding:4px;
        }
        QFrame[section="true"] {
            background:#0f252f;
            border:1px solid #58869a;
            border-left:5px solid #54e6e9;
            border-radius:9px;
            padding:8px;
        }
        QLabel[infoBox="true"] {
            background:#0e2834;
            border:1px solid #4c8197;
            border-radius:7px;
            padding:8px;
        }
        QLabel[hint="true"] { color:#d0e0e9; }
        QLabel[workflowGuide="true"] {
            background:#0d2c35;
            color:#f4feff;
            border:2px solid #54e6e9;
            border-radius:8px;
            padding:4px 8px;
            font-weight:800;
        }
        QLabel[cardTitle="true"] { color:#c0d0dc; font-size:0.92em; }
        QLabel[cardValue="true"] { color:#ffffff; font-weight:800; }

        QPushButton {
            background:#18323f;
            color:#ffffff;
            border:1px solid #79a5b8;
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
        QPushButton#process_cancel:disabled,
        QPushButton#process_pause:disabled {
            background:#151d23;
            color:#82919a;
            border:1px solid #4a5962;
        }

        QLineEdit, QComboBox, QSpinBox {
            background:#07151d;
            color:#ffffff;
            border:1px solid #7aa5b7;
            border-radius:6px;
            padding:7px 9px;
            min-height:30px;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border:2px solid #45d8df; }

        QListWidget, QTableView, QTableWidget {
            background:#07151d;
            alternate-background-color:#102b36;
            color:#f7fcff;
            border:1px solid #719caf;
            border-radius:8px;
            gridline-color:#355160;
            selection-background-color:#0a7187;
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
            background:#071821;
            border:1px solid #568499;
            padding:4px;
        }
        QListWidget#main_navigation::item { margin:3px 3px; padding:10px 9px; border-radius:6px; font-weight:800; }
        QListWidget#main_navigation::item:selected { background:#0b6f84; border:2px solid #6ff7f7; color:#ffffff; }
        QListWidget#main_navigation::item:hover { background:#173f4d; }
        QTableView::item { padding:6px; border-bottom:1px solid #304956; }
        QTableView::item:hover { background:#143744; color:#ffffff; }
        QTableView::item:selected { background:#0a7187; color:#ffffff; }

        QHeaderView::section {
            background:#193b4b;
            color:#ffffff;
            padding:9px;
            font-weight:900;
            border:0;
            border-right:1px solid #4b7185;
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
        QProgressBar::chunk { background:#20d3dc; border-radius:6px; }

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
        QLabel#status_label {
            background:#10242f;
            color:#eef8ff;
            border:1px solid #5d8799;
            border-radius:6px;
            padding:5px 9px;
            font-weight:900;
        }
        QLabel#status_label[statusLevel="ok"] {
            background:#0d2b23;
            color:#eafff2;
            border:1px solid #4ddd9c;
        }
        QLabel#status_label[statusLevel="warning"] {
            background:#332914;
            color:#fff4c2;
            border:1px solid #e5bd45;
        }
        QLabel#status_label[statusLevel="error"] {
            background:#3a1822;
            color:#ffe8ee;
            border:1px solid #ff6f8f;
        }
        QLabel#status_label[statusLevel="neutral"] {
            background:#102a36;
            color:#eaf8ff;
            border:1px solid #57a6c2;
        }
        QLabel#step_label, QLabel#eta_label, QLabel#activity_label {
            color:#dbe8ef;
        }
        QLabel#counter_label {
            color:#f4fbff;
            font-weight:800;
        }

        QLabel#file_browser_title { color:#ffd09a; }
        QFrame#file_preview_panel {
            background:#1f1a12;
            border:1px solid #8b673d;
            border-left:5px solid #ffb35c;
        }
        QLabel#file_preview_title { color:#ffd09a; }
        QLabel#file_preview_image {
            background:#0d1116;
            border:1px solid #6f5b43;
            border-radius:7px;
            padding:6px;
        }
        QTextBrowser#file_preview_text {
            background:#0d1116;
            color:#fff8ed;
            border:1px solid #6f5b43;
            border-radius:7px;
            padding:6px;
        }
        QWidget#file_browser QPushButton[primaryAction="true"] {
            background:#54320f;
            border:2px solid #ffb35c;
            color:#ffffff;
        }
        QWidget#file_browser QPushButton[primaryAction="true"]:hover {
            background:#704618;
            border-color:#ffd09a;
        }
        QWidget#file_browser QTableView::item:selected {
            background:#744716;
            color:#ffffff;
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
