from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_theme_has_no_corrupted_nan_token_and_has_neon_action_borders():
    source=(ROOT/"app/gui/theme.py").read_text(encoding="utf-8")
    assert "NaN" not in source
    assert "#00bcd4" in source
    assert 'QPushButton[danger="true"]' in source
    assert "QProgressBar::chunk" in source


def test_process_controls_and_filters_are_visible_contracts():
    source=(ROOT/"app/gui/main_window.py").read_text(encoding="utf-8")
    for token in (
        "activity_pause",
        "activity_cancel",
        "activity_eta",
        "search_filter_options",
        "duplicate_filter_options",
        "_pause_or_resume",
        "_cancel_active_process",
    ):
        assert token in source


def test_dashboard_contains_cpu_autosave_and_state_transfer():
    source=(ROOT/"app/gui/enhancements.py").read_text(encoding="utf-8")
    for token in ("cpu_core_limit","autosave_info","dashboard_export","dashboard_import"):
        assert token in source
