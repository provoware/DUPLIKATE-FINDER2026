from __future__ import annotations

from pathlib import Path

from app.file_browser.classification import classify_path, known_extensions
from app.file_browser.preview import (
    MAX_TEXT_PREVIEW_BYTES,
    build_preview,
    media_metadata,
    read_image_preview,
    read_text_preview,
    text_preview_info,
)


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
    assert "Standardprogramm" in data.text
    assert "Öffnen" in data.text


def test_text_preview_reports_encoding_and_counts(tmp_path: Path):
    path = tmp_path / "notiz.txt"
    path.write_text("eins zwei\ndrei vier\n", encoding="utf-8")
    info = text_preview_info(path)
    assert info.encoding == "utf-8-sig"
    assert info.line_count == 2
    assert info.word_count == 4
    assert info.character_count >= 18
    assert info.truncated is False


def test_json_preview_is_pretty_printed(tmp_path: Path):
    path = tmp_path / "daten.json"
    path.write_text('{"name":"PROVOWARE","wert":8}', encoding="utf-8")
    data = build_preview(path)
    assert '"name": "PROVOWARE"' in data.text
    assert "Zeichenkodierung:" in data.details
    assert "Wörter:" in data.details


def test_wav_metadata_uses_python_standard_library(tmp_path: Path):
    import wave

    path = tmp_path / "ton.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        wav.writeframes(b"\x00\x00\x00\x00" * 44100)

    details = "\n".join(media_metadata(path))
    assert "Dauer: 1.00 Sekunden" in details
    assert "Kanäle: 2" in details
    assert "Abtastrate: 44100 Hz" in details
    assert "Auflösung: 16 Bit" in details


def test_non_wav_media_explains_metadata_limit(tmp_path: Path):
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"placeholder")
    details = "\n".join(media_metadata(path))
    assert "ohne zusätzliche Medienbibliothek" in details


def test_text_reader_never_loads_entire_large_file(tmp_path, monkeypatch):
    import io
    path = tmp_path / 'large.txt'
    path.write_bytes(b'x' * 2000)
    class BoundedReader(io.BytesIO):
        def read(self, size=-1):
            assert 0 < size <= 128
            return super().read(size)
    monkeypatch.setattr(Path, 'open', lambda *a, **k: BoundedReader(b'x' * 2000))
    info = text_preview_info(path, limit=128)
    assert info.truncated and len(info.text) == 128


def test_even_length_windows_text_is_not_misread_as_utf16(tmp_path):
    path = tmp_path / 'windows.txt'
    path.write_bytes(b'Gr\xf6\xdfe!')
    assert read_text_preview(path) == 'Größe!'


def test_broken_wav_does_not_crash_preview(tmp_path):
    path = tmp_path / 'broken.wav'
    path.write_bytes(b'RIFF')
    assert 'konnten nicht' in '\n'.join(media_metadata(path))


def test_deeply_nested_json_falls_back_to_text(tmp_path):
    path = tmp_path / 'deep.json'
    raw = '[' * 2000 + '0' + ']' * 2000
    path.write_text(raw)
    assert read_text_preview(path) == raw


def test_document_preview_formats_and_safety(tmp_path):
    import zipfile
    from app.file_browser.preview import read_document_preview, MAX_DOCUMENT_XML_BYTES
    for suffix, member, xml in [
        ('.docx', 'word/document.xml', '<doc><p><t>Hallo Welt</t></p></doc>'),
        ('.odt', 'content.xml', '<doc><h>Titel</h><p>Hallo Welt</p></doc>'),
    ]:
        path = tmp_path / ('test' + suffix)
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(member, xml)
        assert classify_path(path).key == 'document'
        assert 'Hallo Welt' in build_preview(path).text
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(member, '<!DOCTYPE doc [<!ENTITY x "unsafe">]><doc><p>&x;</p></doc>')
        assert 'abgebrochen' in read_document_preview(path)
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(member, 'x' * (MAX_DOCUMENT_XML_BYTES + 1))
        assert 'ungewöhnlich groß' in read_document_preview(path)
        path.write_bytes(b'broken archive')
        assert 'nicht gelesen' in read_document_preview(path)
