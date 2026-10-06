from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class JobStatus(str, Enum):
    PENDING = "wartend"
    RUNNING = "laeuft"
    PAUSED = "pausiert"
    DONE = "fertig"
    CANCELLED = "abgebrochen"
    FAILED = "fehler"


@dataclass(frozen=True)
class FileRecord:
    path: Path
    size: int
    mtime_ns: int
    sha256: Optional[str] = None


@dataclass(frozen=True)
class SearchHit:
    path: Path
    line_number: Optional[int]
    excerpt: str
    source: str  # "dateiname" oder "inhalt"


@dataclass
class SearchJob:
    root: Path
    query: str
    search_names: bool = True
    search_contents: bool = True
    status: JobStatus = JobStatus.PENDING
    scanned_files: int = 0
    hits: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DuplicateGroup:
    sha256: str
    size: int
    paths: tuple[Path, ...]


@dataclass(frozen=True)
class Collection:
    id: int
    name: str
    note: str = ""


@dataclass(frozen=True)
class CollectionItem:
    collection_id: int
    path: Path
    note: str = ""


@dataclass(frozen=True)
class VirtualItemState:
    path: Path
    marked: bool = False
    note: str = ""


@dataclass(frozen=True)
class ChangeJournalEntry:
    action: str
    source: Path
    target: Optional[Path]
    status: str
    details: str = ""
