from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def catalog() -> dict:
    path=Path(__file__).resolve().parents[1]/"resources"/"texts"/"de-DE.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def text(path: str, default: str = "") -> str:
    current: object=catalog()
    for part in path.split("."):
        if not isinstance(current,dict) or part not in current:
            return default or path
        current=current[part]
    return str(current)
