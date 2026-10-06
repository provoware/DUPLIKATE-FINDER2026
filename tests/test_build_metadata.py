from __future__ import annotations

import json
import tomllib
from pathlib import Path

from tools import build_metadata
import app


def test_build_metadata_writes_sha_and_spdx(tmp_path: Path, monkeypatch):
    archive=tmp_path/"paket.tar.gz"
    archive.write_bytes(b"abc")
    output=tmp_path/"reports"
    monkeypatch.setattr("sys.argv",["build_metadata.py","--archive",str(archive),"--output-dir",str(output),"--commit","abc123"])
    assert build_metadata.main()==0
    build=json.loads((output/"BUILD-NACHWEIS.json").read_text(encoding="utf-8"))
    spdx=json.loads((output/"SBOM.spdx.json").read_text(encoding="utf-8"))
    assert build["archive"]["sha256"] == build_metadata.sha256(archive)
    assert build["project_version"] == app.__version__
    assert spdx["packages"][0]["versionInfo"] == app.__version__
    assert spdx["spdxVersion"] == "SPDX-2.3"
    assert any(r["relationshipType"]=="DESCRIBES" for r in spdx["relationships"])


def test_application_version_matches_project_metadata():
    root=Path(__file__).resolve().parents[1]
    expected=tomllib.loads((root/"pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    assert app.__version__==expected
