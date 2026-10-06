from __future__ import annotations

from pathlib import Path

from app.file_browser.classification import classify_path, known_extensions
from app.file_browser.preview import MAX_TEXT_PREVIEW_BYTES, build_preview, read_image_preview, read_text_preview


def test_file_kinds_cover_planned_groups(tmp_path: Path):
    assert classify_path(tmp_path / "notiz.md", is_dir=False).key == "text"
    assert classify_path(tmp_path / "bild.webp", is_dir=False).key == "image"
    assert classify_path(tmp_path / "bericht.pdf", is_dir=False).key == "pdf"
    assert classify_path(tmp_path / "film.mkv", is_dir=False).key == "video"
    assert classify_path(tmp_path / "musik.flac", is_dir=False).key == "audio"
    assert classify_path(tmp_path / "archiv.xyz", is_dir=False).key == "other"
    assert ".toml" in known_extensions()
    assert ".tiff" in known_extensions()


def test_text_preview_is_limited_and_readable(tmp_path: Path):
    path = tmp_path / "gross.txt"
    path.write_text("äöü " + ("Test " * 150000), encoding="utf-8")
    text = read_text_preview(path)
    assert "äöü" in text
    assert "Vorschau" in text
    assert len(text.encode("utf-8")) < MAX_TEXT_PREVIEW_BYTES + 2048


def test_windows_encoded_text_is_readable(tmp_path: Path):
    path = tmp_path / "legacy.txt"
    path.write_bytes("Größe – Prüfung".encode("cp1252"))
    assert "Größe" in read_text_preview(path)


def test_image_preview_is_scaled(tmp_path: Path):
    import pytest
    try:
        from PySide6.QtGui import QImage
    except ImportError:
        pytest.skip("Qt-Grafiklaufzeit ist in diesem reinen Kern-Testjob nicht installiert.")

    path = tmp_path / "bild.png"
    image = QImage(2000, 1200, QImage.Format.Format_RGB32)
    image.fill(0xFF224466)
    assert image.save(str(path))
    preview = read_image_preview(path, 500, 500)
    assert preview is not None
    assert preview.width() <= 500
    assert preview.height() <= 500


def test_audio_video_preview_does_not_require_player(tmp_path: Path):
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"placeholder")
    data = build_preview(path)
    assert data.kind == "video"
    assert data.image is None
    assert "Extern öffnen" in data.text
