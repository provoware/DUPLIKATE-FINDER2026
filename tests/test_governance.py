from __future__ import annotations

import json
from pathlib import Path

from tools.state_registry import area_for, recommended_checks, snapshot


ROOT = Path(__file__).resolve().parents[1]


def test_manifests_have_single_writer():
    data=json.loads((ROOT/"manifest/agents.manifest.json").read_text(encoding="utf-8"))
    writers=[a["id"] for a in data["agents"] if a["mode"]=="write"]
    assert writers == [data["single_writer"]] == ["operator"]


def test_project_manifest_forbids_tkinter():
    data=json.loads((ROOT/"manifest/project.manifest.json").read_text(encoding="utf-8"))
    assert data["runtime"]["tkinter_allowed"] is False


def test_targeted_plan_keeps_full_acceptance_for_code_changes():
    checks=recommended_checks(["app/core/search.py"])
    assert "unit" in checks
    assert "acceptance" in checks


def test_gui_change_requests_all_zoom_checks():
    checks=recommended_checks(["app/gui/main_window.py"])
    assert {"ui-100","ui-150","ui-200","acceptance"} <= set(checks)


def test_snapshot_is_stable_for_same_tree():
    a=snapshot(ROOT)
    b=snapshot(ROOT)
    assert a["aggregate_sha256"] == b["aggregate_sha256"]


def test_area_classification():
    assert "startup" in area_for("app/startup/bootstrap.py")
    assert "gui" in area_for("app/gui/theme.py")
    assert "gui" in area_for("app/file_browser/widget.py")
    assert "core" in area_for("app/file_browser/classification.py")


def test_text_catalog_manifest_matches_catalog_version():
    manifest=json.loads((ROOT/"resources/texts/manifest.json").read_text(encoding="utf-8"))
    entry=manifest["catalogs"][0]
    catalog=json.loads((ROOT/entry["path"]).read_text(encoding="utf-8"))
    assert entry["version"] == catalog["catalog_version"]
    assert manifest["active_locale"] == catalog["locale"]


def test_ui_process_area_reopening_and_freeze_are_recorded():
    data=json.loads((ROOT/"manifest/project.manifest.json").read_text(encoding="utf-8"))
    frozen={item["id"]:item for item in data["governance"]["frozen_areas"]}
    area=frozen["ui_process_control"]
    assert area["status"] in {"FROZEN","REOPENED"}
    if area["status"] == "REOPENED":
        assert area.get("reopen_reason")
    assert area["since_version"]=="0.6.0"
    assert area["reopened_from_version"]=="0.5.1"
    assert area["reopened_on"]=="2026-10-06"
    assert "app/gui/**" in area["scope"]
    assert "full_800x600_100_150_200_acceptance" in area["reopen_requires"]
    assert (ROOT/"docs/FREEZE_BEDIENUNG_PROZESS.md").is_file()
