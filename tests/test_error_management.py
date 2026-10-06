from pathlib import Path

from app.error_management import record_error, solution_for


def test_error_record_always_contains_solution(tmp_path: Path):
    entry=record_error(tmp_path,"test","Datei nicht gefunden")
    assert entry["solution"]
    assert entry["fingerprint"]
    assert (tmp_path/"fehlerkatalog.jsonl").is_file()


def test_known_permission_error_has_concrete_solution():
    assert "Schreibrechte" in solution_for("Permission denied")
