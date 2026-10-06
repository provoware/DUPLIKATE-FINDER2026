from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


QUERY = "PROVOWARE_TESTLAB_TOKEN"


@dataclass(frozen=True)
class FileSpec:
    relative_path: str
    content: bytes


@dataclass(frozen=True)
class Expected:
    files: int
    search_hits: int
    duplicate_groups: int
    duplicate_files: int
    errors: int = 0


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    files: tuple[FileSpec, ...]
    expected: Expected
    create_symlink: bool = False


PROFILES: dict[str, Profile] = {
    "mini": Profile(
        "mini",
        "Schneller Grundtest für Suche und Duplikate",
        (
            FileSpec("docs/eins.txt", f"{QUERY}\n".encode()),
            FileSpec("duplikate/a.txt", b"IDENTISCH-MINI\n"),
            FileSpec("duplikate/b.txt", b"IDENTISCH-MINI\n"),
        ),
        Expected(files=3, search_hits=1, duplicate_groups=1, duplicate_files=2),
    ),
    "normal": Profile(
        "normal",
        "Typische gemischte Ordnerstruktur",
        (
            FileSpec("Dokumente/bericht.txt", f"{QUERY}\nBericht\n".encode()),
            FileSpec("Dokumente/todo.md", f"Aufgabe\n{QUERY}\n".encode()),
            FileSpec("Bilder/original.bin", b"EINZIGARTIG-BINAER"),
            FileSpec("Bilder/kopie_a.bin", b"GLEICHES-BILD"),
            FileSpec("Bilder/kopie_b.bin", b"GLEICHES-BILD"),
            FileSpec("Texte/kopie_a.txt", b"GLEICHER-TEXT\n"),
            FileSpec("Texte/kopie_b.txt", b"GLEICHER-TEXT\n"),
        ),
        Expected(files=7, search_hits=2, duplicate_groups=2, duplicate_files=4),
    ),
    "chaos": Profile(
        "chaos",
        "Leerzeichen, Unicode, tiefe Pfade, Symlink und gleiche Größen",
        (
            FileSpec("Leer zeichen/normal.txt", b"kein treffer\n"),
            FileSpec("Unicode/aeoeue-äöüß.txt", f"{QUERY}\n".encode("utf-8")),
            FileSpec("Tief/a/b/c/d/e/tief.txt", f"{QUERY}\n".encode()),
            FileSpec("Leer/leer.txt", b""),
            FileSpec("GleicheGroesse/eins.bin", b"AAAA"),
            FileSpec("GleicheGroesse/zwei.bin", b"BBBB"),
        ),
        Expected(files=6, search_hits=2, duplicate_groups=0, duplicate_files=0),
        create_symlink=True,
    ),
    "duplikate": Profile(
        "duplikate",
        "Mehrere sichere Duplikatgruppen unterschiedlicher Größe",
        (
            FileSpec("g1/a.bin", b"GRUPPE-EINS"),
            FileSpec("g1/b.bin", b"GRUPPE-EINS"),
            FileSpec("g1/c.bin", b"GRUPPE-EINS"),
            FileSpec("g2/a.txt", b"GRUPPE-ZWEI\n"),
            FileSpec("g2/b.txt", b"GRUPPE-ZWEI\n"),
            FileSpec("g3/a.bin", b"333333333333"),
            FileSpec("g3/b.bin", b"333333333333"),
            FileSpec("g3/c.bin", b"333333333333"),
            FileSpec("g3/d.bin", b"333333333333"),
            FileSpec("unique/einzig.bin", b"EINZIGARTIG"),
            FileSpec("search/treffer.txt", f"{QUERY}\n".encode()),
        ),
        Expected(files=11, search_hits=1, duplicate_groups=3, duplicate_files=9),
    ),
}


def available_profiles() -> tuple[str, ...]:
    return tuple(PROFILES)


def materialize_profile(profile: Profile, root: Path) -> None:
    for spec in profile.files:
        path = root / spec.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(spec.content)

    if profile.create_symlink and hasattr(os, "symlink"):
        link = root / "Symlink-nach-aussen"
        try:
            link.symlink_to(Path.home(), target_is_directory=True)
        except OSError:
            pass
