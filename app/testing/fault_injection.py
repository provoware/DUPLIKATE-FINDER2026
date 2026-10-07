from __future__ import annotations

import errno
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from app.settings_store import SettingsStore
from app.state_portability import export_state
from app.storage.database import Database
from app.testing.sandbox import TestSandbox


@dataclass(frozen=True)
class FaultInjectionResult:
    sqlite_write_ok: bool
    sqlite_read_ok: bool
    disk_full_settings_ok: bool
    disk_full_export_ok: bool
    permission_settings_ok: bool
    permission_export_ok: bool

    @property
    def sqlite_ok(self) -> bool:
        return self.sqlite_write_ok and self.sqlite_read_ok

    @property
    def disk_full_ok(self) -> bool:
        return self.disk_full_settings_ok and self.disk_full_export_ok

    @property
    def permission_ok(self) -> bool:
        return self.permission_settings_ok and self.permission_export_ok

    @property
    def ok(self) -> bool:
        return self.sqlite_ok and self.disk_full_ok and self.permission_ok

    @property
    def detail(self) -> str:
        return (
            f"SQLite Schreiben {'OK' if self.sqlite_write_ok else 'FEHLER'} · "
            f"SQLite Lesen {'OK' if self.sqlite_read_ok else 'FEHLER'} · "
            f"Voll/Einstellungen {'OK' if self.disk_full_settings_ok else 'FEHLER'} · "
            f"Voll/Export {'OK' if self.disk_full_export_ok else 'FEHLER'} · "
            f"Rechte/Einstellungen {'OK' if self.permission_settings_ok else 'FEHLER'} · "
            f"Rechte/Export {'OK' if self.permission_export_ok else 'FEHLER'}"
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
    """Prüft reproduzierbare Speicherfehler ohne echten Datenträger zu gefährden."""
    with TestSandbox.create(sandbox_parent) as sandbox:
        database = Database(sandbox.state_dir / "faults.sqlite3")
        database.initialize()
        example = sandbox.files_dir / "beispiel.txt"
        example.write_text("Fehler-Injektion\n", encoding="utf-8")

        with patch.object(
            database,
            "connect",
            side_effect=sqlite3.OperationalError("simulierter SQLite-Schreibfehler"),
        ):
            sqlite_write_ok = _raises_expected(
                lambda: database.set_virtual_item(example, True, "Test"),
                sqlite3.Error,
            )

        with patch.object(
            database,
            "connect",
            side_effect=sqlite3.OperationalError("simulierter SQLite-Lesefehler"),
        ):
            sqlite_read_ok = _raises_expected(
                database.collections,
                sqlite3.Error,
            )

        store = SettingsStore(sandbox.state_dir / "settings.json")

        with patch(
            "app.settings_store.atomic_write_text",
            side_effect=OSError(errno.ENOSPC, "simulierter voller Datenträger"),
        ):
            disk_full_settings_ok = _raises_expected(
                lambda: store.save({"zoom_percent": 100}),
                OSError,
            )

        with patch(
            "app.state_portability.atomic_write_text",
            side_effect=OSError(errno.ENOSPC, "simulierter voller Datenträger"),
        ):
            disk_full_export_ok = _raises_expected(
                lambda: export_state(
                    database,
                    sandbox.state_dir / "export.json",
                    {"zoom_percent": 100},
                ),
                OSError,
            )

        permission_error = PermissionError(
            errno.EACCES,
            "simulierte fehlende Schreibrechte",
        )
        with patch(
            "app.settings_store.atomic_write_text",
            side_effect=permission_error,
        ):
            permission_settings_ok = _raises_expected(
                lambda: store.save({"zoom_percent": 100}),
                PermissionError,
            )

        with patch(
            "app.state_portability.atomic_write_text",
            side_effect=PermissionError(
                errno.EACCES,
                "simulierte fehlende Schreibrechte",
            ),
        ):
            permission_export_ok = _raises_expected(
                lambda: export_state(
                    database,
                    sandbox.state_dir / "export-ohne-rechte.json",
                    {"zoom_percent": 100},
                ),
                PermissionError,
            )

        return FaultInjectionResult(
            sqlite_write_ok=sqlite_write_ok,
            sqlite_read_ok=sqlite_read_ok,
            disk_full_settings_ok=disk_full_settings_ok,
            disk_full_export_ok=disk_full_export_ok,
            permission_settings_ok=permission_settings_ok,
            permission_export_ok=permission_export_ok,
        )
