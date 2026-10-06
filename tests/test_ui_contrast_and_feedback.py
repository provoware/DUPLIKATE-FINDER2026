from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "app/gui/theme.py"


def _luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    channels = [int(value[index:index + 2], 16) / 255 for index in (0, 2, 4)]

    def linear(channel: float) -> float:
        return (
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
        )

    red, green, blue = (linear(channel) for channel in channels)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast(foreground: str, background: str) -> float:
    first = _luminance(foreground)
    second = _luminance(background)
    bright, dark = max(first, second), min(first, second)
    return (bright + 0.05) / (dark + 0.05)


def test_primary_theme_pairs_keep_readable_contrast():
    pairs = (
        ("#f7fbff", "#091018"),
        ("#ffffff", "#193b4b"),
        ("#ffffff", "#0a7187"),
        ("#eafff2", "#0d2b23"),
        ("#fff4c2", "#332914"),
        ("#ffe8ee", "#3a1822"),
        ("#eaf8ff", "#102a36"),
        ("#82919a", "#151d23"),
        ("#dbe8ef", "#091018"),
    )
    for foreground, background in pairs:
        assert _contrast(foreground, background) >= 4.5


def test_theme_has_distinct_semantic_status_states_and_disabled_process_buttons():
    source = THEME.read_text(encoding="utf-8")

    for level in ("ok", "warning", "error", "neutral"):
        assert f'statusLevel="{level}"' in source

    assert "QPushButton#process_cancel:disabled" in source
    assert "QPushButton#process_pause:disabled" in source


def test_status_feedback_is_event_driven_not_polled():
    enhancements = (ROOT / "app/gui/enhancements.py").read_text(encoding="utf-8")
    status = (ROOT / "app/gui/status_feedback.py").read_text(encoding="utf-8")

    assert "_refresh_status_style" not in enhancements
    assert "timer.start(300)" not in enhancements
    assert "statusLevel" in status
    assert "unpolish" in status
    assert "polish" in status


def test_virtual_database_actions_use_common_error_feedback():
    for relative in (
        "app/gui/result_controller.py",
        "app/gui/collection_controller.py",
        "app/gui/state_portability_controller.py",
        "app/gui/enhancements.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "report_ui_error" in source
