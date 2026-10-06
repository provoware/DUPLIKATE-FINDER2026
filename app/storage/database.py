from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

from app.models.entities import (
    Collection,
    CollectionItem,
    DuplicateGroup,
    FileRecord,
    ScanIssue,
    SearchHit,
    SearchJob,
    VirtualItemState,
)
from app.safety.policy import WRITE_FEATURES
from app.storage.migrations import LATEST_SCHEMA_VERSION, apply_migrations


SCHEMA_VERSION = str(LATEST_SCHEMA_VERSION)

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
    indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    device INTEGER NOT NULL DEFAULT 0,
    inode INTEGER NOT NULL DEFAULT 0,
    quick_hash TEXT,
    verified_at TEXT
);
CREATE TABLE IF NOT EXISTS search_jobs (
    id INTEGER PRIMARY KEY,
    root TEXT NOT NULL,
    query TEXT NOT NULL,
    status TEXT NOT NULL,
    scanned_files INTEGER NOT NULL DEFAULT 0,
    hit_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    error_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS search_hits (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES search_jobs(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    line_number INTEGER,
    excerpt TEXT NOT NULL,
    source TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_search_hits_job_id_id ON search_hits(job_id,id);
CREATE INDEX IF NOT EXISTS idx_search_hits_job_path ON search_hits(job_id,path);
CREATE INDEX IF NOT EXISTS idx_search_hits_job_source ON search_hits(job_id,source);
CREATE INDEX IF NOT EXISTS idx_search_hits_job_line ON search_hits(job_id,line_number);
CREATE TABLE IF NOT EXISTS duplicate_groups (
    id INTEGER PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE,
    size INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS duplicate_members (
    group_id INTEGER NOT NULL REFERENCES duplicate_groups(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    size INTEGER NOT NULL DEFAULT 0,
    mtime_ns INTEGER NOT NULL DEFAULT 0,
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
CREATE TABLE IF NOT EXISTS scan_runs (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    root TEXT NOT NULL,
    status TEXT NOT NULL,
    scanned_files INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS scan_inventory (
    run_id INTEGER NOT NULL REFERENCES scan_runs(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    device INTEGER NOT NULL DEFAULT 0,
    inode INTEGER NOT NULL DEFAULT 0,
    quick_hash TEXT,
    sha256 TEXT,
    PRIMARY KEY(run_id, path)
);
CREATE INDEX IF NOT EXISTS idx_scan_inventory_run_size ON scan_inventory(run_id,size);
CREATE INDEX IF NOT EXISTS idx_scan_inventory_run_quick ON scan_inventory(run_id,size,quick_hash);
CREATE INDEX IF NOT EXISTS idx_scan_inventory_run_sha ON scan_inventory(run_id,size,sha256);
CREATE TABLE IF NOT EXISTS scan_errors (
    id INTEGER PRIMARY KEY,
    run_id INTEGER REFERENCES scan_runs(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    stage TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_scan_errors_run_id ON scan_errors(run_id,id);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            apply_migrations(connection)
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

    def schema_version(self) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_state WHERE key='schema_version'"
            ).fetchone()
        return int(row["value"]) if row is not None else 0

    # ---------------- Suche ----------------

    def create_search_job(self, job: SearchJob) -> int:
        with self.connect() as connection:
            cur = connection.execute(
                "INSERT INTO search_jobs(root,query,status,scanned_files,hit_count,error_count) "
                "VALUES(?,?,?,?,0,0)",
                (str(job.root), job.query, job.status.value, 0),
            )
            return int(cur.lastrowid)

    def append_search_hits(self, job_id: int, hits: list[SearchHit]) -> None:
        if not hits:
            return
        with self.connect() as connection:
            connection.executemany(
                "INSERT INTO search_hits(job_id,path,line_number,excerpt,source) VALUES(?,?,?,?,?)",
                [
                    (job_id, str(hit.path), hit.line_number, hit.excerpt, hit.source)
                    for hit in hits
                ],
            )

    def finish_search_job(
        self,
        job_id: int,
        *,
        status: str,
        scanned_files: int,
        hit_count: int,
        error_count: int = 0,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE search_jobs SET status=?,scanned_files=?,hit_count=?,error_count=? WHERE id=?",
                (status, int(scanned_files), int(hit_count), int(error_count), int(job_id)),
            )

    def prune_search_jobs(self, keep: int = 25) -> int:
        keep = max(1, int(keep))
        with self.connect() as connection:
            cur = connection.execute(
                "DELETE FROM search_jobs WHERE id NOT IN "
                "(SELECT id FROM search_jobs ORDER BY id DESC LIMIT ?) "
                "AND status != ?",
                (keep, "laeuft"),
            )
            return max(0, int(cur.rowcount))

    def search_hit_count(self, job_id: int) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT hit_count FROM search_jobs WHERE id=?", (int(job_id),)
            ).fetchone()
        return int(row["hit_count"]) if row is not None else 0

    def search_hits_page(
        self,
        job_id: int,
        *,
        offset: int,
        limit: int,
        sort_column: int = 2,
        descending: bool = False,
    ) -> list[tuple[SearchHit, bool]]:
        order_map = {
            0: "COALESCE(v.marked,0)",
            1: "h.source COLLATE NOCASE",
            2: "h.path COLLATE NOCASE",
            3: "COALESCE(h.line_number,-1)",
            4: "h.excerpt COLLATE NOCASE",
        }
        order = order_map.get(int(sort_column), order_map[2])
        direction = "DESC" if descending else "ASC"
        sql = (
            "SELECT h.path,h.line_number,h.excerpt,h.source,COALESCE(v.marked,0) AS marked "
            "FROM search_hits h LEFT JOIN virtual_items v ON v.path=h.path "
            "WHERE h.job_id=? "
            f"ORDER BY {order} {direction}, h.id ASC LIMIT ? OFFSET ?"
        )
        with self.connect() as connection:
            rows = connection.execute(
                sql, (int(job_id), max(1, int(limit)), max(0, int(offset)))
            ).fetchall()
        return [
            (
                SearchHit(
                    Path(row["path"]),
                    None if row["line_number"] is None else int(row["line_number"]),
                    row["excerpt"],
                    row["source"],
                ),
                bool(row["marked"]),
            )
            for row in rows
        ]

    # ---------------- Scan-Inventar ----------------

    def create_scan_run(self, kind: str, root: Path) -> int:
        with self.connect() as connection:
            cur = connection.execute(
                "INSERT INTO scan_runs(kind,root,status) VALUES(?,?,?)",
                (str(kind), str(root), "laeuft"),
            )
            return int(cur.lastrowid)

    def append_scan_inventory(self, run_id: int, records: list[FileRecord]) -> None:
        if not records:
            return
        with self.connect() as connection:
            connection.executemany(
                "INSERT OR REPLACE INTO scan_inventory"
                "(run_id,path,size,mtime_ns,device,inode,quick_hash,sha256) "
                "VALUES(?,?,?,?,?,?,NULL,NULL)",
                [
                    (
                        int(run_id),
                        str(record.path),
                        int(record.size),
                        int(record.mtime_ns),
                        int(record.device),
                        int(record.inode),
                    )
                    for record in records
                ],
            )

    def record_scan_issue(self, run_id: int, issue: ScanIssue) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO scan_errors(run_id,path,stage,message) VALUES(?,?,?,?)",
                (int(run_id), str(issue.path), issue.stage, issue.message),
            )
            connection.execute(
                "UPDATE scan_runs SET error_count=error_count+1 WHERE id=?",
                (int(run_id),),
            )

    def scan_error_count(self, run_id: int) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM scan_errors WHERE run_id=?",
                (int(run_id),),
            ).fetchone()
        return int(row["count"]) if row else 0

    def scan_inventory_totals(self, run_id: int) -> tuple[int, int]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count,COALESCE(SUM(size),0) AS bytes "
                "FROM scan_inventory WHERE run_id=?",
                (int(run_id),),
            ).fetchone()
        return (int(row["count"]), int(row["bytes"])) if row else (0, 0)

    def iter_scan_records(self, run_id: int) -> Iterator[FileRecord]:
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT path,size,mtime_ns,device,inode,sha256 "
                "FROM scan_inventory WHERE run_id=? ORDER BY path",
                (int(run_id),),
            )
            for row in cursor:
                yield FileRecord(
                    Path(row["path"]),
                    int(row["size"]),
                    int(row["mtime_ns"]),
                    row["sha256"],
                    int(row["device"]),
                    int(row["inode"]),
                )

    def duplicate_candidate_totals(self, run_id: int) -> tuple[int, int]:
        sql = """
        SELECT COUNT(*) AS count,COALESCE(SUM(i.size),0) AS bytes
        FROM scan_inventory i
        JOIN (
            SELECT size FROM scan_inventory
            WHERE run_id=?
            GROUP BY size HAVING COUNT(*)>1
        ) c ON c.size=i.size
        WHERE i.run_id=?
        """
        with self.connect() as connection:
            row = connection.execute(sql, (int(run_id), int(run_id))).fetchone()
        return (int(row["count"]), int(row["bytes"])) if row else (0, 0)

    def iter_duplicate_size_candidates(self, run_id: int) -> Iterator[FileRecord]:
        sql = """
        SELECT i.path,i.size,i.mtime_ns,i.device,i.inode
        FROM scan_inventory i
        JOIN (
            SELECT size FROM scan_inventory
            WHERE run_id=?
            GROUP BY size HAVING COUNT(*)>1
        ) c ON c.size=i.size
        WHERE i.run_id=?
        ORDER BY i.size,i.path
        """
        with self.connect() as connection:
            for row in connection.execute(sql, (int(run_id), int(run_id))):
                yield FileRecord(
                    Path(row["path"]),
                    int(row["size"]),
                    int(row["mtime_ns"]),
                    None,
                    int(row["device"]),
                    int(row["inode"]),
                )

    def set_inventory_quick_hash(self, run_id: int, path: Path, digest: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE scan_inventory SET quick_hash=? WHERE run_id=? AND path=?",
                (digest, int(run_id), str(path)),
            )

    def full_hash_candidate_totals(self, run_id: int) -> tuple[int, int]:
        sql = """
        SELECT COUNT(*) AS count,COALESCE(SUM(i.size),0) AS bytes
        FROM scan_inventory i
        JOIN (
            SELECT size,quick_hash FROM scan_inventory
            WHERE run_id=? AND quick_hash IS NOT NULL
            GROUP BY size,quick_hash HAVING COUNT(*)>1
        ) c ON c.size=i.size AND c.quick_hash=i.quick_hash
        WHERE i.run_id=?
        """
        with self.connect() as connection:
            row = connection.execute(sql, (int(run_id), int(run_id))).fetchone()
        return (int(row["count"]), int(row["bytes"])) if row else (0, 0)

    def iter_full_hash_candidates(self, run_id: int) -> Iterator[FileRecord]:
        sql = """
        SELECT i.path,i.size,i.mtime_ns,i.device,i.inode
        FROM scan_inventory i
        JOIN (
            SELECT size,quick_hash FROM scan_inventory
            WHERE run_id=? AND quick_hash IS NOT NULL
            GROUP BY size,quick_hash HAVING COUNT(*)>1
        ) c ON c.size=i.size AND c.quick_hash=i.quick_hash
        WHERE i.run_id=?
        ORDER BY i.size,i.quick_hash,i.path
        """
        with self.connect() as connection:
            for row in connection.execute(sql, (int(run_id), int(run_id))):
                yield FileRecord(
                    Path(row["path"]),
                    int(row["size"]),
                    int(row["mtime_ns"]),
                    None,
                    int(row["device"]),
                    int(row["inode"]),
                )

    def set_inventory_sha256(self, run_id: int, path: Path, digest: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE scan_inventory SET sha256=? WHERE run_id=? AND path=?",
                (digest, int(run_id), str(path)),
            )

    def finish_scan_run(self, run_id: int, status: str, scanned_files: int) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE scan_runs SET status=?,scanned_files=?,finished_at=CURRENT_TIMESTAMP "
                "WHERE id=?",
                (status, int(scanned_files), int(run_id)),
            )

    def prune_scan_runs(self, keep: int = 5) -> int:
        keep = max(1, int(keep))
        with self.connect() as connection:
            cur = connection.execute(
                "DELETE FROM scan_runs WHERE id NOT IN "
                "(SELECT id FROM scan_runs ORDER BY id DESC LIMIT ?) "
                "AND status != 'laeuft'",
                (keep,),
            )
            return max(0, int(cur.rowcount))

    # ---------------- Hash-Zwischenspeicher ----------------

    def cached_sha256(self, record: FileRecord) -> str | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT sha256 FROM files WHERE path=? AND size=? AND mtime_ns=? "
                "AND device=? AND inode=? AND sha256 IS NOT NULL",
                (
                    str(record.path),
                    int(record.size),
                    int(record.mtime_ns),
                    int(record.device),
                    int(record.inode),
                ),
            ).fetchone()
        return str(row["sha256"]) if row and row["sha256"] else None

    def cache_sha256(self, record: FileRecord, digest: str, quick_hash: str | None = None) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO files(path,size,mtime_ns,sha256,device,inode,quick_hash,verified_at) "
                "VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP) "
                "ON CONFLICT(path) DO UPDATE SET "
                "size=excluded.size,mtime_ns=excluded.mtime_ns,sha256=excluded.sha256,"
                "device=excluded.device,inode=excluded.inode,quick_hash=excluded.quick_hash,"
                "verified_at=CURRENT_TIMESTAMP,indexed_at=CURRENT_TIMESTAMP",
                (
                    str(record.path),
                    int(record.size),
                    int(record.mtime_ns),
                    digest,
                    int(record.device),
                    int(record.inode),
                    quick_hash,
                ),
            )

    # ---------------- Duplikat-Ergebnisse ----------------

    def persist_duplicates_from_run(self, run_id: int) -> int:
        with self.connect() as connection:
            connection.execute("DELETE FROM duplicate_members")
            connection.execute("DELETE FROM duplicate_groups")
            rows = connection.execute(
                "SELECT sha256,size,COUNT(*) AS count FROM scan_inventory "
                "WHERE run_id=? AND sha256 IS NOT NULL "
                "GROUP BY sha256,size HAVING COUNT(*)>1 "
                "ORDER BY size*COUNT(*) DESC,sha256",
                (int(run_id),),
            ).fetchall()
            for row in rows:
                cur = connection.execute(
                    "INSERT INTO duplicate_groups(sha256,size) VALUES(?,?)",
                    (row["sha256"], int(row["size"])),
                )
                group_id = int(cur.lastrowid)
                connection.execute(
                    "INSERT INTO duplicate_members(group_id,path,size,mtime_ns) "
                    "SELECT ?,path,size,mtime_ns FROM scan_inventory "
                    "WHERE run_id=? AND sha256=? ORDER BY path",
                    (group_id, int(run_id), row["sha256"]),
                )
            return len(rows)

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
                payload = []
                for path in group.paths:
                    try:
                        stat = path.stat()
                        size = int(stat.st_size)
                        mtime_ns = int(stat.st_mtime_ns)
                    except OSError:
                        size = int(group.size)
                        mtime_ns = 0
                    payload.append((group_id, str(path), size, mtime_ns))
                connection.executemany(
                    "INSERT INTO duplicate_members(group_id,path,size,mtime_ns) VALUES(?,?,?,?)",
                    payload,
                )

    def duplicate_groups(self) -> list[tuple[int, DuplicateGroup]]:
        with self.connect() as connection:
            group_rows = list(
                connection.execute(
                    "SELECT id,sha256,size FROM duplicate_groups ORDER BY size DESC,id"
                )
            )
            result: list[tuple[int, DuplicateGroup]] = []
            for row in group_rows:
                members = tuple(
                    Path(member["path"])
                    for member in connection.execute(
                        "SELECT path FROM duplicate_members WHERE group_id=? ORDER BY path",
                        (row["id"],),
                    )
                )
                result.append(
                    (
                        int(row["id"]),
                        DuplicateGroup(row["sha256"], int(row["size"]), members),
                    )
                )
            return result

    def duplicate_group_summaries(self) -> list[tuple[int, str, int, int]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT g.id,g.sha256,g.size,COUNT(m.path) AS members "
                "FROM duplicate_groups g JOIN duplicate_members m ON m.group_id=g.id "
                "GROUP BY g.id,g.sha256,g.size "
                "ORDER BY g.size*COUNT(m.path) DESC,g.sha256"
            ).fetchall()
        return [
            (int(row["id"]), row["sha256"], int(row["size"]), int(row["members"]))
            for row in rows
        ]

    def duplicate_member_count(self, group_id: int) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM duplicate_members WHERE group_id=?",
                (int(group_id),),
            ).fetchone()
        return int(row["count"]) if row else 0

    def duplicate_members_page(
        self,
        group_id: int,
        *,
        offset: int,
        limit: int,
        sort_column: int = 0,
        descending: bool = False,
    ) -> list[tuple[Path, int, int]]:
        order_map = {
            0: "path COLLATE NOCASE",
            1: "path COLLATE NOCASE",
            2: "size",
            3: "mtime_ns",
        }
        order = order_map.get(int(sort_column), order_map[0])
        direction = "DESC" if descending else "ASC"
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT path,size,mtime_ns FROM duplicate_members WHERE group_id=? "
                f"ORDER BY {order} {direction},path COLLATE NOCASE LIMIT ? OFFSET ?",
                (int(group_id), max(1, int(limit)), max(0, int(offset))),
            ).fetchall()
        return [
            (Path(row["path"]), int(row["size"]), int(row["mtime_ns"]))
            for row in rows
        ]

    # ---------------- Virtuelle Organisation ----------------

    def feature_flags(self) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(
                connection.execute(
                    "SELECT key,label,enabled,locked FROM feature_flags ORDER BY key"
                )
            )

    def set_virtual_item(self, path: Path, marked: bool, note: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO virtual_items(path,marked,note,updated_at) "
                "VALUES(?,?,?,CURRENT_TIMESTAMP) "
                "ON CONFLICT(path) DO UPDATE SET marked=excluded.marked,"
                "note=excluded.note,updated_at=CURRENT_TIMESTAMP",
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
        return [
            Collection(int(row["id"]), row["name"], row["note"])
            for row in rows
        ]

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

    def collection_item_count(self, collection_id: int) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM collection_items WHERE collection_id=?",
                (int(collection_id),),
            ).fetchone()
        return int(row["count"]) if row else 0

    def collection_items_page(
        self,
        collection_id: int,
        *,
        offset: int,
        limit: int,
        sort_column: int = 0,
        descending: bool = False,
    ) -> list[CollectionItem]:
        order_map = {
            0: "path COLLATE NOCASE",
            1: "path COLLATE NOCASE",
            2: "note COLLATE NOCASE",
        }
        order = order_map.get(int(sort_column), order_map[0])
        direction = "DESC" if descending else "ASC"
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT collection_id,path,note FROM collection_items "
                f"WHERE collection_id=? ORDER BY {order} {direction},path COLLATE NOCASE "
                "LIMIT ? OFFSET ?",
                (int(collection_id), max(1, int(limit)), max(0, int(offset))),
            ).fetchall()
        return [
            CollectionItem(int(row["collection_id"]), Path(row["path"]), row["note"])
            for row in rows
        ]

    def collection_items(self, collection_id: int) -> list[CollectionItem]:
        count = self.collection_item_count(collection_id)
        return self.collection_items_page(
            collection_id, offset=0, limit=max(1, count)
        )

    def export_virtual_state(self) -> dict:
        with self.connect() as connection:
            collections = [
                {"id": int(row["id"]), "name": row["name"], "note": row["note"]}
                for row in connection.execute(
                    "SELECT id,name,note FROM collections ORDER BY id"
                )
            ]
            collection_items = [
                {
                    "collection_id": int(row["collection_id"]),
                    "path": row["path"],
                    "note": row["note"],
                }
                for row in connection.execute(
                    "SELECT collection_id,path,note FROM collection_items "
                    "ORDER BY collection_id,path"
                )
            ]
            virtual_items = [
                {
                    "path": row["path"],
                    "marked": bool(row["marked"]),
                    "note": row["note"],
                }
                for row in connection.execute(
                    "SELECT path,marked,note FROM virtual_items ORDER BY path"
                )
            ]
        return {
            "collections": collections,
            "collection_items": collection_items,
            "virtual_items": virtual_items,
        }

    @staticmethod
    def _import_virtual_state_connection(
        connection: sqlite3.Connection, state: dict
    ) -> None:
        collections = state.get("collections", [])
        items = state.get("collection_items", [])
        virtual = state.get("virtual_items", [])
        id_map: dict[int, int] = {}

        for row in collections:
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            note = str(row.get("note", ""))
            existing = connection.execute(
                "SELECT id FROM collections WHERE name=?", (name,)
            ).fetchone()
            if existing is None:
                cur = connection.execute(
                    "INSERT INTO collections(name,note) VALUES(?,?)", (name, note)
                )
                new_id = int(cur.lastrowid)
            else:
                new_id = int(existing["id"])
                connection.execute(
                    "UPDATE collections SET note=? WHERE id=?", (note, new_id)
                )
            id_map[int(row.get("id", new_id))] = new_id

        for row in items:
            old_id = int(row.get("collection_id", -1))
            new_id = id_map.get(old_id)
            path = str(row.get("path", "")).strip()
            if new_id is None or not path:
                continue
            connection.execute(
                "INSERT INTO collection_items(collection_id,path,note) VALUES(?,?,?) "
                "ON CONFLICT(collection_id,path) DO UPDATE SET note=excluded.note",
                (new_id, path, str(row.get("note", ""))),
            )

        for row in virtual:
            path = str(row.get("path", "")).strip()
            if not path:
                continue
            connection.execute(
                "INSERT INTO virtual_items(path,marked,note,updated_at) "
                "VALUES(?,?,?,CURRENT_TIMESTAMP) "
                "ON CONFLICT(path) DO UPDATE SET marked=excluded.marked,"
                "note=excluded.note,updated_at=CURRENT_TIMESTAMP",
                (
                    path,
                    int(bool(row.get("marked", False))),
                    str(row.get("note", "")),
                ),
            )

    def import_virtual_state_atomic(
        self, state: dict, expected_names: set[str] | None = None
    ) -> None:
        with self.connect() as connection:
            self._import_virtual_state_connection(connection, state)
            if expected_names:
                actual = {
                    str(row["name"])
                    for row in connection.execute("SELECT name FROM collections")
                }
                missing = expected_names - actual
                if missing:
                    raise ValueError(
                        "Nachprüfung fehlgeschlagen: "
                        + ", ".join(sorted(missing))
                    )

    def import_virtual_state(self, state: dict) -> None:
        self.import_virtual_state_atomic(state)
