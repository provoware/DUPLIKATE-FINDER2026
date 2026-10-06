from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from app.startup.selftest import Check, run_selftest


def _portable_runtime(base_dir: Path) -> bool:
    expected = (base_dir / "runtime" / "bin" / "python3").resolve(strict=False)
    return Path(sys.executable).resolve(strict=False) == expected


def _gui_import_works() -> bool:
    try:
        completed = subprocess.run(
            [sys.executable, "-c", "from PySide6.QtWidgets import QApplication"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def _repair_gui_dependency(base_dir: Path) -> tuple[bool, str]:
    if _gui_import_works():
        return True, "PySide6 bereits vorhanden"
    if not _portable_runtime(base_dir):
        return False, "PySide6 fehlt. Entwicklungsumgebungen werden absichtlich nicht automatisch verändert."
    wheelhouse = base_dir / "wheelhouse"
    if not wheelhouse.is_dir():
        return False, "Lokales Reparaturpaket (wheelhouse) fehlt."
    command = [
        sys.executable, "-m", "pip", "install",
        "--disable-pip-version-check", "--no-index",
        "--find-links", str(wheelhouse), "PySide6>=6.8,<7",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
    if completed.returncode != 0:
        logging.getLogger(__name__).error("PySide6-Reparatur fehlgeschlagen: %s", completed.stderr[-2000:])
        return False, "Die lokale GUI-Reparatur ist fehlgeschlagen. Details stehen im Protokoll."

    repaired = _gui_import_works()
    return repaired, (
        "PySide6 wurde aus dem lokalen Reparaturpaket wiederhergestellt."
        if repaired
        else "PySide6 wurde installiert, konnte aber noch nicht geladen werden."
    )


def bootstrap(base_dir: Path, require_gui: bool) -> list[Check]:
    for name in ("data", "logs", "recovery", "quarantine"):
        (base_dir / name).mkdir(parents=True, exist_ok=True)
    repair_note = "GUI nicht erforderlich"
    repair_ok = True
    if require_gui:
        repair_ok, repair_note = _repair_gui_dependency(base_dir)
    checks = [Check("Lokale Reparatur", repair_ok, repair_note)]
    checks.extend(run_selftest(base_dir, require_gui=require_gui))
    try:
        (base_dir / "logs" / "startup-status.json").write_text(
            json.dumps({"modus": "gui" if require_gui else "konsole", "checks": [asdict(c) for c in checks]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--console", action="store_true")
    args = parser.parse_args()
    base = Path(__file__).resolve().parents[2]
    checks = bootstrap(base, require_gui=not args.console)
    bad = [c for c in checks if not c.ok]
    for check in checks:
        print(("OK" if check.ok else "FEHLER") + " | " + check.name + " | " + check.detail)
    return 2 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
