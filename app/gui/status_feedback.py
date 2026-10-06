from __future__ import annotations

from typing import Literal

from PySide6.QtWidgets import QLabel


StatusLevel = Literal["neutral", "ok", "warning", "error"]


def set_status(label: QLabel, text: str, level: StatusLevel = "neutral") -> None:
    """Setzt Statustext und semantische Farbe gemeinsam."""
    label.setProperty("statusLevel", level)
    label.setText(text)
    style = label.style()
    if style is not None:
        style.unpolish(label)
        style.polish(label)
    label.update()
