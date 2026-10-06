from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def catalog() -> dict:
    manifest_path = _root() / "resources" / "texts" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    active = manifest.get("active_locale", "de-DE")
    entry = next(
        (item for item in manifest.get("catalogs", []) if item.get("locale") == active),
        None,
    )
    if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
        raise RuntimeError("Aktiver PROVOWARE-Textkatalog fehlt.")
    path = _root() / entry["path"]
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("locale") != active or data.get("catalog_version") != entry.get("version"):
        raise RuntimeError("PROVOWARE-Textkatalog und Manifest passen nicht zusammen.")
    return data


def text(path: str, default: str = "") -> str:
    current: object = catalog()
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default or path
        current = current[part]
    return str(current)
