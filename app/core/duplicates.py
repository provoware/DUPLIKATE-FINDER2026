from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from app.core.hashing import sha256_file
from app.core.scanner import FileScanner
from app.models.entities import DuplicateGroup, FileRecord
from app.process_control import ProgressInfo, ProgressTracker


ProgressCallback=Callable[[ProgressInfo],None]


def find_duplicate_groups(
    records:list[FileRecord],
    *,
    scanner:FileScanner|None=None,
    progress:ProgressCallback|None=None,
)->list[DuplicateGroup]:
    """Erkennt Duplikate erst nach vollständiger SHA-256-Prüfung."""
    by_size:dict[int,list[FileRecord]]=defaultdict(list)
    for record in records:
        by_size[record.size].append(record)

    candidates=[record for same_size in by_size.values() if len(same_size)>1 for record in same_size]
    pause_provider=(lambda:scanner.control.paused_seconds) if scanner and scanner.control else None
    tracker=ProgressTracker(
        len(candidates),
        "Duplikatkandidaten vollständig prüfen",
        pause_provider,
        total_bytes=sum(record.size for record in candidates),
    )
    checked=0
    processed_bytes=0
    groups:list[DuplicateGroup]=[]

    if progress and not candidates:
        progress(tracker.update(0,"Keine gleich großen Kandidaten – fertig"))

    for size,same_size in by_size.items():
        if len(same_size)<2:
            continue
        by_hash:dict[str,list[Path]]=defaultdict(list)
        for record in same_size:
            if scanner is not None:
                scanner._checkpoint()
            try:
                by_hash[sha256_file(record.path)].append(record.path)
                processed_bytes+=record.size
            except (OSError,PermissionError):
                pass
            checked+=1
            if progress:
                progress(tracker.update(
                    checked,
                    f"Prüfsumme {checked} von {len(candidates)}",
                    processed_bytes=processed_bytes,
                ))

        for digest,paths in by_hash.items():
            if len(paths)>1:
                groups.append(DuplicateGroup(digest,size,tuple(sorted(paths))))

    return sorted(groups,key=lambda group:(-group.size*len(group.paths),group.sha256))


def scan_duplicate_groups(
    root:Path,
    scanner:FileScanner|None=None,
    progress:ProgressCallback|None=None,
)->tuple[int,list[DuplicateGroup]]:
    active_scanner=scanner or FileScanner()
    records=list(active_scanner.iter_files(root))
    if progress:
        progress(ProgressInfo("Nach Dateigröße vorsortieren",0,0,0.0,None,0))
    return len(records),find_duplicate_groups(records,scanner=active_scanner,progress=progress)
