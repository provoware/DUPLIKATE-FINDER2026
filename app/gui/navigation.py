from __future__ import annotations

from dataclasses import dataclass

from app.texts import text as ui_text


@dataclass(frozen=True)
class NavigationItem:
    text_key: str
    color: str


NAVIGATION: tuple[NavigationItem, ...] = (
    NavigationItem("navigation.dashboard", "#74d9ff"),
    NavigationItem("navigation.search", "#6ee7ff"),
    NavigationItem("navigation.results", "#9ce6ff"),
    NavigationItem("navigation.duplicates", "#ff7e9d"),
    NavigationItem("navigation.collections", "#d59bff"),
    NavigationItem("navigation.files", "#ffbf69"),
    NavigationItem("navigation.journal", "#74e39a"),
    NavigationItem("navigation.help", "#b8c4ff"),
)


def navigation_titles() -> list[str]:
    return [ui_text(item.text_key) for item in NAVIGATION]
