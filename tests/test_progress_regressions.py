from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def test_duplicate_progress_does_not_emit_false_100_between_phases():
    source=(ROOT/"app/core/duplicates.py").read_text(encoding="utf-8")
    assert 'ProgressInfo("Dateiinventur abgeschlossen"' not in source


def test_duplicate_finish_resets_controls_and_sets_100_percent():
    source=(ROOT/"app/gui/main_window.py").read_text(encoding="utf-8")
    start=source.index("def _duplicate_scan_finished")
    end=source.index("def _duplicate_scan_failed",start)
    block=source[start:end]
    assert "_set_process_idle()" in block
    assert "setValue(100)" in block
    assert "Restzeit: 0 s" in block


def test_duplicate_error_gets_solution():
    source=(ROOT/"app/gui/main_window.py").read_text(encoding="utf-8")
    start=source.index("def _duplicate_scan_failed")
    block=source[start:start+900]
    assert "record_error" in block
    assert "Lösung:" in block
