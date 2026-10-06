from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavigationItem:
    title: str
    color: str


NAVIGATION: tuple[NavigationItem, ...] = (
    NavigationItem("Übersicht", "#74d9ff"),
    NavigationItem("Textsuche", "#6ee7ff"),
    NavigationItem("Ergebnisse", "#9ce6ff"),
    NavigationItem("Duplikate", "#ff7e9d"),
    NavigationItem("Sammlungen", "#d59bff"),
    NavigationItem("Dateien & Vorschau", "#ffbf69"),
    NavigationItem("Journal", "#74e39a"),
    NavigationItem("Hilfe", "#b8c4ff"),
)


def navigation_titles() -> list[str]:
    return [item.title for item in NAVIGATION]
