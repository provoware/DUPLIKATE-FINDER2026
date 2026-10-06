from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def test_no_tkinter_anywhere_in_python_source():
    import re

    offenders = []
    forbidden_import = re.compile(r"(?m)^\\s*(?:from\\s+tkinter(?:\\.|\\s)|import\\s+tkinter(?:\\.|\\s|$))")
    for source_root in (APP, ROOT / "tools"):
        for path in source_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8").casefold()
            if forbidden_import.search(text):
                offenders.append(str(path))
    assert offenders == []
    assert "tkinter" not in (ROOT / "pyproject.toml").read_text(encoding="utf-8").casefold()


def test_no_destructive_file_api_in_application():
    forbidden = (
        "shutil.move(",
        "os.remove(",
        "os.unlink(",
        "os.replace(",
        ".rename(",
        ".unlink(",
        "shutil.rmtree(",
    )
    offenders = []
    for path in APP.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            if needle in text:
                offenders.append(f"{path}:{needle}")
    assert offenders == []


def test_release_start_never_falls_back_to_system_python():
    text = (ROOT / "STARTEN.sh").read_text(encoding="utf-8")
    assert 'runtime/bin/python3' in text
    assert "python3 -m app.main" not in text
    assert "command -v python" not in text


def test_dashboard_keeps_write_features_visible_but_disabled():
    source = (APP / "gui" / "main_window.py").read_text(encoding="utf-8")
    assert "setEnabled(False)" in source
    for key in ("move_files", "rename_files", "quarantine", "delete_files"):
        assert key in (APP / "safety" / "policy.py").read_text(encoding="utf-8")


def test_startup_never_uses_system_package_manager_or_network_installer():
    sources = [
        (ROOT / "STARTEN.sh").read_text(encoding="utf-8").casefold(),
        (ROOT / "STARTEN_KONSOLE.sh").read_text(encoding="utf-8").casefold(),
        (APP / "startup" / "bootstrap.py").read_text(encoding="utf-8").casefold(),
    ]
    forbidden = ("sudo ", "apt install", "apt-get install", "dnf ", "pacman ", "zypper ", "curl ", "wget ")
    for source in sources:
        for needle in forbidden:
            assert needle not in source


def test_console_entrypoint_exists_and_reuses_core():
    source = (APP / "cli.py").read_text(encoding="utf-8")
    assert "TextSearcher" in source
    assert "scan_duplicate_groups" in source
    assert "validate_scan_root" in source

def test_development_start_is_self_bootstrapping():
    source = (ROOT / "ENTWICKLUNG_STARTEN.sh").read_text(encoding="utf-8")
    assert ".provoware-dev" in source
    assert "PYTHON_VERSION" in source
    assert "python3 -m venv" not in source
    assert "sudo " not in source
    assert "PySide6" in source

def test_dependency_contract_is_documented():
    assert (ROOT / "dependencies.env").is_file()
    assert (ROOT / "docs" / "ABHAENGIGKEITEN.md").is_file()
    text = (ROOT / "dependencies.env").read_text(encoding="utf-8")
    assert 'PYTHON_VERSION="3.12.15"' in text
    assert 'PYSIDE6_VERSION="6.11.2"' in text

