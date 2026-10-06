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
