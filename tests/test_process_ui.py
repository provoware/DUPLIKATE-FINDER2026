from __future__ import annotations

from app.gui.main_window import MainWindow


def test_eta_format_is_lay_friendly():
    assert MainWindow._format_eta(None) == "wird ermittelt"
    assert MainWindow._format_eta(12).startswith("ca. 12")
    assert "min" in MainWindow._format_eta(125)


def test_common_exclusion_dialog_has_no_free_text_input():
    from app.gui.exclusion_dialog import COMMON_TYPES
    assert ".py" in dict(COMMON_TYPES)
    assert ".mp4" in dict(COMMON_TYPES)
    assert len(COMMON_TYPES) >= 10
