from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


TEXT_EXTENSIONS = frozenset({
    ".txt", ".md", ".csv", ".log", ".json", ".xml", ".yaml", ".yml",
    ".ini", ".conf", ".py", ".sh", ".toml", ".rst", ".sql", ".html",
    ".htm", ".css", ".js", ".ts",
})
IMAGE_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff",
})
PDF_EXTENSIONS = frozenset({".pdf"})
DOCUMENT_EXTENSIONS = frozenset({".docx", ".odt"})
VIDEO_EXTENSIONS = frozenset({
    ".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v", ".mpeg", ".mpg",
})
AUDIO_EXTENSIONS = frozenset({
    ".mp3", ".wav", ".flac", ".ogg", ".oga", ".m4a", ".aac",
})


@dataclass(frozen=True)
class FileKind:
    key: str
    label: str


KINDS = {
    "directory": FileKind("directory", "Ordner"),
    "text": FileKind("text", "Text"),
    "image": FileKind("image", "Bild"),
    "pdf": FileKind("pdf", "PDF"),
    "document": FileKind("document", "Dokument"),
    "video": FileKind("video", "Video"),
    "audio": FileKind("audio", "Audio"),
    "other": FileKind("other", "Andere Datei"),
}


def classify_path(path: Path, *, is_dir: bool | None = None) -> FileKind:
    if is_dir is True or (is_dir is None and path.is_dir()):
        return KINDS["directory"]
    suffix = path.suffix.casefold()
    if suffix in TEXT_EXTENSIONS:
        return KINDS["text"]
    if suffix in IMAGE_EXTENSIONS:
        return KINDS["image"]
    if suffix in PDF_EXTENSIONS:
        return KINDS["pdf"]
    if suffix in DOCUMENT_EXTENSIONS:
        return KINDS["document"]
    if suffix in VIDEO_EXTENSIONS:
        return KINDS["video"]
    if suffix in AUDIO_EXTENSIONS:
        return KINDS["audio"]
    return KINDS["other"]


def known_extensions() -> frozenset[str]:
    return frozenset().union(
        TEXT_EXTENSIONS,
        IMAGE_EXTENSIONS,
        PDF_EXTENSIONS,
        DOCUMENT_EXTENSIONS,
        VIDEO_EXTENSIONS,
        AUDIO_EXTENSIONS,
    )
