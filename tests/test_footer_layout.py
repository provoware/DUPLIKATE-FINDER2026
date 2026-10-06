from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def test_footer_uses_independent_rows_not_shared_grid_columns():
    source=(ROOT/"app/gui/main_window.py").read_text(encoding="utf-8")
    start=source.index('footer = QVBoxLayout()')
    end=source.index('self.nav.currentRowChanged',start)
    block=source[start:end]
    assert "status_row = QHBoxLayout()" in block
    assert "control_row = QHBoxLayout()" in block
    assert 'self.pause_button.setProperty("compact", True)' in block
    assert 'self.cancel_button.setProperty("compact", True)' in block
    assert "footer = QGridLayout()" not in block
