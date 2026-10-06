from __future__ import annotations

import os

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


SUPPORTED_ZOOM = (100, 150, 200)


def requested_zoom() -> int:
    raw = os.environ.get("PROVOWARE_UI_ZOOM", "100")
    try:
        zoom = int(raw)
    except ValueError:
        return 100
    return zoom if zoom in SUPPORTED_ZOOM else 100


def apply_accessible_theme(app: QApplication, zoom: int | None = None) -> int:
    active_zoom = zoom or requested_zoom()
    point_size = max(10, round(11 * active_zoom / 100))
    app.setFont(QFont("Sans Serif", point_size))
    app.setStyleSheet(
        """
        QWidget { }
        QMainWindow { background: #f4f4f4; }
        QPushButton { padding: 7px 12px; font-weight: 600; }
        QLineEdit, QComboBox { padding: 6px 8px; }
        QListWidget::item { padding: 7px; }
        QTableWidget { gridline-color: #8a8a8a; }
        QHeaderView::section { padding: 6px; font-weight: 700; }
        QCheckBox { spacing: 8px; }
        QCheckBox::indicator { width: 22px; height: 22px; }
        QFrame[card="true"] { border: 1px solid #777; border-radius: 4px; padding: 6px; }
        QLabel[heading="true"] { font-weight: 800; }
        """
    )
    return active_zoom
