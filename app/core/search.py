from __future__ import annotations

from pathlib import Path

from app.core.scanner import FileScanner
from app.models.entities import JobStatus, SearchHit, SearchJob


class TextSearcher:
    def __init__(self, scanner: FileScanner | None = None) -> None:
        self.scanner = scanner or FileScanner()

    def search(self, job: SearchJob) -> list[SearchHit]:
        query = job.query.casefold().strip()
        if not query:
            return []

        hits: list[SearchHit] = []
        job.status = JobStatus.RUNNING

        for record in self.scanner.iter_text_files(job.root):
            job.scanned_files += 1
            path = record.path

            if job.search_names and query in path.name.casefold():
                hits.append(SearchHit(path=path, line_number=None, excerpt=path.name, source="dateiname"))

            if job.search_contents:
                try:
                    with path.open("r", encoding="utf-8", errors="replace") as handle:
                        for number, line in enumerate(handle, start=1):
                            if query in line.casefold():
                                excerpt = line.strip()[:300]
                                hits.append(
                                    SearchHit(path=path, line_number=number, excerpt=excerpt, source="inhalt")
                                )
                except (OSError, PermissionError):
                    job.errors.append(str(path))

        job.hits = len(hits)
        job.status = JobStatus.DONE
        return hits
