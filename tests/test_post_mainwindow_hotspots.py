from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_enhancements_delegate_portability_and_resources():
    source = (ROOT / "app/gui/enhancements.py").read_text(encoding="utf-8")

    assert "StatePortabilityController" in source
    assert "ResourceDashboardController" in source
    assert "portability_controller.export" in source
    assert "portability_controller.import_state" in source
    assert "resource_controller.refresh" in source
    assert "def _export_state" not in source
    assert "def _import_state" not in source
    assert "def _refresh_resources" not in source


def test_table_models_share_one_paging_contract():
    source = (ROOT / "app/gui/table_models.py").read_text(encoding="utf-8")

    assert "class _PagedTableModel" in source
    assert "class SearchResultsModel(_PagedTableModel)" in source
    assert "class DuplicateMembersModel(_PagedTableModel)" in source
    assert "class CollectionItemsModel(_PagedTableModel)" in source

    # Der gemeinsame Vertrag darf nicht erneut in jedem Modell dupliziert werden.
    assert source.count("def cached_row_count") == 1
    assert source.count("def rowCount") == 1
    assert source.count("def columnCount") == 1
    assert source.count("def headerData") == 1


def test_file_browser_stays_widget_focused_without_cosmetic_split():
    source = (ROOT / "app/file_browser/widget.py").read_text(encoding="utf-8")
    preview = (ROOT / "app/file_browser/preview.py").read_text(encoding="utf-8")

    assert "build_preview" in source
    assert "def build_preview" in preview
    assert "class FileBrowserWidget" in source
