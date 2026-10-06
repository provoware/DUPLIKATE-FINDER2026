from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from app.storage.atomic_io import atomic_write_text


DEFAULT_SETTINGS = {
    "schema_version": "1.0.0",
    "zoom_percent": 100,
    "window_width": 1280,
    "window_height": 800,
    "cpu_cores": 0,
    "exclude_python_project_dirs": True,
    "excluded_extensions": [],
}


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.last_load_error: str | None = None
        self.corrupt_backup: Path | None = None

    def _backup_corrupt_file(self) -> None:
        if not self.path.is_file():
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = self.path.with_name(
            f"{self.path.stem}.beschaedigt-{stamp}{self.path.suffix}"
        )
        try:
            shutil.copy2(self.path, target)
            self.corrupt_backup = target
        except OSError:
            self.corrupt_backup = None

    def load(self) -> dict:
        data = dict(DEFAULT_SETTINGS)
        self.last_load_error = None
        self.corrupt_backup = None
        if not self.path.exists():
            return data
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("Einstellungsdatei enthält kein JSON-Objekt.")
            for key in data:
                if key in raw:
                    data[key] = raw[key]
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            self.last_load_error = str(exc)
            self._backup_corrupt_file()
        return data

    def save(self, data: dict) -> None:
        clean = dict(DEFAULT_SETTINGS)
        clean.update({key: data[key] for key in clean if key in data})
        atomic_write_text(
            self.path,
            json.dumps(clean, ensure_ascii=False, indent=2) + "\n",
        )
