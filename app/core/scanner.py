from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from app.models.entities import FileRecord
from app.safety.policy import SafetyPolicy


TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".log", ".json", ".xml", ".yaml", ".yml",
    ".ini", ".conf", ".py", ".sh",
}


class FileScanner:
    def __init__(self, policy: SafetyPolicy | None = None) -> None:
        self.policy = policy or SafetyPolicy()

    def iter_files(self, root: Path) -> Iterator[FileRecord]:
        """Liefert reguläre Dateien ausschließlich lesend und ohne Symlink-Folgen."""
        safe_root = self.policy.ensure_scan_root_allowed(root)
        if not safe_root.exists() or not safe_root.is_dir():
            return

        for dirpath, dirnames, filenames in os.walk(
            safe_root, followlinks=self.policy.follow_symlinks
        ):
            current = Path(dirpath)
            if not self.policy.follow_symlinks:
                dirnames[:] = [d for d in dirnames if not (current / d).is_symlink()]

            for filename in filenames:
                path = current / filename
                try:
                    if path.is_symlink() and not self.policy.follow_symlinks:
                        continue
                    if not path.is_file():
                        continue
                    stat = path.stat()
                    yield FileRecord(path=path, size=stat.st_size, mtime_ns=stat.st_mtime_ns)
                except (OSError, PermissionError):
                    continue

    def iter_text_files(self, root: Path) -> Iterator[FileRecord]:
        for record in self.iter_files(root):
            if record.path.suffix.lower() in TEXT_EXTENSIONS:
                yield record
