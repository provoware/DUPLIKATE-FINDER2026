from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.core.control import ProcessControl
from app.core.hashing import sha256_file
from app.core.scanner import FileScanner, ScanOptions
from app.models.entities import DuplicateGroup, FileRecord

ProgressCallback = Callable[[int, int, str], None]


def find_duplicate_groups(
    records: list[FileRecord],
    *,
    control: ProcessControl | None = None,
    progress: ProgressCallback | None = None,
    max_workers: int = 1,
) -> list[DuplicateGroup]:
    """Erkennt Duplikate erst nach vollständiger SHA-256-Prüfung."""
    by_size: dict[int, list[FileRecord]] = defaultdict(list)
    for record in records:
        by_size[record.size].append(record)

    candidates = [
        record
        for same_size in by_size.values()
        if len(same_size) > 1
        for record in same_size
    ]
    total = len(candidates)
    if progress is not None:
        progress(0, total, "Inhalte werden vollständig verglichen")

    by_hash: dict[tuple[int, str], list[Path]] = defaultdict(list)

    def hash_record(record: FileRecord) -> tuple[int, str, Path]:
        if control is not None:
            control.checkpoint()
        return record.size, sha256_file(record.path, control=control), record.path

    workers = max(1, int(max_workers))
    if workers == 1:
        for index, record in enumerate(candidates, start=1):
            try:
                size, digest, path = hash_record(record)
            except (OSError, PermissionError):
                continue
            by_hash[(size, digest)].append(path)
            if progress is not None:
                progress(index, total, "Inhalte werden vollständig verglichen")
    else:
        completed = 0
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="provoware-hash") as pool:
            futures = [pool.submit(hash_record, record) for record in candidates]
            for future in as_completed(futures):
                if control is not None:
                    control.checkpoint()
                try:
                    size, digest, path = future.result()
                except (OSError, PermissionError):
                    completed += 1
                    continue
                by_hash[(size, digest)].append(path)
                completed += 1
                if progress is not None:
                    progress(completed, total, "Inhalte werden vollständig verglichen")

    groups = [
        DuplicateGroup(digest, size, tuple(sorted(paths)))
        for (size, digest), paths in by_hash.items()
        if len(paths) > 1
    ]
    return sorted(groups, key=lambda group: (-group.size * len(group.paths), group.sha256))


def scan_duplicate_groups(
    root: Path,
    scanner: FileScanner | None = None,
    *,
    options: ScanOptions | None = None,
    control: ProcessControl | None = None,
    progress: ProgressCallback | None = None,
    max_workers: int = 1,
) -> tuple[int, list[DuplicateGroup]]:
    active_scanner = scanner or FileScanner()

    def discovered(count: int, _path: Path) -> None:
        if progress is not None and (count == 1 or count % 25 == 0):
            progress(count, 0, "Dateiliste wird aufgebaut")

    records = list(
        active_scanner.iter_files(
            root,
            options=options,
            control=control,
            on_discovered=discovered,
        )
    )
    return len(records), find_duplicate_groups(
        records,
        control=control,
        progress=progress,
        max_workers=max_workers,
    )
