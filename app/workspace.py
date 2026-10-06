from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

WORKSPACE_ENV = "PROVOWARE_PROJECT_DIR"
DEFAULT_RELATIVE = Path("PROVOWARE") / "DUPLIKATE-FINDER-2026"
REQUIRED_DIRS = ("data","logs","recovery","quarantine","exports","reports","checkpoints","config")


def default_workspace() -> Path:
    configured=os.environ.get(WORKSPACE_ENV,"").strip()
    return Path(configured).expanduser() if configured else Path.home()/DEFAULT_RELATIVE


def ensure_workspace(path: Path | None = None) -> Path:
    root=(path or default_workspace()).expanduser().resolve(strict=False)
    if root == Path("/"):
        raise RuntimeError("Der Projektordner darf nicht das Linux-Wurzelverzeichnis sein.")
    root.mkdir(parents=True,exist_ok=True)
    for name in REQUIRED_DIRS:
        (root/name).mkdir(parents=True,exist_ok=True)
    manifest=root/"config"/"arbeitsordner.json"
    payload={
        "schema_version":"1.0.0",
        "application":"PROVOWARE DUPLIKATE-FINDER 2026",
        "workspace":str(root),
        "required_directories":list(REQUIRED_DIRS),
        "updated_at":datetime.now().astimezone().isoformat(),
    }
    manifest.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    return root
