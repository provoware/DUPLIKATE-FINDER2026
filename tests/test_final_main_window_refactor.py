from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / "app" / "gui"


def test_main_window_delegates_result_and_root_flows():
    source = (GUI / "main_window.py").read_text(encoding="utf-8")

    assert "ResultController(self)" in source
    assert "ScanRootController(self)" in source
    assert "result_controller.load_selected_state" in source
    assert "result_controller.save_selected_state" in source
    assert "result_controller.add_selected_to_collection" in source
    assert "scan_root_controller.choose" in source

    for method in (
        "_choose_root",
        "_selected_result_path",
        "_load_selected_result_state",
        "_save_selected_result_state",
        "_add_selected_result_to_collection",
    ):
        assert f"def {method}" not in source


def test_result_controller_owns_virtual_result_state():
    source = (GUI / "result_controller.py").read_text(encoding="utf-8")

    for method in (
        "selected_path",
        "load_selected_state",
        "save_selected_state",
        "add_selected_to_collection",
    ):
        assert f"def {method}" in source

    assert "database.virtual_item" in source
    assert "database.set_virtual_item" in source
    assert "database.add_collection_item" in source
    assert "results_model.set_marked" in source


def test_scan_root_controller_owns_shared_root_selection():
    source = (GUI / "scan_root_controller.py").read_text(encoding="utf-8")

    assert "QFileDialog.getExistingDirectory" in source
    assert "validate_scan_root" in source
    assert "selected_root" in source
    assert "root_label.setText" in source
    assert "duplicate_root.setText" in source


def test_page_building_stays_explicit_in_main_window():
    source = (GUI / "main_window.py").read_text(encoding="utf-8")

    for method in (
        "_dashboard_page",
        "_search_page",
        "_results_page",
        "_duplicates_page",
        "_collections_page",
        "_journal_page",
        "_help_page",
    ):
        assert f"def {method}" in source
