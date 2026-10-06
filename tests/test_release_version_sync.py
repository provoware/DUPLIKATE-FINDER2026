from pathlib import Path
import tomllib

ROOT=Path(__file__).resolve().parents[1]


def test_release_workflows_match_project_version():
    version=tomllib.loads((ROOT/"pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    dev=(ROOT/".github/workflows/development-full-bundle.yml").read_text(encoding="utf-8")
    portable=(ROOT/".github/workflows/portable-release.yml").read_text(encoding="utf-8")
    assert f"v{version}" in dev
    assert f'VERSION: "{version}"' in portable
    assert f"v{version}-linux-x86_64" in portable


def test_portable_docs_do_not_freeze_old_acceptance_count():
    text=(ROOT/"docs/PORTABLE_RELEASE.md").read_text(encoding="utf-8")
    assert "73/73" not in text
    assert "Mindestabdeckung" in text
