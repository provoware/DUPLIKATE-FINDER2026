from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.duplicates import scan_duplicate_groups_to_database
from app.core.hashing import FileChangedError, stable_sha256
from app.core.scanner import FileScanner
from app.gui.table_models import CollectionItemsModel, DuplicateMembersModel
from app.models.entities import DuplicateGroup, FileRecord, SearchJob
from app.settings_store import SettingsStore
from app.state_portability import validate_import_payload
from app.storage.database import Database
from app.storage.migrations import LATEST_SCHEMA_VERSION


def _record(path: Path) -> FileRecord:
    stat = path.stat()
    return FileRecord(
        path=path,
        size=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
        device=int(getattr(stat, "st_dev", 0)),
        inode=int(getattr(stat, "st_ino", 0)),
    )


def test_database_migrates_to_latest_schema(tmp_path: Path):
    db = Database(tmp_path / "state.sqlite3")
    db.initialize()
    assert db.schema_version() == LATEST_SCHEMA_VERSION
    with db.connect() as connection:
        file_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(files)")
        }
        search_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(search_jobs)")
        }
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert {"device", "inode", "quick_hash", "verified_at"} <= file_columns
    assert "error_count" in search_columns
    assert {"scan_runs", "scan_inventory", "scan_errors"} <= tables


def test_corrupt_settings_are_backed_up_and_reported(tmp_path: Path):
    path = tmp_path / "settings.json"
    path.write_text("{ kaputt", encoding="utf-8")
    store = SettingsStore(path)
    data = store.load()
    assert data["zoom_percent"] == 100
    assert store.last_load_error
    assert store.corrupt_backup is not None
    assert store.corrupt_backup.read_text(encoding="utf-8") == "{ kaputt"


def test_settings_save_is_atomic_and_valid_json(tmp_path: Path):
    store = SettingsStore(tmp_path / "settings.json")
    store.save({"zoom_percent": 150, "cpu_cores": 2})
    payload = json.loads(store.path.read_text(encoding="utf-8"))
    assert payload["zoom_percent"] == 150
    assert payload["cpu_cores"] == 2


def test_atomic_virtual_import_rolls_back_on_failed_postcheck(tmp_path: Path):
    db = Database(tmp_path / "state.sqlite3")
    db.initialize()
    state = {
        "collections": [{"id": 1, "name": "Neu", "note": ""}],
        "collection_items": [],
        "virtual_items": [],
    }
    with pytest.raises(ValueError):
        db.import_virtual_state_atomic(
            state,
            expected_names={"Neu", "Fehlt"},
        )
    assert {item.name for item in db.collections()} == set()


def test_import_validation_rejects_unknown_collection_reference():
    payload = {
        "format": "PROVOWARE-DUPLIKATE-FINDER-STATE",
        "version": "1.0.0",
        "settings": {},
        "virtual_state": {
            "collections": [{"id": 1, "name": "A", "note": ""}],
            "collection_items": [
                {"collection_id": 99, "path": "/tmp/x", "note": ""}
            ],
            "virtual_items": [],
        },
    }
    with pytest.raises(ValueError):
        validate_import_payload(payload)


def test_hash_rejects_file_changed_since_inventory(tmp_path: Path):
    path = tmp_path / "a.bin"
    path.write_bytes(b"abc")
    record = _record(path)
    path.write_bytes(b"abcd")
    with pytest.raises(FileChangedError):
        stable_sha256(record)


def test_duplicate_database_pipeline_and_hash_cache(tmp_path: Path):
    root = tmp_path / "files"
    root.mkdir()
    a = root / "a.bin"
    b = root / "b.bin"
    c = root / "c.bin"
    a.write_bytes(b"x" * 200_000)
    b.write_bytes(b"x" * 200_000)
    c.write_bytes(b"y" * 200_000)

    db = Database(tmp_path / "state.sqlite3")
    db.initialize()
    scanned, groups, errors = scan_duplicate_groups_to_database(
        root,
        db,
        scanner=FileScanner(),
    )
    assert scanned == 3
    assert groups == 1
    assert errors == 0
    summaries = db.duplicate_group_summaries()
    assert len(summaries) == 1
    group_id, _digest, size, members = summaries[0]
    assert size == 200_000
    assert members == 2
    assert db.duplicate_member_count(group_id) == 2
    assert db.cached_sha256(_record(a)) is not None


def test_old_search_jobs_are_pruned(tmp_path: Path):
    db = Database(tmp_path / "state.sqlite3")
    db.initialize()
    for index in range(12):
        job = SearchJob(tmp_path, f"q{index}")
        job_id = db.create_search_job(job)
        db.finish_search_job(
            job_id,
            status="fertig",
            scanned_files=0,
            hit_count=0,
        )
    removed = db.prune_search_jobs(keep=5)
    assert removed == 7
    with db.connect() as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS count FROM search_jobs"
        ).fetchone()["count"]
    assert count == 5


def test_collection_model_pages_database_rows(tmp_path: Path):
    db = Database(tmp_path / "state.sqlite3")
    db.initialize()
    collection_id = db.create_collection("Viele")
    with db.connect() as connection:
        connection.executemany(
            "INSERT INTO collection_items(collection_id,path,note) VALUES(?,?,?)",
            [
                (collection_id, f"/tmp/datei-{index:05d}.txt", "n")
                for index in range(5000)
            ],
        )
    model = CollectionItemsModel(db, page_size=100, max_pages=3)
    model.set_collection(collection_id)
    assert model.rowCount() == 5000
    assert model.cached_row_count == 0
    assert model.path_at(0) == Path("/tmp/datei-00000.txt")
    assert model.cached_row_count <= 100
    assert model.path_at(4999) == Path("/tmp/datei-04999.txt")
    assert model.cached_row_count <= 200


def test_duplicate_member_model_pages_database_rows(tmp_path: Path):
    db = Database(tmp_path / "state.sqlite3")
    db.initialize()
    paths = tuple(Path(f"/tmp/dupe-{index:05d}.bin") for index in range(3000))
    db.replace_duplicate_groups([DuplicateGroup("a" * 64, 10, paths)])
    group_id, _digest, size, count = db.duplicate_group_summaries()[0]
    model = DuplicateMembersModel(db, page_size=100, max_pages=3)
    model.set_group_id(group_id, size=size, count=count)
    assert model.rowCount() == 3000
    assert model.cached_row_count == 0
    assert model.path_at(0) == Path("/tmp/dupe-00000.bin")
    assert model.cached_row_count <= 100
    assert model.path_at(2999) == Path("/tmp/dupe-02999.bin")
    assert model.cached_row_count <= 200
