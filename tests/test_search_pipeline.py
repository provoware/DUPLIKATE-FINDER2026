from pathlib import Path

from app.core.search_pipeline import run_search_to_database
from app.models.entities import JobStatus, SearchJob
from app.storage.database import Database


def test_search_pipeline_persists_hits_and_finishes_job(tmp_path: Path):
    root = tmp_path / "docs"
    root.mkdir()
    (root / "eins.txt").write_text("alpha beta", encoding="utf-8")
    (root / "zwei.txt").write_text("ohne treffer", encoding="utf-8")

    database = Database(tmp_path / "test.sqlite3")
    database.initialize()
    job = SearchJob(
        root=root,
        query="alpha",
        search_names=False,
        search_contents=True,
    )

    result = run_search_to_database(
        job,
        database,
        run_kind="search-test",
    )

    assert result.job_id > 0
    assert result.hit_count == 1
    assert result.error_count == 0
    assert job.status == JobStatus.DONE
    assert database.search_hit_count(result.job_id) == 1

    page = database.search_hits_page(
        result.job_id,
        offset=0,
        limit=10,
        sort_column=2,
    )
    assert len(page) == 1
    assert page[0][0].path.name == "eins.txt"


def test_gui_worker_and_cli_use_shared_search_pipeline():
    root = Path(__file__).resolve().parents[1]
    worker = (root / "app/gui/workers.py").read_text(encoding="utf-8")
    cli = (root / "app/cli.py").read_text(encoding="utf-8")

    assert "run_search_to_database" in worker
    assert "run_search_to_database" in cli
    assert "TextSearcher(" not in worker
    assert "TextSearcher(" not in cli
