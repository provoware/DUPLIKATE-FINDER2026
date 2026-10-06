from __future__ import annotations

import hashlib
from pathlib import Path

from app.models.entities import FileRecord
from app.process_control import ProcessControl


class FileChangedError(RuntimeError):
    pass


def _identity(path: Path) -> tuple[int, int, int, int]:
    stat = path.stat()
    return (
        int(stat.st_size),
        int(stat.st_mtime_ns),
        int(getattr(stat, "st_dev", 0)),
        int(getattr(stat, "st_ino", 0)),
    )


def record_identity(record: FileRecord) -> tuple[int, int, int, int]:
    return (record.size, record.mtime_ns, record.device, record.inode)


def ensure_record_unchanged(record: FileRecord) -> None:
    current = _identity(record.path)
    expected = record_identity(record)
    stable = current[0] == expected[0] and current[1] == expected[1]
    if record.device:
        stable = stable and current[2] == expected[2]
    if record.inode:
        stable = stable and current[3] == expected[3]
    if not stable:
        raise FileChangedError(
            f"Datei wurde während der Prüfung verändert: {record.path}"
        )


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def stable_sha256(
    record: FileRecord,
    *,
    control: ProcessControl | None = None,
    chunk_size: int = 1024 * 1024,
) -> str:
    ensure_record_unchanged(record)
    digest = hashlib.sha256()
    with record.path.open("rb") as handle:
        while True:
            if control is not None:
                control.checkpoint()
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    ensure_record_unchanged(record)
    return digest.hexdigest()


def quick_fingerprint(
    record: FileRecord,
    *,
    control: ProcessControl | None = None,
    sample_size: int = 64 * 1024,
) -> str:
    """Schneller Vorfilter. Eine Duplikatentscheidung erfolgt nie allein hierüber."""
    ensure_record_unchanged(record)
    digest = hashlib.sha256()
    digest.update(str(record.size).encode("ascii"))
    with record.path.open("rb") as handle:
        if control is not None:
            control.checkpoint()
        first = handle.read(sample_size)
        digest.update(first)
        if record.size > sample_size:
            handle.seek(max(0, record.size - sample_size))
            if control is not None:
                control.checkpoint()
            digest.update(handle.read(sample_size))
    ensure_record_unchanged(record)
    return digest.hexdigest()
