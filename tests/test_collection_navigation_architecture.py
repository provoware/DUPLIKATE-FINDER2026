from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / "app" / "gui"


def test_main_window_delegates_collection_management():
    source = (GUI / "main_window.py").read_text(encoding="utf-8")

    assert "CollectionController(self)" in source
    assert "collection_controller.create" in source
    assert "collection_controller.show" in source
    assert "collection_controller.remove_selected_item" in source

    for method in (
        "_create_collection",
        "_current_collection_id",
        "_show_collection",
        "_remove_selected_collection_item",
    ):
        assert f"def {method}" not in source

    assert "def _refresh_collections" in source
    assert "collection_controller.refresh" in source


def test_navigation_has_one_definition_and_uses_text_catalog():
    source = (GUI / "navigation.py").read_text(encoding="utf-8")
    main = (GUI / "main_window.py").read_text(encoding="utf-8")

    assert "NAVIGATION" in source
    assert "navigation_titles" in source
    assert "navigation.dashboard" in source
    assert "navigation.help" in source
    assert "nav_colors =" not in main
    assert "NAVIGATION" in main
    assert "navigation_titles()" in main


def test_collection_and_navigation_copy_is_in_text_catalog():
    catalog = json.loads(
        (ROOT / "resources" / "texts" / "de-DE.v1.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = json.loads(
        (ROOT / "resources" / "texts" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert catalog["catalog_version"] == "1.2.0"
    assert manifest["catalogs"][0]["version"] == catalog["catalog_version"]
    assert len(catalog["navigation"]) == 8
    for key in (
        "heading",
        "create_button",
        "remove_button",
        "safety_note",
        "status_created",
        "status_removed",
    ):
        assert catalog["collections"][key]
