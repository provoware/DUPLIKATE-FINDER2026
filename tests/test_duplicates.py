from pathlib import Path

from app.core.duplicates import find_duplicate_groups, scan_duplicate_groups
from app.models.entities import FileRecord


def _record(path: Path) -> FileRecord:
    stat = path.stat()
    return FileRecord(path, stat.st_size, stat.st_mtime_ns)


def test_duplicate_groups_require_equal_content(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    c = tmp_path / "c.txt"
    a.write_text("gleich", encoding="utf-8")
    b.write_text("gleich", encoding="utf-8")
    c.write_text("anders", encoding="utf-8")
    groups = find_duplicate_groups([_record(a), _record(b), _record(c)])
    assert len(groups) == 1
    assert set(groups[0].paths) == {a, b}


def test_duplicate_scan_includes_non_text_regular_files(tmp_path: Path):
    payload = b"\x00\x01gleich\xff"
    (tmp_path / "a.bin").write_bytes(payload)
    (tmp_path / "b.bin").write_bytes(payload)
    scanned, groups = scan_duplicate_groups(tmp_path)
    assert scanned == 2
    assert len(groups) == 1
    assert {p.name for p in groups[0].paths} == {"a.bin", "b.bin"}
