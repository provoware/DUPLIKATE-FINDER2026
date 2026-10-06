from __future__ import annotations

import json
from pathlib import Path

from app.formatting import format_bytes
from tools.prepare_portable_variants import finalize_lite, make_lite


def test_format_bytes_is_consistent():
    assert format_bytes(0) == "0 B"
    assert format_bytes(1023) == "1023 B"
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1024 * 1024) == "1.0 MB"


def test_lite_profile_removes_only_known_distribution_payload(tmp_path: Path):
    recovery = tmp_path / "recovery"
    lite = tmp_path / "lite"
    for name in ("wheelhouse", "agents", "standards", "schemas", "templates", "tools", "app", "runtime"):
        (recovery / name).mkdir(parents=True, exist_ok=True)
        (recovery / name / "keep.txt").write_text(name, encoding="utf-8")
    docs = recovery / "docs"
    docs.mkdir()
    for name in ("LAIENANLEITUNG.md", "PORTABLE_RELEASE.md", "SICHERHEITSVERTRAG.md", "ARCHITEKTUR.md"):
        (docs / name).write_text(name, encoding="utf-8")

    make_lite(recovery, lite)

    assert (lite / "app").is_dir()
    assert (lite / "runtime").is_dir()
    assert (lite / "tools").is_dir()  # bis nach der E2E-Prüfung erforderlich
    assert not (lite / "wheelhouse").exists()
    assert not (lite / "agents").exists()
    assert not (lite / "standards").exists()
    assert not (lite / "schemas").exists()
    assert not (lite / "templates").exists()
    assert (lite / "docs" / "LAIENANLEITUNG.md").is_file()
    assert not (lite / "docs" / "ARCHITEKTUR.md").exists()

    profile = json.loads((lite / "PAKET-PROFIL.json").read_text(encoding="utf-8"))
    assert profile["profile"] == "lite"
    assert profile["offline_gui_repair"] is False
    assert profile["runtime_pruned"] is False

    finalize_lite(lite)
    assert not (lite / "tools").exists()
