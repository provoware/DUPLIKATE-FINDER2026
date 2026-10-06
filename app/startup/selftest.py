from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.safety.policy import SafetyPolicy, SafetyViolation
from app.storage.database import Database
from app.testing.runner import run_profile


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def run_selftest(base_dir: Path, require_gui: bool = True) -> list[Check]:
    checks: list[Check] = []

    py_ok = sys.version_info[:2] == (3, 12)
    checks.append(Check("Python", py_ok, f"Python {sys.version_info.major}.{sys.version_info.minor} aktiv"))

    if require_gui:
        try:
            gui_probe = subprocess.run(
                [sys.executable, "-c", "from PySide6.QtWidgets import QApplication"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            has_pyside = gui_probe.returncode == 0
            gui_detail = (
                "Grafikbibliothek verfügbar"
                if has_pyside
                else "PySide6/Qt konnte nicht geladen werden: " + (gui_probe.stderr.strip().splitlines()[-1] if gui_probe.stderr.strip() else "unbekannter Fehler")
            )
        except (OSError, subprocess.SubprocessError) as exc:
            has_pyside = False
            gui_detail = f"GUI-Prüfung fehlgeschlagen: {exc}"
        checks.append(Check("PySide6", has_pyside, gui_detail))

    for directory_name in ("data", "logs", "recovery", "quarantine", "exports", "reports", "checkpoints", "config"):
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
        free = shutil.disk_usage(base_dir).free
        ok = free >= 50 * 1024 * 1024
        checks.append(Check("Freier Speicher", ok, f"{free // (1024 * 1024)} MB frei"))
    except OSError as exc:
        checks.append(Check("Freier Speicher", False, str(exc)))

    try:
        with tempfile.TemporaryDirectory() as temp:
            db = Database(Path(temp) / "selftest.sqlite3")
            db.initialize()
            with db.connect() as con:
                integrity = con.execute("PRAGMA quick_check").fetchone()[0]
                mode = con.execute("SELECT value FROM app_state WHERE key='safety_mode'").fetchone()[0]
                flags = con.execute("SELECT COUNT(*) FROM feature_flags WHERE enabled<>0 OR locked<>1").fetchone()[0]
            ok = integrity == "ok" and mode == "read_only" and flags == 0
            checks.append(Check("SQLite", ok, "Datenbank, Integrität und Nur-Lesen-Vertrag geprüft"))
    except (OSError, sqlite3.Error) as exc:
        checks.append(Check("SQLite", False, str(exc)))

    try:
        SafetyPolicy().ensure_scan_root_allowed(Path("/etc"))
        checks.append(Check("Systemschutz", False, "Sperre hat /etc nicht blockiert"))
    except SafetyViolation:
        checks.append(Check("Systemschutz", True, "Kritische Systembereiche werden blockiert"))

    try:
        result = run_profile("mini")
        checks.append(
            Check(
                "Dateisystem-Test",
                result.ok,
                result.detail,
            )
        )
    except Exception as exc:
        checks.append(Check("Dateisystem-Test", False, str(exc)))

    return checks
