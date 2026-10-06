from __future__ import annotations

import os

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.gui.design_tokens import MIN_CLICK_HEIGHT


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
        QWidget { color:#17202a; }
        QMainWindow { background:#eef3f8; }
        QFrame[card="true"] {
            background:#ffffff; border:1px solid #9aa9b7;
            border-radius:7px; padding:7px;
        }
NaN        QPushButton:hover { background:#e9f5ff; border-color:#005fcc; }
        QPushButton:focus { border:3px solid #d68a00; }
        QPushButton:disabled { color:#616b75; background:#e5e9ed; border-color:#a3adb6; }
        QLineEdit, QComboBox {
            background:#ffffff; color:#17202a; border:2px solid #758697;
            border-radius:5px; padding:7px 9px;
        }
        QLineEdit:focus, QComboBox:focus { border:3px solid #005fcc; }
        QListWidget, QTableWidget {
            background:#ffffff; alternate-background-color:#f1f6fa;
            border:1px solid #8796a5; gridline-color:#aab5bf;
        }
        QListWidget::item { padding:8px; }
        QListWidget::item:selected, QTableWidget::item:selected {
            background:#005fcc; color:#ffffff;
        }
        QHeaderView::section {
            background:#dce8f3; color:#17202a; padding:7px;
            font-weight:800; border:1px solid #95a5b3;
        }
        QCheckBox { spacing:8px; }
        QCheckBox::indicator { width:22px; height:22px; }
        QLabel[heading="true"] { font-weight:800; color:#102a43; }
        QToolTip {
            background:#102a43; color:white; border:1px solid #ffffff; padding:5px;
        }
        """
    )
    return active_zoom
