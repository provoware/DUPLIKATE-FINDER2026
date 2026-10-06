from __future__ import annotations

import json
from pathlib import Path

from app.workspace import REQUIRED_DIRS, ensure_workspace


def test_workspace_is_created_with_required_folders(tmp_path: Path):
    root=ensure_workspace(tmp_path/"PROVOWARE"/"DUPLIKATE-FINDER-2026")
    assert root.is_dir()
    for name in REQUIRED_DIRS:
        assert (root/name).is_dir()
    manifest=json.loads((root/"config"/"arbeitsordner.json").read_text(encoding="utf-8"))
    assert manifest["workspace"] == str(root)


def test_workspace_reuses_existing_folder(tmp_path: Path):
    root=ensure_workspace(tmp_path/"workspace")
    marker=root/"data"/"marker.txt"
    marker.write_text("bleibt",encoding="utf-8")
    same=ensure_workspace(root)
    assert same == root
    assert marker.read_text(encoding="utf-8") == "bleibt"
