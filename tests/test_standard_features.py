from __future__ import annotations

import json
from pathlib import Path

from app.cpu_limit import CpuLimiter
from app.settings_store import SettingsStore
from app.state_portability import export_state, import_state, validate_import_payload
from app.storage.database import Database


def test_settings_store_roundtrip(tmp_path:Path):
    store=SettingsStore(tmp_path/"settings.json")
    store.save({"zoom_percent":150,"cpu_cores":2})
    data=store.load()
    assert data["zoom_percent"]==150
    assert data["cpu_cores"]==2
    assert data["exclude_python_project_dirs"] is True


def test_cpu_limiter_never_requests_more_than_available():
    limiter=CpuLimiter()
    assert 1 <= limiter.apply(9999) <= limiter.available


def test_virtual_state_export_import_does_not_touch_original(tmp_path:Path):
    db=Database(tmp_path/"a.sqlite3")
    db.initialize()
    original=tmp_path/"original.txt"
    original.write_text("bleibt",encoding="utf-8")
    cid=db.create_collection("Test")
    db.add_collection_item(cid,original,"notiz")
    db.set_virtual_item(original,True,"markiert")
    out=tmp_path/"export.json"
    export_state(db,out,{"zoom_percent":100})

    db2=Database(tmp_path/"b.sqlite3")
    db2.initialize()
    payload=import_state(db2,out)
    assert validate_import_payload(payload)
    assert db2.collections()[0].name=="Test"
    assert db2.virtual_item(original).marked is True
    assert original.read_text(encoding="utf-8")=="bleibt"


def test_invalid_import_is_rejected():
    try:
        validate_import_payload({"format":"falsch"})
    except ValueError:
        pass
    else:
        raise AssertionError("Ungültiger Import wurde akzeptiert")


def test_wrong_export_version_is_rejected():
    payload={
        "format":"PROVOWARE-DUPLIKATE-FINDER-STATE",
        "version":"999.0",
        "settings":{},
        "virtual_state":{"collections":[],"virtual_items":[]},
    }
    with __import__("pytest").raises(ValueError):
        validate_import_payload(payload)


def test_ui_source_contains_safe_import_backup_and_cpu_presets():
    root=Path(__file__).resolve().parents[1]
    enhancements=(root/"app/gui/enhancements.py").read_text(encoding="utf-8")
    portability=(root/"app/gui/state_portability_controller.py").read_text(encoding="utf-8")
    assert "PROVOWARE-vor-Import-" in portability
    for percent in ("25","50","75"):
        assert percent in enhancements
