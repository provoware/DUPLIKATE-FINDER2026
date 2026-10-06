from pathlib import Path

from app.core.scanner import FileScanner
from app.models.entities import ScanIssue


def test_text_scanner_only_returns_supported_text_files(tmp_path: Path):
    (tmp_path / "a.txt").write_text("Hallo", encoding="utf-8")
    (tmp_path / "b.bin").write_bytes(b"abc")
    records = list(FileScanner().iter_text_files(tmp_path))
    assert [record.path.name for record in records] == ["a.txt"]


def test_general_scanner_returns_regular_files(tmp_path: Path):
    (tmp_path / "a.txt").write_text("Hallo", encoding="utf-8")
    (tmp_path / "b.bin").write_bytes(b"abc")
    names = sorted(record.path.name for record in FileScanner().iter_files(tmp_path))
    assert names == ["a.txt", "b.bin"]


def test_scanner_does_not_follow_symlink_by_default(tmp_path: Path):
    real = tmp_path / "real"
    real.mkdir()
    (real / "inside.txt").write_text("x", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    records = list(FileScanner().iter_text_files(tmp_path))
    assert [r.path.name for r in records].count("inside.txt") == 1


def test_temporary_error_handler_chains_and_restores_previous_handler(tmp_path: Path):
    previous: list[ScanIssue] = []
    temporary: list[ScanIssue] = []
    scanner = FileScanner(on_error=previous.append)
    original_handler = scanner.on_error

    with scanner.temporary_error_handler(temporary.append):
        scanner.report_error(tmp_path / "a.txt", "Test", OSError("kaputt"))

    assert scanner.on_error is original_handler
    assert len(previous) == 1
    assert len(temporary) == 1
    assert previous[0] == temporary[0]


def test_public_scanner_control_helpers_work_without_process_control():
    scanner = FileScanner()

    scanner.checkpoint()

    assert scanner.paused_seconds() == 0.0
