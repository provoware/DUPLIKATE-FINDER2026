from __future__ import annotations

from collections.abc import Callable

from app.core.control import ProcessControl
from app.core.scanner import FileScanner, ScanOptions
from app.models.entities import JobStatus, SearchHit, SearchJob

ProgressCallback = Callable[[int, int, str], None]


class TextSearcher:
    def __init__(self, scanner: FileScanner | None = None) -> None:
        self.scanner = scanner or FileScanner()

    def search(
        self,
        job: SearchJob,
        *,
        options: ScanOptions | None = None,
        control: ProcessControl | None = None,
        progress: ProgressCallback | None = None,
    ) -> list[SearchHit]:
        query = job.query.casefold().strip()
        if not query:
            return []

        hits: list[SearchHit] = []
        job.status = JobStatus.RUNNING

        def discovered(count: int, _path) -> None:
            if progress is not None and (count == 1 or count % 25 == 0):
                progress(count, 0, "Dateiliste wird aufgebaut")

        records = list(
            self.scanner.iter_text_files(
                job.root,
                options=options,
                control=control,
                on_discovered=discovered,
            )
        )
        total = len(records)
        if progress is not None:
            progress(0, total, "Textdateien werden durchsucht")

        for index, record in enumerate(records, start=1):
            if control is not None:
                control.checkpoint()
            job.scanned_files += 1
            path = record.path

            if job.search_names and query in path.name.casefold():
                hits.append(SearchHit(path=path, line_number=None, excerpt=path.name, source="dateiname"))

            if job.search_contents:
                try:
                    with path.open("r", encoding="utf-8", errors="replace") as handle:
                        for number, line in enumerate(handle, start=1):
                            if control is not None and number % 128 == 0:
                                control.checkpoint()
                            if query in line.casefold():
                                excerpt = line.strip()[:300]
                                hits.append(
                                    SearchHit(path=path, line_number=number, excerpt=excerpt, source="inhalt")
                                )
                except (OSError, PermissionError):
                    job.errors.append(str(path))

            if progress is not None:
                progress(index, total, "Textdateien werden durchsucht")

        job.hits = len(hits)
        job.status = JobStatus.DONE
        return hits
