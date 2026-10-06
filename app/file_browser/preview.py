from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
import json
import mimetypes
from pathlib import Path
import shutil
import subprocess
from typing import Any
import wave
import xml.etree.ElementTree as ET
import zipfile

from app.file_browser.classification import classify_path
from app.formatting import format_bytes


MAX_TEXT_PREVIEW_BYTES = 512 * 1024
MAX_DOCUMENT_PREVIEW_CHARS = 100_000
MAX_DOCUMENT_XML_BYTES = 4 * 1024 * 1024
MEDIA_PROBE_TIMEOUT_SECONDS = 1.5


@dataclass(frozen=True)
class PreviewData:
    kind: str
    title: str
    details: str
    text: str = ""
    image: Any | None = None


def _file_details(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError as exc:
        return f"Pfad: {path}\nMetadaten nicht lesbar: {exc}"
    changed = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M:%S")
    mime, _encoding = mimetypes.guess_type(path.name)
    mime_note = f" · Format: {mime}" if mime else ""
    return (
        f"Pfad: {path}\n"
        f"Typ: {classify_path(path).label} · Größe: {format_bytes(stat.st_size)}{mime_note}\n"
        f"Geändert: {changed}"
    )


def read_text_preview(path: Path, limit: int = MAX_TEXT_PREVIEW_BYTES) -> str:
    raw = path.read_bytes()[:limit]
    for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    if path.stat().st_size > limit:
        text += "\n\n[… Vorschau aus Sicherheits- und Leistungsgründen gekürzt …]"
    return text


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _clip_document_text(text: str) -> str:
    compact = "\n".join(line.rstrip() for line in text.splitlines())
    compact = compact.strip()
    if len(compact) > MAX_DOCUMENT_PREVIEW_CHARS:
        return compact[:MAX_DOCUMENT_PREVIEW_CHARS] + "\n\n[… Dokumentvorschau gekürzt …]"
    return compact


def read_document_preview(path: Path) -> str:
    suffix = path.suffix.casefold()
    try:
        with zipfile.ZipFile(path) as archive:
            if suffix == ".docx":
                info = archive.getinfo("word/document.xml")
                if info.file_size > MAX_DOCUMENT_XML_BYTES:
                    return "Dokumentvorschau abgebrochen: Der interne Dokumenttext ist ungewöhnlich groß."
                xml_bytes = archive.read(info)
                root = ET.fromstring(xml_bytes)
                paragraphs: list[str] = []
                for element in root.iter():
                    if _local_name(element.tag) != "p":
                        continue
                    text = "".join(
                        node.text or ""
                        for node in element.iter()
                        if _local_name(node.tag) == "t"
                    ).strip()
                    if text:
                        paragraphs.append(text)
                return _clip_document_text("\n".join(paragraphs))

            if suffix == ".odt":
                info = archive.getinfo("content.xml")
                if info.file_size > MAX_DOCUMENT_XML_BYTES:
                    return "Dokumentvorschau abgebrochen: Der interne Dokumenttext ist ungewöhnlich groß."
                xml_bytes = archive.read(info)
                root = ET.fromstring(xml_bytes)
                paragraphs = []
                for element in root.iter():
                    if _local_name(element.tag) not in {"p", "h"}:
                        continue
                    text = "".join(element.itertext()).strip()
                    if text:
                        paragraphs.append(text)
                return _clip_document_text("\n".join(paragraphs))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        return f"Dokument konnte nicht gelesen werden: {exc}"

    return "Für dieses Dokumentformat gibt es noch keine interne Textvorschau."


def read_image_preview(path: Path, target_width: int = 1000, target_height: int = 800):
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QImageReader

    reader = QImageReader(str(path))
    if not reader.canRead():
        return None
    original = reader.size()
    if original.isValid():
        scaled = QSize(original)
        scaled.scale(QSize(target_width, target_height), Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(scaled)
    image = reader.read()
    return None if image.isNull() else image


def image_metadata(path: Path) -> str:
    from PySide6.QtGui import QImageReader

    reader = QImageReader(str(path))
    if not reader.canRead():
        return "Bildinformationen konnten nicht gelesen werden."

    size = reader.size()
    format_name = bytes(reader.format()).decode("ascii", errors="replace").upper() or path.suffix.lstrip(".").upper()
    parts = [f"Bildformat: {format_name}"]
    if size.isValid():
        parts.append(f"Original: {size.width()} × {size.height()} Pixel")
        if size.height() > 0:
            parts.append(f"Seitenverhältnis: {size.width() / size.height():.2f}:1")
    return "\n".join(parts)


def read_pdf_preview(
    path: Path,
    target_width: int = 1000,
    target_height: int = 1200,
    page_index: int = 0,
):
    from PySide6.QtCore import QSize, Qt

    try:
        from PySide6.QtPdf import QPdfDocument
    except ImportError:
        return None, "PDF-Vorschau ist in dieser Qt-Laufzeit nicht verfügbar.", 0

    document = QPdfDocument()
    error = document.load(str(path))
    if error != QPdfDocument.Error.None_:
        return None, f"PDF konnte nicht gelesen werden: {error}", 0
    pages = document.pageCount()
    if pages < 1:
        return None, "PDF enthält keine darstellbare Seite.", 0
    safe_page = min(max(0, page_index), pages - 1)
    render_size = document.pagePointSize(safe_page).toSize()
    render_size.scale(QSize(target_width, target_height), Qt.AspectRatioMode.KeepAspectRatio)
    image = document.render(safe_page, render_size)
    return (
        None if image.isNull() else image,
        f"PDF-Seiten: {pages} · angezeigt: {safe_page + 1}",
        pages,
    )


def _duration_text(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _fraction_text(value: str | None) -> str | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        number = float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None
    if number <= 0:
        return None
    return f"{number:.2f} fps"


def _wav_metadata(path: Path) -> list[str]:
    if path.suffix.casefold() != ".wav":
        return []
    try:
        with wave.open(str(path), "rb") as audio:
            rate = audio.getframerate()
            frames = audio.getnframes()
            duration = frames / rate if rate else 0.0
            return [
                f"Dauer: {_duration_text(duration)}",
                f"Kanäle: {audio.getnchannels()}",
                f"Abtastrate: {rate} Hz",
                f"Auflösung: {audio.getsampwidth() * 8} Bit",
            ]
    except (OSError, wave.Error):
        return []


def media_metadata(path: Path) -> str:
    lines = _wav_metadata(path)
    ffprobe = shutil.which("ffprobe")

    if ffprobe:
        command = [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=format_name,duration,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=MEDIA_PROBE_TIMEOUT_SECONDS,
            )
            if completed.returncode == 0 and completed.stdout.strip():
                payload = json.loads(completed.stdout)
                fmt = payload.get("format", {})
                if fmt.get("format_name"):
                    lines.append(f"Container: {fmt['format_name']}")
                try:
                    duration = float(fmt.get("duration", 0))
                    if duration > 0:
                        lines.append(f"Dauer: {_duration_text(duration)}")
                except (TypeError, ValueError):
                    pass
                try:
                    bitrate = int(fmt.get("bit_rate", 0))
                    if bitrate > 0:
                        lines.append(f"Bitrate: {bitrate // 1000} kbit/s")
                except (TypeError, ValueError):
                    pass

                for stream in payload.get("streams", []):
                    codec_type = stream.get("codec_type")
                    codec = stream.get("codec_name")
                    if codec_type == "video":
                        width = stream.get("width")
                        height = stream.get("height")
                        detail = f"Video: {codec or 'unbekannt'}"
                        if width and height:
                            detail += f" · {width} × {height}"
                        fps = _fraction_text(stream.get("r_frame_rate"))
                        if fps:
                            detail += f" · {fps}"
                        lines.append(detail)
                    elif codec_type == "audio":
                        detail = f"Audio: {codec or 'unbekannt'}"
                        if stream.get("channels"):
                            detail += f" · {stream['channels']} Kanäle"
                        if stream.get("sample_rate"):
                            detail += f" · {stream['sample_rate']} Hz"
                        lines.append(detail)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            pass

    unique: list[str] = []
    for line in lines:
        if line not in unique:
            unique.append(line)

    if unique:
        return "\n".join(unique)
    return "Erweiterte Audio-/Videodaten sind auf diesem System nicht verfügbar."


def build_preview(path: Path) -> PreviewData:
    kind = classify_path(path)
    details = _file_details(path)

    if kind.key == "directory":
        return PreviewData(kind.key, path.name or str(path), details, "Ordner")

    if kind.key == "text":
        try:
            text = read_text_preview(path)
        except OSError as exc:
            text = f"Text konnte nicht gelesen werden: {exc}"
        return PreviewData(kind.key, path.name, details, text=text)

    if kind.key == "document":
        return PreviewData(kind.key, path.name, details, text=read_document_preview(path))

    if kind.key == "image":
        image = read_image_preview(path)
        if image is None:
            return PreviewData(kind.key, path.name, details, "Bild konnte nicht dargestellt werden.")
        return PreviewData(
            kind.key,
            path.name,
            details + "\n" + image_metadata(path),
            image=image,
        )

    if kind.key == "pdf":
        image, note, _pages = read_pdf_preview(path)
        return PreviewData(kind.key, path.name, details + "\n" + note, image=image)

    if kind.key in {"video", "audio"}:
        return PreviewData(
            kind.key,
            path.name,
            details + "\n" + media_metadata(path),
            "Interne Wiedergabe ist bewusst deaktiviert. Mit „Öffnen“ wird das Standardprogramm verwendet.",
        )

    return PreviewData(
        kind.key,
        path.name,
        details,
        "Für diesen Dateityp gibt es noch keine interne Vorschau.",
    )
