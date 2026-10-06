from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def test_dashboard_cards_use_compact_two_by_two_layout():
    source=(ROOT/"app/gui/main_window.py").read_text(encoding="utf-8")
    start=source.index("def _card")
    block=source[start:source.index("def _build_ui",start)]
    assert "QHBoxLayout(frame)" in block
    dashboard=source[source.index("def _dashboard_page"):source.index("def _root_selector")]
    assert '"Vorgang", "🟢 Bereit", "dashboard_process_metrics"' in dashboard
    assert '"Ressourcen", "CPU – · RAM – · SWAP –", "dashboard_resource_metrics"' in dashboard
    assert 'self._card("Datenbank", "🟢 Lokal · SQLite"), 1, 1' in dashboard
    assert 'cards.addWidget(process_card, 0, 1)' in dashboard
    assert 'cards.addWidget(resource_card, 1, 0)' in dashboard
