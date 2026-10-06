from __future__ import annotations

import json
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.file_browser.classification import classify_path
from app.formatting import format_bytes


MAX_TEXT_PREVIEW_BYTES = 512 * 1024


@dataclass(frozen=True)
class TextPreview:
    text: str
    encoding: str
    line_count: int
    word_count: int
    character_count: int
    truncated: bool


@dataclass(frozen=True)
class PreviewData:
    kind: str
    title: str
    details: str
    text: str = ""
    image: Any | None = None
    page_index: int = 0
    page_count: int = 0


def _file_details(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError as exc:
        return f"Pfad: {path}\nMetadaten nicht lesbar: {exc}"
    changed = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M:%S")
    return (
        f"Pfad: {path}\n"
        f"Typ: {classify_path(path).label} · Größe: {format_bytes(stat.st_size)}\n"
        f"Geändert: {changed}"
    )


def _decode_text(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8 (mit Ersatzzeichen)"


def text_preview_info(path: Path, limit: int = MAX_TEXT_PREVIEW_BYTES) -> TextPreview:
    size = path.stat().st_size
    raw = path.read_bytes()[:limit]
    text, encoding = _decode_text(raw)
    truncated = size > limit

    # JSON wird für Laien lesbarer eingerückt, wenn die Vorschau vollständig ist.
    if path.suffix.casefold() == ".json" and not truncated:
        try:
            parsed = json.loads(text)
            text = json.dumps(parsed, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, TypeError):
            pass

    lines = text.splitlines()
    words = text.split()
    return TextPreview(
        text=text,
        encoding=encoding,
        line_count=max(1, len(lines)),
        word_count=len(words),
        character_count=len(text),
        truncated=truncated,
    )


def read_text_preview(path: Path, limit: int = MAX_TEXT_PREVIEW_BYTES) -> str:
    info = text_preview_info(path, limit)
    text = info.text
    if info.truncated:
        text += "\n\n[… Vorschau aus Sicherheits- und Leistungsgründen gekürzt …]"
    return text


def image_metadata(path: Path) -> tuple[Any | None, list[str]]:
    from PySide6.QtGui import QImageReader

    reader = QImageReader(str(path))
    if not reader.canRead():
        return None, ["Bildformat konnte nicht gelesen werden."]

    image_format = bytes(reader.format()).decode("ascii", errors="replace").upper() or path.suffix.lstrip(".").upper()
    original = reader.size()
    details = [f"Format: {image_format}"]

    if original.isValid():
        pixels = original.width() * original.height()
        details.append(f"Abmessungen: {original.width()} × {original.height()} Pixel")
        details.append(f"Auflösung: {pixels / 1_000_000:.2f} Megapixel")
        if original.height():
            details.append(f"Seitenverhältnis: {original.width() / original.height():.2f}:1")

    return reader, details


def read_image_preview(path: Path, target_width: int = 1000, target_height: int = 800):
    from PySide6.QtCore import QSize, Qt

    reader, _details = image_metadata(path)
    if reader is None:
        return None
    original = reader.size()
    if original.isValid():
        scaled = QSize(original)
        scaled.scale(QSize(target_width, target_height), Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(scaled)
    image = reader.read()
    return None if image.isNull() else image


def read_pdf_preview(
    path: Path,
    page_index: int = 0,
    target_width: int = 1000,
    target_height: int = 1200,
):
    from PySide6.QtCore import QSize, Qt

    try:
        from PySide6.QtPdf import QPdfDocument
    except ImportError:
        return None, "PDF-Vorschau ist in dieser Qt-Laufzeit nicht verfügbar.", 0, 0

    document = QPdfDocument()
    error = document.load(str(path))
    if error != QPdfDocument.Error.None_:
        return None, f"PDF konnte nicht gelesen werden: {error}", 0, 0

    page_count = document.pageCount()
    if page_count < 1:
        return None, "PDF enthält keine darstellbare Seite.", 0, 0

    page_index = max(0, min(int(page_index), page_count - 1))
    render_size = document.pagePointSize(page_index).toSize()
    render_size.scale(QSize(target_width, target_height), Qt.AspectRatioMode.KeepAspectRatio)
    image = document.render(page_index, render_size)
    note = f"PDF-Seite: {page_index + 1} von {page_count}"
    return (None if image.isNull() else image), note, page_index, page_count


def media_metadata(path: Path) -> list[str]:
    suffix = path.suffix.casefold()
    kind = classify_path(path, is_dir=False)
    lines = [f"Medientyp: {kind.label}", f"Dateiendung: {suffix or 'keine'}"]

    if suffix == ".wav":
        try:
            with wave.open(str(path), "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                duration = frames / rate if rate else 0.0
                lines.extend(
                    [
                        f"Dauer: {duration:.2f} Sekunden",
                        f"Kanäle: {wav.getnchannels()}",
                        f"Abtastrate: {rate} Hz",
                        f"Auflösung: {wav.getsampwidth() * 8} Bit",
                    ]
                )
        except (wave.Error, OSError):
            lines.append("WAV-Technikdaten konnten nicht gelesen werden.")
    else:
        lines.append(
            "Dauer, Codec und Bitrate werden ohne zusätzliche Medienbibliothek nicht zuverlässig ausgelesen."
        )
    return lines


def build_preview(path: Path, *, pdf_page: int = 0) -> PreviewData:
    kind = classify_path(path)
    details = _file_details(path)

    if kind.key == "directory":
        return PreviewData(kind.key, path.name or str(path), details, "Ordner")

    if kind.key == "text":
        try:
            info = text_preview_info(path)
            text = info.text
            if info.truncated:
                text += "\n\n[… Vorschau aus Sicherheits- und Leistungsgründen gekürzt …]"
            details += (
                f"\nZeichenkodierung: {info.encoding}"
                f"\nZeilen: {info.line_count} · Wörter: {info.word_count} · Zeichen: {info.character_count}"
            )
            if info.truncated:
                details += f"\nVorschaugrenze: {format_bytes(MAX_TEXT_PREVIEW_BYTES)}"
        except OSError as exc:
            text = f"Text konnte nicht gelesen werden: {exc}"
        return PreviewData(kind.key, path.name, details, text=text)

    if kind.key == "image":
        reader, meta = image_metadata(path)
        if reader is None:
            return PreviewData(kind.key, path.name, details, "Bild konnte nicht dargestellt werden.")
        image = read_image_preview(path)
        if image is None:
            return PreviewData(kind.key, path.name, details + "\n" + "\n".join(meta), "Bild konnte nicht dargestellt werden.")
        details += "\n" + "\n".join(meta)
        details += f"\nGeladene Vorschau: {image.width()} × {image.height()} Pixel"
        return PreviewData(kind.key, path.name, details, image=image)

    if kind.key == "pdf":
        image, note, page_index, page_count = read_pdf_preview(path, pdf_page)
        return PreviewData(
            kind.key,
            path.name,
            details + "\n" + note,
            image=image,
            page_index=page_index,
            page_count=page_count,
        )

    if kind.key in {"video", "audio"}:
        details += "\n" + "\n".join(media_metadata(path))
        return PreviewData(
            kind.key,
            path.name,
            details,
            "Interne Wiedergabe ist bewusst deaktiviert. Mit „Öffnen“ wird das Standardprogramm verwendet.",
        )

    return PreviewData(
        kind.key,
        path.name,
        details,
        "Für diesen Dateityp gibt es noch keine interne Vorschau.",
    )
