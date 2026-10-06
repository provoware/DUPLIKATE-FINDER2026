from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / "app" / "gui"


def test_main_window_delegates_process_control_to_controller():
    source = (GUI / "main_window.py").read_text(encoding="utf-8")

    assert "ProcessUiController(self)" in source
    assert "process_controller.toggle_pause" in source
    assert "process_controller.cancel_active_process" in source
    assert "process_controller.connect_worker_controls" in source
    assert "def _on_process_progress" not in source
    assert "def _toggle_pause" not in source
    assert "def _cancel_active_process" not in source


def test_process_controller_owns_process_feedback_logic():
    source = (GUI / "process_controller.py").read_text(encoding="utf-8")

    for method in (
        "connect_worker_controls",
        "toggle_pause",
        "cancel_active_process",
        "process_cancelled",
        "on_progress",
        "set_idle",
    ):
        assert f"def {method}" in source

    assert "format_eta" in source
    assert "format_bytes" in source
    assert "QMessageBox.question" in source
