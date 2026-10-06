from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib


def _project_version() -> str:
    metadata = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if metadata.is_file():
        try:
            return str(tomllib.loads(metadata.read_text(encoding="utf-8"))["project"]["version"])
        except (OSError, KeyError, tomllib.TOMLDecodeError):
            pass
    try:
        return version("provoware-duplicate-finder-2026")
    except PackageNotFoundError:
        return "0+unbekannt"


__version__ = _project_version()
