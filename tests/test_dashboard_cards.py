from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def test_dashboard_cards_use_clear_four_column_layout():
    source=(ROOT/"app/gui/main_window.py").read_text(encoding="utf-8")
    start=source.index("def _card")
    block=source[start:source.index("def _build_ui",start)]
    assert "QVBoxLayout(frame)" in block
    assert 'setProperty("cardTitle", True)' in block
    assert 'setProperty("cardValue", True)' in block
    dashboard=source[source.index("def _dashboard_page"):source.index("def _root_selector")]
    assert '"Vorgang", "Bereit", "dashboard_process_metrics"' in dashboard
    assert '"Ressourcen", "CPU – · RAM – · SWAP –", "dashboard_resource_metrics"' in dashboard
    assert 'self._card("Datenbank", "Lokal · SQLite")' in dashboard
    assert 'self.dashboard_cards.extend((process_card, resource_card' in dashboard
    assert 'checkbox.setText(f"{text} · gesperrt")' in dashboard
    responsive=source[source.index("def _update_dashboard_card_layout"):source.index("def resizeEvent")]
    assert 'columns = 2 if int(self.property("uiZoom") or 100) >= 150 else 4' in responsive
    assert 'self.dashboard_card_layout.addWidget(card, index // columns, index % columns)' in responsive
