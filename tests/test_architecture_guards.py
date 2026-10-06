from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def test_no_tkinter_in_application_source():
    offenders = []
    for path in APP.rglob("*.py"):
        text = path.read_text(encoding="utf-8").casefold()
        if "tkinter" in text or "from tk" in text:
            offenders.append(str(path))
    assert offenders == []


def test_no_destructive_file_api_in_application():
    forbidden = (
        "shutil.move(",
        "os.remove(",
        "os.unlink(",
        ".rename(",
        ".replace(",
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
