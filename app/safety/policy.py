from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


BLOCKED_SYSTEM_ROOTS = (
    Path("/bin"), Path("/boot"), Path("/dev"), Path("/etc"), Path("/lib"),
    Path("/lib64"), Path("/proc"), Path("/root"), Path("/run"), Path("/sbin"),
    Path("/sys"), Path("/usr"), Path("/var"),
)

SAFE_RUNTIME_MEDIA_ROOT = Path("/run/media")

WRITE_FEATURES = {
    "move_files": "Verschieben",
    "rename_files": "Umbenennen",
    "quarantine": "Quarantäne",
    "delete_files": "Löschen",
}


class SafetyViolation(RuntimeError):
    pass


@dataclass(frozen=True)
class SafetyPolicy:
    read_only: bool = True
    follow_symlinks: bool = False

    def ensure_scan_root_allowed(self, root: Path) -> Path:
        resolved = root.expanduser().resolve(strict=False)
        if resolved == Path("/"):
            raise SafetyViolation("Das gesamte Linux-System darf nicht als Suchwurzel verwendet werden.")

        # Einige Linux-Distributionen hängen Wechseldatenträger unter
        # /run/media/<benutzer>/... ein. Nur dieser eng begrenzte
        # Benutzer-Mountbereich ist eine Ausnahme von der /run-Sperre.
        runtime_media = (
            SAFE_RUNTIME_MEDIA_ROOT in resolved.parents
            and resolved != SAFE_RUNTIME_MEDIA_ROOT
            and len(resolved.relative_to(SAFE_RUNTIME_MEDIA_ROOT).parts) >= 2
        )
        for blocked in BLOCKED_SYSTEM_ROOTS:
            if runtime_media and blocked == Path("/run"):
                continue
            if resolved == blocked or blocked in resolved.parents:
                raise SafetyViolation(f"Systembereich gesperrt: {resolved}")
        return resolved

    def ensure_write_action_allowed(self, action: str) -> None:
        if action in WRITE_FEATURES and self.read_only:
            raise SafetyViolation(
                f"{WRITE_FEATURES[action]} ist in Version 1 absichtlich gesperrt (Nur-Lesen-Modus)."
            )
