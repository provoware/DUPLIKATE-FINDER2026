from __future__ import annotations

from pathlib import Path
import wave
import zipfile

from app.file_browser.classification import classify_path, known_extensions
from app.file_browser.preview import (
    MAX_TEXT_PREVIEW_BYTES,
    build_preview,
    media_metadata,
    read_document_preview,
    read_image_preview,
    read_text_preview,
)


def test_file_kinds_cover_planned_groups(tmp_path: Path):
    assert classify_path(tmp_path / "notiz.md", is_dir=False).key == "text"
    assert classify_path(tmp_path / "bild.webp", is_dir=False).key == "image"
    assert classify_path(tmp_path / "bericht.pdf", is_dir=False).key == "pdf"
    assert classify_path(tmp_path / "datei.docx", is_dir=False).key == "document"
    assert classify_path(tmp_path / "datei.odt", is_dir=False).key == "document"
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



def test_docx_preview_extracts_paragraphs(tmp_path: Path):
    path = tmp_path / "beispiel.docx"
    document_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p><w:r><w:t>Erste Zeile</w:t></w:r></w:p>
        <w:p><w:r><w:t>Zweite Zeile</w:t></w:r></w:p>
      </w:body>
    </w:document>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
    text = read_document_preview(path)
    assert "Erste Zeile" in text
    assert "Zweite Zeile" in text


def test_odt_preview_extracts_paragraphs(tmp_path: Path):
    path = tmp_path / "beispiel.odt"
    content_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <office:document-content
      xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
      xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
      <office:body><office:text>
        <text:h>Überschrift</text:h>
        <text:p>Einfach lesbarer Absatz.</text:p>
      </office:text></office:body>
    </office:document-content>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.xml", content_xml)
    text = read_document_preview(path)
    assert "Überschrift" in text
    assert "Einfach lesbarer Absatz." in text


def test_wav_metadata_without_extra_dependency(tmp_path: Path):
    path = tmp_path / "ton.wav"
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 8000)
    details = media_metadata(path)
    assert "Dauer: 0:01" in details
    assert "Kanäle: 1" in details
    assert "Abtastrate: 8000 Hz" in details
