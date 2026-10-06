from __future__ import annotations

from pathlib import Path


def test_theme_has_no_broken_nan_token():
    source=(Path(__file__).resolve().parents[1]/"app/gui/theme.py").read_text(encoding="utf-8")
    assert "NaN" not in source
    assert "#45d8df" in source
    assert "QProgressBar::chunk" in source
    assert "QLabel { background:transparent; }" in source
    assert "QTableView::item:selected" in source


def test_dashboard_contains_cpu_import_export_autosave_contract():
    source=(Path(__file__).resolve().parents[1]/"app/gui/enhancements.py").read_text(encoding="utf-8")
    for token in ("cpu_limiter","dashboard_export","dashboard_import","300_000"):
        assert token in source
