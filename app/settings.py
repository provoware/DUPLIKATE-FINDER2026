from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

SETTINGS_VERSION = "1.0.0"


def detected_cpu_count() -> int:
    return max(1, os.cpu_count() or 1)


def default_cpu_workers() -> int:
    return max(1, detected_cpu_count() // 2)


@dataclass
class AppSettings:
    version: str = SETTINGS_VERSION
    cpu_workers: int = 0
    skip_python_project_dirs: bool = True
    skip_hidden_dirs: bool = False
    excluded_extensions: list[str] = field(default_factory=list)
    zoom_percent: int = 100
    window_width: int = 1280
    window_height: int = 800
    last_root: str = ""
    autosave_minutes: int = 5

    def resolved_cpu_workers(self) -> int:
        available = detected_cpu_count()
        requested = self.cpu_workers if self.cpu_workers > 0 else default_cpu_workers()
        return max(1, min(available, requested))

    def normalize(self) -> None:
        self.version = SETTINGS_VERSION
        self.cpu_workers = max(0, min(detected_cpu_count(), int(self.cpu_workers or 0)))
        self.excluded_extensions = sorted({
            ext.casefold() if ext.startswith(".") else "." + ext.casefold()
            for ext in self.excluded_extensions
            if isinstance(ext, str) and ext.strip()
        })
        self.zoom_percent = int(self.zoom_percent) if int(self.zoom_percent) > 0 else 100
        self.window_width = max(640, int(self.window_width or 1280))
        self.window_height = max(480, int(self.window_height or 800))
        self.autosave_minutes = 5

    def to_dict(self) -> dict:
        self.normalize()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: object) -> "AppSettings":
        if not isinstance(data, dict):
            return cls()
        known = {name for name in cls.__dataclass_fields__}
        filtered = {key: value for key, value in data.items() if key in known}
        settings = cls(**filtered)
        settings.normalize()
        return settings


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> AppSettings:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return AppSettings()
        return AppSettings.from_dict(data)

    def save(self, settings: AppSettings) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(settings.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return self.path
