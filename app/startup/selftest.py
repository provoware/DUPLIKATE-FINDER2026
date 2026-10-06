from __future__ import annotations

import importlib.util
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.safety.policy import SafetyPolicy, SafetyViolation
from app.storage.database import Database


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def run_selftest(base_dir: Path) -> list[Check]:
    checks: list[Check] = []
    checks.append(Check("Python", True, "Python-Laufzeit verfügbar"))
    has_pyside = importlib.util.find_spec("PySide6") is not None
    checks.append(Check(
        "PySide6",
        has_pyside,
        "Grafikbibliothek verfügbar" if has_pyside else "PySide6 fehlt in der aktiven Laufzeit",
    ))

    for directory_name in ("data", "logs", "recovery"):
        directory = base_dir / directory_name
        try:
            directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=directory, prefix=".write_test_") as probe:
                probe.write(b"ok")
                probe.flush()
            checks.append(Check(directory_name, True, "Arbeitsordner schreibbar"))
        except OSError as exc:
            checks.append(Check(directory_name, False, str(exc)))

    try:
        with tempfile.TemporaryDirectory() as temp:
            db = Database(Path(temp) / "selftest.sqlite3")
            db.initialize()
            with db.connect() as con:
                mode = con.execute(
                    "SELECT value FROM app_state WHERE key='safety_mode'"
                ).fetchone()[0]
            checks.append(Check("SQLite", mode == "read_only", "Datenbank + Nur-Lesen-Vertrag geprüft"))
    except (OSError, sqlite3.Error) as exc:
        checks.append(Check("SQLite", False, str(exc)))

    try:
        SafetyPolicy().ensure_scan_root_allowed(Path("/etc"))
        checks.append(Check("Systemschutz", False, "Sperre hat /etc nicht blockiert"))
    except SafetyViolation:
        checks.append(Check("Systemschutz", True, "Kritische Systembereiche werden blockiert"))

    return checks
