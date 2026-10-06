from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_acceptance_minimum_is_registered_and_not_stale():
    manifest=json.loads((ROOT/"manifest/project.manifest.json").read_text(encoding="utf-8"))
    minimum=manifest["quality"]["minimum_acceptance_checks"]
    assert isinstance(minimum,int)
    assert minimum >= 81


def test_portable_workflow_uses_manifest_minimum_instead_of_exact_old_count():
    text=(ROOT/".github/workflows/portable-release.yml").read_text(encoding="utf-8")
    assert 'minimum_acceptance_checks' in text
    assert 'len(results) == 73' not in text


def test_full_ci_is_reserved_for_main_and_pull_requests():
    ci=(ROOT/".github/workflows/ci.yml").read_text(encoding="utf-8")
    acceptance=(ROOT/".github/workflows/acceptance.yml").read_text(encoding="utf-8")
    assert 'branches: [main]' in ci
    assert 'branches: [main]' in acceptance
    assert (ROOT/".github/workflows/targeted.yml").is_file()


def test_release_workflows_derive_version_from_pyproject():
    root=Path(__file__).resolve().parents[1]
    for rel in (
        ".github/workflows/development-full-bundle.yml",
        ".github/workflows/portable-release.yml",
    ):
        text=(root/rel).read_text(encoding="utf-8")
        assert "tomllib" in text
        assert "pyproject.toml" in text
        assert "v0.3.0" not in text
