from pathlib import Path

import pytest

from app.models.entities import DuplicateGroup
from app.storage.database import Database


def test_feature_flags_are_disabled_and_locked(tmp_path: Path):
    db = Database(tmp_path / "db.sqlite3")
    db.initialize()
    rows = db.feature_flags()
    assert len(rows) == 4
    assert all(row["enabled"] == 0 for row in rows)
    assert all(row["locked"] == 1 for row in rows)


def test_virtual_item_roundtrip(tmp_path: Path):
    db = Database(tmp_path / "db.sqlite3")
    db.initialize()
    path = tmp_path / "beispiel.txt"
    db.set_virtual_item(path, True, "prüfen")
    state = db.virtual_item(path)
    assert state.marked is True
    assert state.note == "prüfen"
    assert state.path == path


def test_collections_are_virtual_and_persistent(tmp_path: Path):
    db = Database(tmp_path / "db.sqlite3")
    db.initialize()
    original = tmp_path / "original.txt"
    original.write_text("Original bleibt stehen", encoding="utf-8")
    before = original.read_bytes()

    collection_id = db.create_collection("Wichtig", "Nur virtuelle Gruppe")
    db.add_collection_item(collection_id, original, "merken")
    items = db.collection_items(collection_id)

    assert len(items) == 1
    assert items[0].path == original
    assert items[0].note == "merken"
    assert original.read_bytes() == before


def test_duplicate_groups_roundtrip(tmp_path: Path):
    db = Database(tmp_path / "db.sqlite3")
    db.initialize()
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    group = DuplicateGroup("a" * 64, 12, (a, b))
    db.replace_duplicate_groups([group])
    stored = db.duplicate_groups()
    assert len(stored) == 1
    assert stored[0][1] == group


def test_duplicate_collection_names_are_rejected(tmp_path: Path):
    db = Database(tmp_path / "db.sqlite3")
    db.initialize()
    db.create_collection("Archiv")
    with pytest.raises(Exception):
        db.create_collection("Archiv")
