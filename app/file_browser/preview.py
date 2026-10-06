from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QImageReader

from app.file_browser.classification import classify_path
from app.formatting import format_bytes


MAX_TEXT_PREVIEW_BYTES = 512 * 1024


@dataclass(frozen=True)
class PreviewData:
    kind: str
    title: str
    details: str
    text: str = ""
    image: QImage | None = None


def _file_details(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError as exc:
        return f"Pfad: {path}\nMetadaten nicht lesbar: {exc}"
    changed = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M:%S")
    return (
        f"Pfad: {path}\n"
        f"Typ: {classify_path(path).label}\n"
        f"Größe: {format_bytes(stat.st_size)}\n"
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


def read_image_preview(path: Path, target: QSize = QSize(1000, 800)) -> QImage | None:
    reader = QImageReader(str(path))
    if not reader.canRead():
        return None
    original = reader.size()
    if original.isValid():
        scaled = QSize(original)
        scaled.scale(target, Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(scaled)
    image = reader.read()
    return None if image.isNull() else image


def read_pdf_preview(path: Path, target: QSize = QSize(1000, 1200)) -> tuple[QImage | None, str]:
    try:
        from PySide6.QtPdf import QPdfDocument
    except ImportError:
        return None, "PDF-Vorschau ist in dieser Qt-Laufzeit nicht verfügbar."

    document = QPdfDocument()
    error = document.load(str(path))
    if error != QPdfDocument.Error.None_:
        return None, f"PDF konnte nicht gelesen werden: {error}"
    pages = document.pageCount()
    if pages < 1:
        return None, "PDF enthält keine darstellbare Seite."
    page_size = document.pagePointSize(0)
    render_size = page_size.toSize()
    render_size.scale(target, Qt.AspectRatioMode.KeepAspectRatio)
    image = document.render(0, render_size)
    return (None if image.isNull() else image), f"Seiten: {pages}"


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

    if kind.key == "image":
        image = read_image_preview(path)
        if image is None:
            return PreviewData(kind.key, path.name, details, "Bild konnte nicht dargestellt werden.")
        return PreviewData(
            kind.key,
            path.name,
            details + f"\nVorschau: {image.width()} × {image.height()} Pixel",
            image=image,
        )

    if kind.key == "pdf":
        image, note = read_pdf_preview(path)
        return PreviewData(kind.key, path.name, details + "\n" + note, image=image)

    if kind.key in {"video", "audio"}:
        return PreviewData(
            kind.key,
            path.name,
            details,
            "Interne Wiedergabe ist bewusst deaktiviert. Mit „Extern öffnen“ wird das Standardprogramm verwendet.",
        )

    return PreviewData(
        kind.key,
        path.name,
        details,
        "Für diesen Dateityp gibt es noch keine interne Vorschau.",
    )
