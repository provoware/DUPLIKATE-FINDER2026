from __future__ import annotations

from pathlib import Path

import pytest

from app.core.control import ProcessCancelled, ProcessControl
from app.core.duplicates import scan_duplicate_groups
from app.core.scanner import FileScanner, ScanOptions
from app.core.search import TextSearcher
from app.models.entities import SearchJob


def test_scanner_skips_python_project_dirs_by_default(tmp_path: Path):
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "paket.txt").write_text("unsichtbar", encoding="utf-8")
    (tmp_path / "normal.txt").write_text("sichtbar", encoding="utf-8")
    names={record.path.name for record in FileScanner().iter_files(tmp_path)}
    assert names == {"normal.txt"}


def test_scanner_can_exclude_file_extensions(tmp_path: Path):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.log").write_text("b", encoding="utf-8")
    options=ScanOptions(excluded_extensions=frozenset({".log"}))
    names={record.path.name for record in FileScanner().iter_files(tmp_path, options=options)}
    assert names == {"a.txt"}


def test_cancelled_search_stops_cooperatively(tmp_path: Path):
    (tmp_path / "a.txt").write_text("Nadel", encoding="utf-8")
    control=ProcessControl()
    control.cancel()
    with pytest.raises(ProcessCancelled):
        TextSearcher().search(SearchJob(tmp_path, "Nadel"), control=control)


def test_duplicate_scan_respects_extension_filter_and_progress(tmp_path: Path):
    payload=b"gleich"
    (tmp_path / "a.bin").write_bytes(payload)
    (tmp_path / "b.bin").write_bytes(payload)
    (tmp_path / "a.tmp").write_bytes(payload)
    (tmp_path / "b.tmp").write_bytes(payload)
    events=[]
    scanned,groups=scan_duplicate_groups(
        tmp_path,
        options=ScanOptions(excluded_extensions=frozenset({".tmp"})),
        progress=lambda current,total,phase: events.append((current,total,phase)),
        max_workers=2,
    )
    assert scanned == 2
    assert len(groups) == 1
    assert {path.suffix for path in groups[0].paths} == {".bin"}
    assert events
