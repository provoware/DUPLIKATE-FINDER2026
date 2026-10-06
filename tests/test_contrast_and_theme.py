from pathlib import Path

from app.gui.design_tokens import THEME_COLORS


ROOT = Path(__file__).resolve().parents[1]


def _luminance(value: str) -> float:
    raw = value.lstrip("#")
    channels = [int(raw[index:index + 2], 16) / 255 for index in (0, 2, 4)]

    def linear(channel: float) -> float:
        if channel <= 0.04045:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (linear(channel) for channel in channels)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast(foreground: str, background: str) -> float:
    high, low = sorted(
        (_luminance(foreground), _luminance(background)),
        reverse=True,
    )
    return (high + 0.05) / (low + 0.05)


def test_critical_text_contrasts_meet_wcag_aa():
    assert _contrast("#ffffff", THEME_COLORS["progress_fill"]) >= 4.5
    assert _contrast(
        THEME_COLORS["placeholder"],
        THEME_COLORS["input_bg"],
    ) >= 4.5
    assert _contrast(
        THEME_COLORS["status_ok_text"],
        THEME_COLORS["status_ok_bg"],
    ) >= 4.5
    assert _contrast(
        THEME_COLORS["status_info_text"],
        THEME_COLORS["status_info_bg"],
    ) >= 4.5
    assert _contrast(
        THEME_COLORS["status_error_text"],
        THEME_COLORS["status_error_bg"],
    ) >= 4.5


def test_status_colors_are_centralized_in_theme():
    enhancements = (ROOT / "app/gui/enhancements.py").read_text(encoding="utf-8")
    theme = (ROOT / "app/gui/theme.py").read_text(encoding="utf-8")

    assert 'setProperty("statusLevel", level)' in enhancements
    assert "status_label.setStyleSheet" not in enhancements
    assert 'QLabel#status_label[statusLevel="error"]' in theme
    assert "QPalette.ColorRole.PlaceholderText" in theme


def test_theme_contains_no_unresolved_color_placeholders():
    from PySide6.QtWidgets import QApplication
    from app.gui.theme import apply_accessible_theme

    app = QApplication.instance() or QApplication([])
    apply_accessible_theme(app, 100)
    assert "__" not in app.styleSheet()
