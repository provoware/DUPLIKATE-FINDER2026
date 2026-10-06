from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from app.core.hashing import sha256_file
from app.core.scanner import FileScanner
from app.models.entities import DuplicateGroup, FileRecord


def find_duplicate_groups(records: list[FileRecord]) -> list[DuplicateGroup]:
    """Erkennt Duplikate erst nach vollständiger SHA-256-Prüfung."""
    by_size: dict[int, list[FileRecord]] = defaultdict(list)
    for record in records:
        by_size[record.size].append(record)

    groups: list[DuplicateGroup] = []
    for size, same_size in by_size.items():
        if len(same_size) < 2:
            continue

        by_hash: dict[str, list[Path]] = defaultdict(list)
        for record in same_size:
            try:
                by_hash[sha256_file(record.path)].append(record.path)
            except (OSError, PermissionError):
                continue

        for digest, paths in by_hash.items():
            if len(paths) > 1:
                groups.append(DuplicateGroup(digest, size, tuple(sorted(paths))))

    return sorted(groups, key=lambda group: (-group.size * len(group.paths), group.sha256))


def scan_duplicate_groups(root: Path, scanner: FileScanner | None = None) -> tuple[int, list[DuplicateGroup]]:
    active_scanner = scanner or FileScanner()
    records = list(active_scanner.iter_files(root))
    return len(records), find_duplicate_groups(records)
