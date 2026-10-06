from __future__ import annotations

import json
from pathlib import Path

from tools import build_metadata


def test_build_metadata_writes_sha_and_spdx(tmp_path: Path, monkeypatch):
    archive=tmp_path/"paket.tar.gz"
    archive.write_bytes(b"abc")
    output=tmp_path/"reports"
    monkeypatch.setattr("sys.argv",["build_metadata.py","--archive",str(archive),"--output-dir",str(output),"--commit","abc123"])
    assert build_metadata.main()==0
    build=json.loads((output/"BUILD-NACHWEIS.json").read_text(encoding="utf-8"))
    spdx=json.loads((output/"SBOM.spdx.json").read_text(encoding="utf-8"))
    assert build["archive"]["sha256"] == build_metadata.sha256(archive)
    assert spdx["spdxVersion"] == "SPDX-2.3"
    assert any(r["relationshipType"]=="DESCRIBES" for r in spdx["relationships"])
