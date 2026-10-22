from pathlib import Path

import pytest

from app.core.search import TextSearcher
from app.models.entities import JobStatus, SearchJob


def test_unexpected_record_failure_marks_job_failed():
    job = SearchJob(root=Path('/tmp'), query='probe')

    def broken_records():
        raise RuntimeError('Testfehler beim Lesen')
        yield

    with pytest.raises(RuntimeError, match='Testfehler'):
        TextSearcher().search(job, records=broken_records())
    assert job.status == JobStatus.FAILED


def test_empty_query_does_not_start_job():
    job = SearchJob(root=Path('/tmp'), query='  ')
    assert TextSearcher().search(job, records=[]) == []
    assert job.status == JobStatus.PENDING
