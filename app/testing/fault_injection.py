from __future__ import annotations

import errno
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from app.settings_store import SettingsStore
from app.storage.database import Database
from app.testing.sandbox import TestSandbox


@dataclass(frozen=True)
class FaultInjectionResult:
    sqlite_ok: bool
    disk_full_ok: bool
    permission_ok: bool

    @property
    def ok(self) -> bool:
        return self.sqlite_ok and self.disk_full_ok and self.permission_ok

    @property
    def detail(self) -> str:
        return (
            f"SQLite {'OK' if self.sqlite_ok else 'FEHLER'} · "
            f"Datenträger voll {'OK' if self.disk_full_ok else 'FEHLER'} · "
            f"Schreibrechte {'OK' if self.permission_ok else 'FEHLER'}"
        )


def _raises_expected(callable_, exception_type: type[BaseException]) -> bool:
    try:
        callable_()
    except exception_type:
        return True
    return False


def run_fault_injection_suite(
    *,
    sandbox_parent: Path | None = None,
) -> FaultInjectionResult:
    """Erzeugt reproduzierbare Speicherfehler ohne echten Datenträger zu gefährden."""
    with TestSandbox.create(sandbox_parent) as sandbox:
        database = Database(sandbox.state_dir / "faults.sqlite3")
        database.initialize()

        with patch.object(
            database,
            "connect",
            side_effect=sqlite3.OperationalError("simulierter SQLite-Fehler"),
        ):
            sqlite_ok = _raises_expected(
                lambda: database.set_virtual_item(
                    sandbox.files_dir / "beispiel.txt",
                    True,
                    "Test",
                ),
                sqlite3.Error,
            )

        store = SettingsStore(sandbox.state_dir / "settings.json")

        with patch(
            "app.settings_store.atomic_write_text",
            side_effect=OSError(errno.ENOSPC, "simulierter voller Datenträger"),
        ):
            disk_full_ok = _raises_expected(
                lambda: store.save({"zoom_percent": 100}),
                OSError,
            )

        with patch(
            "app.settings_store.atomic_write_text",
            side_effect=PermissionError(
                errno.EACCES,
                "simulierte fehlende Schreibrechte",
            ),
        ):
            permission_ok = _raises_expected(
                lambda: store.save({"zoom_percent": 100}),
                PermissionError,
            )

        return FaultInjectionResult(
            sqlite_ok=sqlite_ok,
            disk_full_ok=disk_full_ok,
            permission_ok=permission_ok,
        )
