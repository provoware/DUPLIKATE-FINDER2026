from pathlib import Path

from app.core.search import MAX_TEXT_READ_CHARS, TextSearcher
from app.core.scanner import FileScanner
from app.models.entities import SearchJob


def test_search_names_and_contents(tmp_path: Path):
    (tmp_path / "urlaub.txt").write_text("Rechnung Müller\nzweite Zeile", encoding="utf-8")
    job = SearchJob(tmp_path, "müller", search_names=True, search_contents=True)
    hits = TextSearcher().search(job)
    assert any(hit.source == "inhalt" and hit.line_number == 1 for hit in hits)

    job2 = SearchJob(tmp_path, "urlaub", search_names=True, search_contents=False)
    hits2 = TextSearcher().search(job2)
    assert any(hit.source == "dateiname" for hit in hits2)


def test_search_finds_query_across_bounded_read_boundary(tmp_path: Path):
    query = "PROVOWARE-GRENZTEST"
    prefix = "x" * (MAX_TEXT_READ_CHARS - 8)
    (tmp_path / "lang.txt").write_text(prefix + query + "ende", encoding="utf-8")

    job = SearchJob(tmp_path, query, search_names=False, search_contents=True)
    hits = TextSearcher().search(job)

    assert len(hits) == 1
    assert hits[0].line_number == 1
    assert hits[0].source == "inhalt"


def test_search_skips_content_changed_after_inventory(tmp_path: Path):
    path = tmp_path / "wechsel.txt"
    path.write_text("alter inhalt", encoding="utf-8")
    scanner = FileScanner()
    records = list(scanner.iter_text_files(tmp_path))
    path.write_text("PROVOWARE neuer und deutlich längerer inhalt", encoding="utf-8")

    job = SearchJob(tmp_path, "PROVOWARE", search_names=False, search_contents=True)
    hits = TextSearcher(scanner).search(job, records=records, total_records=1)

    assert hits == []
    assert job.error_count == 1
