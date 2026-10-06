from __future__ import annotations

import json
from pathlib import Path

from app.settings import AppSettings, SettingsStore
from app.state_transfer import build_export, validate_import
from app.storage.database import Database


def test_settings_roundtrip_and_cpu_limit(tmp_path: Path):
    store=SettingsStore(tmp_path/"config"/"settings.json")
    settings=AppSettings(cpu_workers=999, excluded_extensions=["ZIP", ".mp4"])
    store.save(settings)
    loaded=store.load()
    assert loaded.resolved_cpu_workers() >= 1
    assert ".mp4" in loaded.excluded_extensions
    assert ".zip" in loaded.excluded_extensions
    assert loaded.autosave_minutes == 5


def test_virtual_state_export_import_does_not_touch_original(tmp_path: Path):
    original=tmp_path/"original.txt"
    original.write_text("unverändert",encoding="utf-8")
    before=original.read_bytes()

    first=Database(tmp_path/"a.sqlite3")
    first.initialize()
    first.set_virtual_item(original,True,"merken")
    cid=first.create_collection("Wichtig","virtuell")
    first.add_collection_item(cid,original,"Eintrag")
    exported=first.export_virtual_state()

    second=Database(tmp_path/"b.sqlite3")
    second.initialize()
    counts=second.import_virtual_state(exported)
    assert counts == (1,1)
    assert second.virtual_item(original).marked is True
    assert second.collections()[0].name == "Wichtig"
    assert original.read_bytes() == before


def test_state_transfer_contract():
    payload=build_export({"cpu_workers":2},{"schema_version":"1.0.0","collections":[],"virtual_items":[]})
    assert validate_import(payload)["schema"] == "provoware-state-export-1"
