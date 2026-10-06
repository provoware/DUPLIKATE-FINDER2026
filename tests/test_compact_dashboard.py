from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def test_dashboard_status_strip_stays_compact():
    source=(ROOT/"app/gui/enhancements.py").read_text(encoding="utf-8")
    assert 'QPushButton("🧰 Werkzeuge")' in source
    assert 'self.autosave_info=QLabel("💾 Auto:' in source
    assert 'grid.addWidget(self.size_combo, 0, 2)' in source
    assert 'grid.addWidget(self.cpu_combo, 1, 0)' in source
