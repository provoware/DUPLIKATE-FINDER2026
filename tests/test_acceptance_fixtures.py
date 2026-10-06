from pathlib import Path

from app.core.duplicates import scan_duplicate_groups
from app.core.search import TextSearcher
from app.models.entities import SearchJob

FIXTURES = Path(__file__).parent / "fixtures"


def test_real_fixture_search_contract():
    job = SearchJob(root=FIXTURES, query="Nadelwort", search_names=True, search_contents=True)
    hits = TextSearcher().search(job)
    assert len(hits) == 3


def test_real_fixture_duplicate_contract():
    _, groups = scan_duplicate_groups(FIXTURES)
    matching = [group for group in groups if {p.name for p in group.paths} == {"kopie_a.bin", "kopie_b.bin"}]
    assert len(matching) == 1
