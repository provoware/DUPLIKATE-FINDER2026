from __future__ import annotations

import sqlite3
from pathlib import Path

from app.models.entities import Collection, CollectionItem, DuplicateGroup, VirtualItemState
from app.safety.policy import WRITE_FEATURES


SCHEMA_VERSION = "1"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    sha256 TEXT,
    indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS search_jobs (
    id INTEGER PRIMARY KEY,
    root TEXT NOT NULL,
    query TEXT NOT NULL,
    status TEXT NOT NULL,
    scanned_files INTEGER NOT NULL DEFAULT 0,
    hit_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS search_hits (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES search_jobs(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    line_number INTEGER,
    excerpt TEXT NOT NULL,
    source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS duplicate_groups (
    id INTEGER PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE,
    size INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS duplicate_members (
    group_id INTEGER NOT NULL REFERENCES duplicate_groups(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    PRIMARY KEY(group_id, path)
);
CREATE TABLE IF NOT EXISTS virtual_items (
    path TEXT PRIMARY KEY,
    marked INTEGER NOT NULL DEFAULT 0 CHECK(marked IN (0,1)),
    note TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS collection_items (
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(collection_id, path)
);
CREATE TABLE IF NOT EXISTS change_journal (
    id INTEGER PRIMARY KEY,
    action TEXT NOT NULL,
    source TEXT NOT NULL,
    target TEXT,
    status TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS feature_flags (
    key TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 0 CHECK(enabled IN (0,1)),
    locked INTEGER NOT NULL DEFAULT 1 CHECK(locked IN (0,1))
);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            for key, label in WRITE_FEATURES.items():
                connection.execute(
                    "INSERT INTO feature_flags(key,label,enabled,locked) VALUES(?,?,0,1) "
                    "ON CONFLICT(key) DO UPDATE SET enabled=0, locked=1, label=excluded.label",
                    (key, label),
                )
            connection.execute(
                "INSERT INTO app_state(key,value) VALUES('safety_mode','read_only') "
                "ON CONFLICT(key) DO UPDATE SET value='read_only'"
            )
            connection.execute(
                "INSERT INTO app_state(key,value) VALUES('schema_version',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (SCHEMA_VERSION,),
            )

    def feature_flags(self) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(connection.execute(
                "SELECT key,label,enabled,locked FROM feature_flags ORDER BY key"
            ))

    def replace_duplicate_groups(self, groups: list[DuplicateGroup]) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM duplicate_members")
            connection.execute("DELETE FROM duplicate_groups")
            for group in groups:
                cur = connection.execute(
                    "INSERT INTO duplicate_groups(sha256,size) VALUES(?,?)",
                    (group.sha256, group.size),
                )
                group_id = int(cur.lastrowid)
                connection.executemany(
                    "INSERT INTO duplicate_members(group_id,path) VALUES(?,?)",
                    [(group_id, str(path)) for path in group.paths],
                )

    def duplicate_groups(self) -> list[tuple[int, DuplicateGroup]]:
        with self.connect() as connection:
            group_rows = list(connection.execute(
                "SELECT id,sha256,size FROM duplicate_groups ORDER BY size DESC, id"
            ))
            result: list[tuple[int, DuplicateGroup]] = []
            for row in group_rows:
                members = tuple(
                    Path(member["path"])
                    for member in connection.execute(
                        "SELECT path FROM duplicate_members WHERE group_id=? ORDER BY path",
                        (row["id"],),
                    )
                )
                result.append((row["id"], DuplicateGroup(row["sha256"], row["size"], members)))
            return result

    def set_virtual_item(self, path: Path, marked: bool, note: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO virtual_items(path,marked,note,updated_at) "
                "VALUES(?,?,?,CURRENT_TIMESTAMP) "
                "ON CONFLICT(path) DO UPDATE SET marked=excluded.marked, "
                "note=excluded.note, updated_at=CURRENT_TIMESTAMP",
                (str(path), int(marked), note),
            )

    def virtual_item(self, path: Path) -> VirtualItemState:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT path,marked,note FROM virtual_items WHERE path=?",
                (str(path),),
            ).fetchone()
        if row is None:
            return VirtualItemState(path=path)
        return VirtualItemState(Path(row["path"]), bool(row["marked"]), row["note"])

    def create_collection(self, name: str, note: str = "") -> int:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Der Sammlungsname darf nicht leer sein.")
        with self.connect() as connection:
            cur = connection.execute(
                "INSERT INTO collections(name,note) VALUES(?,?)",
                (clean_name, note.strip()),
            )
            return int(cur.lastrowid)

    def collections(self) -> list[Collection]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id,name,note FROM collections ORDER BY name COLLATE NOCASE"
            ).fetchall()
        return [Collection(int(row["id"]), row["name"], row["note"]) for row in rows]

    def add_collection_item(self, collection_id: int, path: Path, note: str = "") -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO collection_items(collection_id,path,note) VALUES(?,?,?) "
                "ON CONFLICT(collection_id,path) DO UPDATE SET note=excluded.note",
                (collection_id, str(path), note.strip()),
            )

    def remove_collection_item(self, collection_id: int, path: Path) -> None:
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM collection_items WHERE collection_id=? AND path=?",
                (collection_id, str(path)),
            )

    def collection_items(self, collection_id: int) -> list[CollectionItem]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT collection_id,path,note FROM collection_items "
                "WHERE collection_id=? ORDER BY path COLLATE NOCASE",
                (collection_id,),
            ).fetchall()
        return [
            CollectionItem(int(row["collection_id"]), Path(row["path"]), row["note"])
            for row in rows
        ]

    def export_virtual_state(self) -> dict:
        with self.connect() as connection:
            collections=[
                {"id":int(row["id"]),"name":row["name"],"note":row["note"]}
                for row in connection.execute("SELECT id,name,note FROM collections ORDER BY id")
            ]
            collection_items=[
                {"collection_id":int(row["collection_id"]),"path":row["path"],"note":row["note"]}
                for row in connection.execute(
                    "SELECT collection_id,path,note FROM collection_items ORDER BY collection_id,path"
                )
            ]
            virtual_items=[
                {"path":row["path"],"marked":bool(row["marked"]),"note":row["note"]}
                for row in connection.execute("SELECT path,marked,note FROM virtual_items ORDER BY path")
            ]
        return {
            "collections":collections,
            "collection_items":collection_items,
            "virtual_items":virtual_items,
        }

    def import_virtual_state(self, state: dict) -> None:
        collections=state.get("collections",[])
        items=state.get("collection_items",[])
        virtual=state.get("virtual_items",[])
        with self.connect() as connection:
            id_map={}
            for row in collections:
                name=str(row.get("name","")).strip()
                if not name:
                    continue
                note=str(row.get("note",""))
                existing=connection.execute(
                    "SELECT id FROM collections WHERE name=?",(name,)
                ).fetchone()
                if existing is None:
                    cur=connection.execute(
                        "INSERT INTO collections(name,note) VALUES(?,?)",(name,note)
                    )
                    new_id=int(cur.lastrowid)
                else:
                    new_id=int(existing["id"])
                    connection.execute("UPDATE collections SET note=? WHERE id=?",(note,new_id))
                id_map[int(row.get("id",new_id))]=new_id

            for row in items:
                old_id=int(row.get("collection_id",-1))
                new_id=id_map.get(old_id)
                path=str(row.get("path","")).strip()
                if new_id is None or not path:
                    continue
                connection.execute(
                    "INSERT INTO collection_items(collection_id,path,note) VALUES(?,?,?) "
                    "ON CONFLICT(collection_id,path) DO UPDATE SET note=excluded.note",
                    (new_id,path,str(row.get("note",""))),
                )

            for row in virtual:
                path=str(row.get("path","")).strip()
                if not path:
                    continue
                connection.execute(
                    "INSERT INTO virtual_items(path,marked,note,updated_at) VALUES(?,?,?,CURRENT_TIMESTAMP) "
                    "ON CONFLICT(path) DO UPDATE SET marked=excluded.marked,note=excluded.note,updated_at=CURRENT_TIMESTAMP",
                    (path,int(bool(row.get("marked",False))),str(row.get("note",""))),
                )
