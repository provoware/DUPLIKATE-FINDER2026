from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from app.core.control import ProcessControl
from app.models.entities import FileRecord
from app.safety.policy import SafetyPolicy


TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".log", ".json", ".xml", ".yaml", ".yml",
    ".ini", ".conf", ".py", ".sh",
}

PYTHON_PROJECT_DIRS = frozenset({
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".nox", ".provoware-dev", "build", "dist",
    "site-packages", "node_modules",
})


@dataclass(frozen=True)
class ScanOptions:
    skip_python_project_dirs: bool = True
    skip_hidden_dirs: bool = False
    excluded_extensions: frozenset[str] = field(default_factory=frozenset)

    def normalized_extensions(self) -> frozenset[str]:
        return frozenset(
            ext.casefold() if ext.startswith(".") else "." + ext.casefold()
            for ext in self.excluded_extensions
            if ext.strip()
        )


class FileScanner:
    def __init__(self, policy: SafetyPolicy | None = None) -> None:
        self.policy = policy or SafetyPolicy()

    def iter_files(
        self,
        root: Path,
        *,
        options: ScanOptions | None = None,
        control: ProcessControl | None = None,
        on_discovered: Callable[[int, Path], None] | None = None,
    ) -> Iterator[FileRecord]:
        """Liefert reguläre Dateien ausschließlich lesend und ohne Symlink-Folgen."""
        safe_root = self.policy.ensure_scan_root_allowed(root)
        if not safe_root.exists() or not safe_root.is_dir():
            return

        active = options or ScanOptions()
        excluded_extensions = active.normalized_extensions()
        found = 0

        for dirpath, dirnames, filenames in os.walk(
            safe_root, followlinks=self.policy.follow_symlinks
        ):
            if control is not None:
                control.checkpoint()
            current = Path(dirpath)

            kept_dirs: list[str] = []
            for name in dirnames:
                candidate = current / name
                if not self.policy.follow_symlinks and candidate.is_symlink():
                    continue
                if active.skip_python_project_dirs and name in PYTHON_PROJECT_DIRS:
                    continue
                if active.skip_hidden_dirs and name.startswith("."):
                    continue
                kept_dirs.append(name)
            dirnames[:] = kept_dirs

            for filename in filenames:
                if control is not None:
                    control.checkpoint()
                path = current / filename
                try:
                    if path.is_symlink() and not self.policy.follow_symlinks:
                        continue
                    if not path.is_file():
                        continue
                    if path.suffix.casefold() in excluded_extensions:
                        continue
                    stat = path.stat()
                    found += 1
                    if on_discovered is not None:
                        on_discovered(found, path)
                    yield FileRecord(path=path, size=stat.st_size, mtime_ns=stat.st_mtime_ns)
                except (OSError, PermissionError):
                    continue

    def iter_text_files(
        self,
        root: Path,
        *,
        options: ScanOptions | None = None,
        control: ProcessControl | None = None,
        on_discovered: Callable[[int, Path], None] | None = None,
    ) -> Iterator[FileRecord]:
        for record in self.iter_files(
            root, options=options, control=control, on_discovered=on_discovered
        ):
            if record.path.suffix.casefold() in TEXT_EXTENSIONS:
                yield record
