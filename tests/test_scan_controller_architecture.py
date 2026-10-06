from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / "app" / "gui"


def test_main_window_delegates_search_and_duplicate_flows():
    source = (GUI / "main_window.py").read_text(encoding="utf-8")

    assert "SearchController(self)" in source
    assert "DuplicateController(self)" in source
    assert "search_controller.start" in source
    assert "duplicate_controller.start" in source
    assert "duplicate_controller.show_group" in source

    for method in (
        "_start_search",
        "_search_finished",
        "_search_failed",
        "_start_duplicate_scan",
        "_duplicate_scan_finished",
        "_duplicate_scan_failed",
        "_fill_duplicate_groups",
        "_show_duplicate_group",
    ):
        assert f"def {method}" not in source


def test_shared_scan_ui_support_owns_only_common_flow():
    support = (GUI / "scan_controller_support.py").read_text(encoding="utf-8")
    search = (GUI / "search_controller.py").read_text(encoding="utf-8")
    duplicate = (GUI / "duplicate_controller.py").read_text(encoding="utf-8")

    for helper in (
        "show_validation_error",
        "current_scan_options",
        "prepare_process_start",
        "fail_process",
    ):
        assert f"def {helper}" in support

    assert "prepare_process_start" in search
    assert "prepare_process_start" in duplicate
    assert "current_scan_options" in search
    assert "current_scan_options" in duplicate
    assert "fail_process" in search
    assert "fail_process" in duplicate
