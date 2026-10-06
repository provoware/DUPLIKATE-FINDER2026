from __future__ import annotations

import os

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


ZOOM_STEPS = (80, 90, 100, 110, 125, 150, 175, 200)
SUPPORTED_ZOOM = ZOOM_STEPS


def requested_zoom() -> int:
    raw = os.environ.get("PROVOWARE_UI_ZOOM", "100")
    try:
        zoom = int(raw)
    except ValueError:
        return 100
    return zoom if zoom in SUPPORTED_ZOOM else 100


def apply_accessible_theme(app: QApplication, zoom: int | None = None) -> int:
    active_zoom = zoom or requested_zoom()
    point_size = max(9, round(11 * active_zoom / 100))
    app.setFont(QFont("Sans Serif", point_size))
    app.setStyleSheet(
        """
        QWidget {
            color:#f1f7fb;
            background:transparent;
        }
        QMainWindow {
            background:#07111f;
        }
        QFrame[headerPanel="true"] {
            background:#0d1b2d;
            border:1px solid #27445e;
            border-radius:10px;
        }
        QWidget[pagePanel="true"] {
            background:#0a1626;
            border:1px solid #203b55;
            border-radius:10px;
        }
        QFrame[card="true"] {
            background:#102238;
            border:1px solid #31536f;
            border-radius:9px;
        }
        QFrame[section="true"] {
            background:#0f2034;
            border:1px solid #2a5873;
            border-radius:9px;
        }
        QFrame[processPanel="true"] {
            background:#0c1c2d;
            border:1px solid #2e617d;
            border-radius:9px;
        }
        QFrame[lockedPanel="true"] {
            background:#171d2a;
            border:1px solid #665b45;
            border-radius:9px;
        }
        QFrame[accentPanel="true"] {
            background:#0b2230;
            border:1px solid #00cfe8;
            border-radius:9px;
        }
        QLabel[infoPanel="true"] {
            background:#102840;
            color:#e8f6ff;
            border:1px solid #315f7d;
            border-radius:7px;
            padding:8px;
        }
        QLabel[safetyBanner="true"] {
            background:#112d27;
            color:#eafff3;
            border:2px solid #33e39a;
            border-radius:7px;
            padding:8px;
            font-weight:800;
        }
        QLabel[heading="true"] {
            color:#f7fbff;
            font-weight:800;
        }
        QLabel[cardTitle="true"], QLabel[sectionTitle="true"] {
            color:#a9dcef;
            font-weight:800;
        }
        QLabel[cardValue="true"] {
            color:#ffffff;
            font-weight:800;
        }
        QPushButton {
            background:#0d2033;
            color:#f5fbff;
            border:2px solid #00bcd4;
            border-radius:7px;
            padding:7px 11px;
            min-height:28px;
            font-weight:700;
        }
        QPushButton:hover {
            background:#12314a;
            border-color:#32efff;
        }
        QPushButton:focus {
            border:3px solid #7cfff4;
            background:#12314a;
        }
        QPushButton:pressed {
            background:#061522;
            border-color:#ffffff;
        }
        QPushButton[accent="true"] {
            background:#0a2d3b;
            border-color:#26f7ff;
        }
        QPushButton[warning="true"] {
            background:#2e2612;
            border-color:#ffd54a;
            color:#fff6d5;
        }
        QPushButton[danger="true"] {
            background:#32161d;
            border-color:#ff4f79;
            color:#fff2f5;
        }
        QPushButton:disabled {
            color:#7f91a2;
            background:#18212c;
            border-color:#465666;
        }
        QLineEdit, QComboBox {
            background:#081725;
            color:#f3f9fc;
            border:2px solid #41677f;
            border-radius:6px;
            padding:7px 9px;
            min-height:26px;
            selection-background-color:#00a9c2;
        }
        QLineEdit:focus, QComboBox:focus {
            border:2px solid #3cf5ff;
        }
        QListWidget, QTableWidget {
            background:#071421;
            alternate-background-color:#0d2031;
            color:#edf7fb;
            border:1px solid #365a72;
            border-radius:7px;
            gridline-color:#28465a;
            selection-background-color:#087e9a;
            selection-color:#ffffff;
        }
        QListWidget::item {
            padding:8px;
            border-bottom:1px solid #1b3549;
        }
        QListWidget::item:hover {
            background:#13344c;
        }
        QListWidget::item:selected, QTableWidget::item:selected {
            background:#087e9a;
            color:#ffffff;
        }
        QHeaderView::section {
            background:#15334c;
            color:#ffffff;
            padding:8px;
            font-weight:800;
            border:0;
            border-right:1px solid #47718b;
            border-bottom:2px solid #00cfe8;
        }
        QTableCornerButton::section {
            background:#15334c;
            border:0;
        }
        QCheckBox {
            spacing:8px;
            color:#eff8fb;
        }
        QCheckBox::indicator {
            width:20px;
            height:20px;
        }
        QProgressBar {
            background:#071421;
            color:#ffffff;
            border:1px solid #3d6279;
            border-radius:6px;
            text-align:center;
            min-height:22px;
            font-weight:800;
        }
        QProgressBar::chunk {
            background:#00cfe8;
            border-radius:5px;
        }
        QSplitter::handle {
            background:#284a61;
            width:3px;
            height:3px;
        }
        QScrollBar:vertical, QScrollBar:horizontal {
            background:#081725;
            border:0;
            margin:0;
        }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background:#3b6882;
            border-radius:5px;
            min-height:28px;
            min-width:28px;
        }
        QToolTip {
            background:#eefbff;
            color:#08131d;
            border:2px solid #00bcd4;
            padding:6px;
        }
        """
    )
    return active_zoom
