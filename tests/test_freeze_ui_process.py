from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_ui_process_area_is_refrozen_after_v060_acceptance():
    manifest=json.loads((ROOT/"manifest/project.manifest.json").read_text(encoding="utf-8"))
    areas={area["id"]:area for area in manifest["governance"]["frozen_areas"]}
    frozen=areas["ui_process_control"]
    assert frozen["status"]=="FROZEN"
    assert frozen["since_version"]=="0.6.0"
    assert frozen["reopened_from_version"]=="0.5.1"
    assert "regression_correction" in frozen["allowed_without_reopen"]
    assert "full_800x600_100_150_200_acceptance" in frozen["reopen_requires"]


def test_real_search_virtualization_contract():
    model=(ROOT/"app/gui/table_models.py").read_text(encoding="utf-8")
    worker=(ROOT/"app/gui/workers.py").read_text(encoding="utf-8")
    main=(ROOT/"app/gui/main_window.py").read_text(encoding="utf-8")
    assert "search_hits_page" in model
    assert "max_pages" in model
    assert "collect_hits=False" in worker
    assert "results_model.set_job" in main
    assert "last_hits" not in main
