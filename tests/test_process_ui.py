from __future__ import annotations

from pathlib import Path

from app.progress_format import format_eta


ROOT=Path(__file__).resolve().parents[1]


def test_eta_format_is_lay_friendly_without_gui_import():
    assert format_eta(None) == "wird ermittelt"
    assert format_eta(12).startswith("ca. 12")
    assert "min" in format_eta(125)


def test_common_exclusion_dialog_contract_is_static():
    source=(ROOT/"app/gui/exclusion_dialog.py").read_text(encoding="utf-8")
    assert '".py"' in source
    assert '".mp4"' in source
    assert "QLineEdit" not in source


def test_core_process_tests_do_not_import_gui_main_window():
    source=(ROOT/"tests/test_process_ui.py").read_text(encoding="utf-8")
    assert "app.gui.main_window" not in source
