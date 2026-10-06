from pathlib import Path

from app.core.scanner import FileScanner


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
