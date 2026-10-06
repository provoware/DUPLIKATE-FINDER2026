from __future__ import annotations

import sqlite3
from collections.abc import Callable


LATEST_SCHEMA_VERSION = 2


def _column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row[1] == column for row in connection.execute(f"PRAGMA table_info({table})"))


def _add_column(connection: sqlite3.Connection, table: str, definition: str) -> None:
    column = definition.split()[0]
    if not _column_exists(connection, table, column):
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def _migration_2(connection: sqlite3.Connection) -> None:
    _add_column(connection, "files", "device INTEGER NOT NULL DEFAULT 0")
    _add_column(connection, "files", "inode INTEGER NOT NULL DEFAULT 0")
    _add_column(connection, "files", "quick_hash TEXT")
    _add_column(connection, "files", "verified_at TEXT")
    _add_column(connection, "search_jobs", "error_count INTEGER NOT NULL DEFAULT 0")
    _add_column(connection, "duplicate_members", "size INTEGER NOT NULL DEFAULT 0")
    _add_column(connection, "duplicate_members", "mtime_ns INTEGER NOT NULL DEFAULT 0")

    statements = (
        """CREATE TABLE IF NOT EXISTS scan_runs (
            id INTEGER PRIMARY KEY,
            kind TEXT NOT NULL,
            root TEXT NOT NULL,
            status TEXT NOT NULL,
            scanned_files INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS scan_inventory (
            run_id INTEGER NOT NULL REFERENCES scan_runs(id) ON DELETE CASCADE,
            path TEXT NOT NULL,
            size INTEGER NOT NULL,
            mtime_ns INTEGER NOT NULL,
            device INTEGER NOT NULL DEFAULT 0,
            inode INTEGER NOT NULL DEFAULT 0,
            quick_hash TEXT,
            sha256 TEXT,
            PRIMARY KEY(run_id, path)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_scan_inventory_run_size ON scan_inventory(run_id,size)",
        "CREATE INDEX IF NOT EXISTS idx_scan_inventory_run_quick ON scan_inventory(run_id,size,quick_hash)",
        "CREATE INDEX IF NOT EXISTS idx_scan_inventory_run_sha ON scan_inventory(run_id,size,sha256)",
        """CREATE TABLE IF NOT EXISTS scan_errors (
            id INTEGER PRIMARY KEY,
            run_id INTEGER REFERENCES scan_runs(id) ON DELETE CASCADE,
            path TEXT NOT NULL,
            stage TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""",
        "CREATE INDEX IF NOT EXISTS idx_scan_errors_run_id ON scan_errors(run_id,id)",
    )
    for statement in statements:
        connection.execute(statement)


MIGRATIONS: dict[int, Callable[[sqlite3.Connection], None]] = {
    2: _migration_2,
}


def current_schema_version(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        "SELECT value FROM app_state WHERE key='schema_version'"
    ).fetchone()
    if row is None:
        return 1
    try:
        return int(row[0])
    except (TypeError, ValueError):
        return 1


def apply_migrations(connection: sqlite3.Connection) -> int:
    current = current_schema_version(connection)
    if current > LATEST_SCHEMA_VERSION:
        raise RuntimeError(
            f"Datenbank-Schema {current} ist neuer als unterstützt ({LATEST_SCHEMA_VERSION})."
        )

    for target in range(current + 1, LATEST_SCHEMA_VERSION + 1):
        migration = MIGRATIONS.get(target)
        if migration is None:
            raise RuntimeError(f"Migration auf Schema {target} fehlt.")
        savepoint = f"migration_{target}"
        connection.execute(f"SAVEPOINT {savepoint}")
        try:
            migration(connection)
            connection.execute(
                "INSERT INTO app_state(key,value) VALUES('schema_version',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(target),),
            )
            connection.execute(f"RELEASE SAVEPOINT {savepoint}")
        except Exception:
            connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            connection.execute(f"RELEASE SAVEPOINT {savepoint}")
            raise
        current = target
    return current
