from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def _imports_forbidden(text: str, module: str) -> bool:
    return (
        f"from {module}" in text
        or f"import {module}" in text
    )


def test_core_and_storage_do_not_depend_on_gui_or_testlab():
    offenders: list[str] = []
    for folder in (APP / "core", APP / "storage"):
        for path in folder.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            for forbidden in ("app.gui", "app.testing"):
                if _imports_forbidden(source, forbidden):
                    offenders.append(f"{path.relative_to(ROOT)} -> {forbidden}")
    assert offenders == []


def test_testlab_does_not_depend_on_gui():
    offenders: list[str] = []
    for path in (APP / "testing").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if _imports_forbidden(source, "app.gui"):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_main_cli_delegates_testlab_details():
    source = (APP / "cli.py").read_text(encoding="utf-8")

    assert "configure_testlab_arguments" in source
    assert "run_requested_testlab" in source
    assert "run_performance_profile" not in source
    assert "run_fault_injection_suite" not in source
    assert "write_performance_report" not in source
