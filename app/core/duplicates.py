from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from app.core.hashing import (
    FileChangedError,
    ensure_record_unchanged,
    quick_fingerprint,
    stable_sha256,
)
from app.core.scanner import FileScanner
from app.models.entities import DuplicateGroup, FileRecord, ScanIssue
from app.process_control import ProgressInfo, ProgressTracker
from app.storage.database import Database


ProgressCallback = Callable[[ProgressInfo], None]
MIN_INVENTORY_BATCH_SIZE = 50


def _progress_tracker(
    total: int,
    label: str,
    scanner: FileScanner | None,
    *,
    total_bytes: int = 0,
) -> ProgressTracker:
    pause_provider = scanner.paused_seconds if scanner is not None else None
    return ProgressTracker(
        total,
        label,
        pause_provider,
        total_bytes=total_bytes,
    )


def find_duplicate_groups(
    records: list[FileRecord],
    *,
    scanner: FileScanner | None = None,
    progress: ProgressCallback | None = None,
) -> list[DuplicateGroup]:
    """Kompatibler In-Memory-Weg; finale Entscheidung immer über vollständiges SHA-256."""
    by_size: dict[int, list[FileRecord]] = defaultdict(list)
    for record in records:
        by_size[record.size].append(record)

    candidates = [
        record
        for same_size in by_size.values()
        if len(same_size) > 1
        for record in same_size
    ]
    tracker = _progress_tracker(
        len(candidates),
        "Duplikatkandidaten prüfen",
        scanner,
        total_bytes=sum(record.size for record in candidates),
    )
    checked = 0
    processed_bytes = 0
    groups: list[DuplicateGroup] = []

    for size, same_size in by_size.items():
        if len(same_size) < 2:
            continue

        by_quick: dict[str, list[FileRecord]] = defaultdict(list)
        for record in same_size:
            if scanner is not None:
                scanner.checkpoint()
            try:
                by_quick[
                    quick_fingerprint(
                        record,
                        control=scanner.control if scanner else None,
                    )
                ].append(record)
            except (OSError, FileChangedError) as exc:
                if scanner is not None:
                    scanner.report_error(record.path, "Schnellprüfung", exc)

        for quick_records in by_quick.values():
            if len(quick_records) < 2:
                continue

            by_hash: dict[str, list[Path]] = defaultdict(list)
            for record in quick_records:
                if scanner is not None:
                    scanner.checkpoint()
                try:
                    digest = stable_sha256(
                        record,
                        control=scanner.control if scanner else None,
                    )
                    by_hash[digest].append(record.path)
                except (OSError, FileChangedError) as exc:
                    if scanner is not None:
                        scanner.report_error(record.path, "SHA-256-Prüfung", exc)

                checked += 1
                processed_bytes += record.size
                if progress:
                    progress(
                        tracker.update(
                            checked,
                            f"Prüfsumme {checked} von {len(candidates)}",
                            processed_bytes=processed_bytes,
                        )
                    )

            for digest, paths in by_hash.items():
                if len(paths) > 1:
                    groups.append(
                        DuplicateGroup(digest, size, tuple(sorted(paths)))
                    )

    if progress and not candidates:
        progress(tracker.update(0, "Keine gleich großen Kandidaten – fertig"))

    return sorted(
        groups,
        key=lambda group: (-group.size * len(group.paths), group.sha256),
    )


def scan_duplicate_groups(
    root: Path,
    scanner: FileScanner | None = None,
    progress: ProgressCallback | None = None,
) -> tuple[int, list[DuplicateGroup]]:
    """Kompatibler Weg für kleine direkte Aufrufe und bestehende API-Nutzer."""
    active_scanner = scanner or FileScanner()
    records = list(active_scanner.iter_files(root))
    if progress:
        progress(ProgressInfo("Nach Dateigröße vorsortieren", 0, 0, 0.0, None, 0))
    return (
        len(records),
        find_duplicate_groups(records, scanner=active_scanner, progress=progress),
    )


def _collect_inventory(
    root: Path,
    database: Database,
    run_id: int,
    scanner: FileScanner,
    batch_size: int,
) -> int:
    inventory: list[FileRecord] = []
    scanned = 0
    effective_batch_size = max(MIN_INVENTORY_BATCH_SIZE, int(batch_size))

    for record in scanner.iter_files(root):
        inventory.append(record)
        scanned += 1
        if len(inventory) >= effective_batch_size:
            database.append_scan_inventory(run_id, inventory)
            inventory.clear()

    if inventory:
        database.append_scan_inventory(run_id, inventory)

    return scanned


def _quick_hash_candidates(
    database: Database,
    run_id: int,
    scanner: FileScanner,
    progress: ProgressCallback | None,
) -> None:
    candidate_count, candidate_bytes = database.duplicate_candidate_totals(run_id)
    tracker = _progress_tracker(
        candidate_count,
        "Schnellprüfung gleicher Dateigrößen",
        scanner,
        total_bytes=candidate_bytes,
    )
    checked = 0
    processed_bytes = 0

    for record in database.iter_duplicate_size_candidates(run_id):
        scanner.checkpoint()
        try:
            digest = quick_fingerprint(record, control=scanner.control)
            database.set_inventory_quick_hash(run_id, record.path, digest)
        except (OSError, FileChangedError) as exc:
            scanner.report_error(record.path, "Schnellprüfung", exc)

        checked += 1
        processed_bytes += record.size
        if progress:
            progress(
                tracker.update(
                    checked,
                    f"Schnellprüfung {checked} von {candidate_count}",
                    processed_bytes=processed_bytes,
                )
            )


def _full_hash_candidates(
    database: Database,
    run_id: int,
    scanner: FileScanner,
    progress: ProgressCallback | None,
) -> None:
    candidate_count, candidate_bytes = database.full_hash_candidate_totals(run_id)
    tracker = _progress_tracker(
        candidate_count,
        "Vollständige SHA-256-Prüfung",
        scanner,
        total_bytes=candidate_bytes,
    )
    checked = 0
    processed_bytes = 0

    for record in database.iter_full_hash_candidates(run_id):
        scanner.checkpoint()
        try:
            ensure_record_unchanged(record)
            digest = database.cached_sha256(record)
            if digest is None:
                digest = stable_sha256(record, control=scanner.control)
                database.cache_sha256(record, digest)
            else:
                ensure_record_unchanged(record)
            database.set_inventory_sha256(run_id, record.path, digest)
        except (OSError, FileChangedError) as exc:
            scanner.report_error(record.path, "SHA-256-Prüfung", exc)

        checked += 1
        processed_bytes += record.size
        if progress:
            progress(
                tracker.update(
                    checked,
                    f"SHA-256 {checked} von {candidate_count}",
                    processed_bytes=processed_bytes,
                )
            )


def scan_duplicate_groups_to_database(
    root: Path,
    database: Database,
    *,
    scanner: FileScanner | None = None,
    progress: ProgressCallback | None = None,
    batch_size: int = 500,
) -> tuple[int, int, int]:
    """Skalierbarer Produktionsweg: Inventar, Vorfilter und Hashes bleiben in SQLite."""
    active_scanner = scanner or FileScanner()
    run_id = database.create_scan_run("duplicates", root)
    scanned = 0

    def record_issue(issue: ScanIssue) -> None:
        database.record_scan_issue(run_id, issue)

    try:
        with active_scanner.temporary_error_handler(record_issue):
            scanned = _collect_inventory(
                root,
                database,
                run_id,
                active_scanner,
                batch_size,
            )
            _quick_hash_candidates(
                database,
                run_id,
                active_scanner,
                progress,
            )
            _full_hash_candidates(
                database,
                run_id,
                active_scanner,
                progress,
            )

        group_count = database.persist_duplicates_from_run(run_id)
        error_count = database.scan_error_count(run_id)
        database.finish_scan_run(run_id, "fertig", scanned)
        database.prune_scan_runs()
        return scanned, group_count, error_count
    except Exception:
        database.finish_scan_run(run_id, "fehler", scanned)
        raise
