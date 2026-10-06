from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from app.models.entities import FileRecord
from app.process_control import ProcessControl, ProgressInfo, ProgressTracker
from app.safety.policy import SafetyPolicy


TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".log", ".json", ".xml", ".yaml", ".yml",
    ".ini", ".conf", ".py", ".sh",
}

DEFAULT_PYTHON_PROJECT_DIRS = frozenset({
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", ".nox", "build", "dist",
    "site-packages", ".provoware-dev", "runtime", "node_modules",
})

ProgressCallback=Callable[[ProgressInfo],None]


@dataclass(frozen=True)
class ScanOptions:
    exclude_python_project_dirs: bool = True
    excluded_dir_names: frozenset[str] = field(default_factory=frozenset)
    excluded_extensions: frozenset[str] = field(default_factory=frozenset)

    def normalized_extensions(self)->frozenset[str]:
        return frozenset(
            value.casefold() if value.startswith(".") else "."+value.casefold()
            for value in self.excluded_extensions
            if value.strip()
        )


class FileScanner:
    def __init__(
        self,
        policy: SafetyPolicy | None = None,
        options: ScanOptions | None = None,
        control: ProcessControl | None = None,
        progress: ProgressCallback | None = None,
    ) -> None:
        self.policy = policy or SafetyPolicy()
        self.options = options or ScanOptions()
        self.control = control
        self.progress = progress

    def _checkpoint(self)->None:
        if self.control is not None:
            self.control.checkpoint()

    def _paused_seconds(self)->float:
        return self.control.paused_seconds if self.control is not None else 0.0

    def iter_files(self, root: Path) -> Iterator[FileRecord]:
        """Liefert reguläre Dateien ausschließlich lesend und ohne Symlink-Folgen."""
        safe_root = self.policy.ensure_scan_root_allowed(root)
        if not safe_root.exists() or not safe_root.is_dir():
            return

        excluded_dirs=set(self.options.excluded_dir_names)
        if self.options.exclude_python_project_dirs:
            excluded_dirs.update(DEFAULT_PYTHON_PROJECT_DIRS)
        excluded_dirs_cf={name.casefold() for name in excluded_dirs}
        excluded_ext=self.options.normalized_extensions()
        discovered=0
        tracker=ProgressTracker(0,"Dateien erfassen",self._paused_seconds)

        for dirpath, dirnames, filenames in os.walk(
            safe_root, followlinks=self.policy.follow_symlinks
        ):
            self._checkpoint()
            current = Path(dirpath)
            kept=[]
            for dirname in dirnames:
                candidate=current/dirname
                if dirname.casefold() in excluded_dirs_cf:
                    continue
                if not self.policy.follow_symlinks and candidate.is_symlink():
                    continue
                kept.append(dirname)
            dirnames[:]=kept

            for filename in filenames:
                self._checkpoint()
                path=current/filename
                try:
                    if path.suffix.casefold() in excluded_ext:
                        continue
                    if path.is_symlink() and not self.policy.follow_symlinks:
                        continue
                    if not path.is_file():
                        continue
                    stat=path.stat()
                    discovered+=1
                    if self.progress and (discovered == 1 or discovered % 25 == 0):
                        self.progress(tracker.update(discovered,f"Dateien erfassen · {discovered} gefunden"))
                    yield FileRecord(path=path,size=stat.st_size,mtime_ns=stat.st_mtime_ns)
                except (OSError,PermissionError):
                    continue

        if self.progress:
            self.progress(tracker.update(discovered,f"Dateiliste fertig · {discovered} Dateien"))

    def iter_text_files(self, root: Path) -> Iterator[FileRecord]:
        for record in self.iter_files(root):
            if record.path.suffix.lower() in TEXT_EXTENSIONS:
                yield record
