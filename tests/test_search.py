from pathlib import Path

from app.core.search import TextSearcher
from app.models.entities import SearchJob


def test_search_names_and_contents(tmp_path: Path):
    (tmp_path / "urlaub.txt").write_text("Rechnung Müller\nzweite Zeile", encoding="utf-8")
    job = SearchJob(tmp_path, "müller", search_names=True, search_contents=True)
    hits = TextSearcher().search(job)
    assert any(hit.source == "inhalt" and hit.line_number == 1 for hit in hits)

    job2 = SearchJob(tmp_path, "urlaub", search_names=True, search_contents=False)
    hits2 = TextSearcher().search(job2)
    assert any(hit.source == "dateiname" for hit in hits2)
