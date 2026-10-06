from __future__ import annotations

from collections.abc import Callable, Iterable

from app.core.scanner import FileScanner
from app.models.entities import FileRecord, JobStatus, SearchHit, SearchJob
from app.process_control import ProgressInfo, ProgressTracker


ProgressCallback = Callable[[ProgressInfo], None]
HitCallback = Callable[[SearchHit], None]


class TextSearcher:
    def __init__(
        self,
        scanner: FileScanner | None = None,
        progress: ProgressCallback | None = None,
        on_hit: HitCallback | None = None,
        collect_hits: bool = True,
    ) -> None:
        self.scanner = scanner or FileScanner()
        self.progress = progress
        self.on_hit = on_hit
        self.collect_hits = collect_hits

    def _record_hit(self, hits: list[SearchHit], hit: SearchHit) -> None:
        if self.collect_hits:
            hits.append(hit)
        if self.on_hit:
            self.on_hit(hit)

    def search(
        self,
        job: SearchJob,
        *,
        records: Iterable[FileRecord] | None = None,
        total_records: int = 0,
        total_bytes: int = 0,
    ) -> list[SearchHit]:
        query = job.query.casefold().strip()
        if not query:
            return []

        hits: list[SearchHit] = []
        job.status = JobStatus.RUNNING
        source = records if records is not None else self.scanner.iter_text_files(job.root)
        pause_provider = (
            (lambda: self.scanner.control.paused_seconds)
            if self.scanner.control
            else None
        )
        tracker = ProgressTracker(
            max(0, int(total_records)),
            "Textdateien durchsuchen",
            pause_provider,
            total_bytes=max(0, int(total_bytes)) if job.search_contents else 0,
        )
        processed_bytes = 0

        for index, record in enumerate(source, start=1):
            self.scanner._checkpoint()
            job.scanned_files += 1
            path = record.path

            if job.search_names and query in path.name.casefold():
                self._record_hit(
                    hits,
                    SearchHit(
                        path=path,
                        line_number=None,
                        excerpt=path.name,
                        source="dateiname",
                    ),
                )

            if job.search_contents:
                try:
                    with path.open(
                        "r",
                        encoding="utf-8",
                        errors="replace",
                    ) as handle:
                        for number, line in enumerate(handle, start=1):
                            self.scanner._checkpoint()
                            if query in line.casefold():
                                self._record_hit(
                                    hits,
                                    SearchHit(
                                        path=path,
                                        line_number=number,
                                        excerpt=line.strip()[:300],
                                        source="inhalt",
                                    ),
                                )
                    processed_bytes += record.size
                except OSError as exc:
                    if len(job.errors) < 100:
                        job.errors.append(str(path))
                    self.scanner.report_error(path, "Textinhalt lesen", exc)

            if self.progress:
                total = max(0, int(total_records))
                step = (
                    f"Text prüfen · Datei {index} von {total}"
                    if total
                    else f"Text prüfen · {index} Dateien"
                )
                self.progress(
                    tracker.update(
                        index,
                        step,
                        processed_bytes=processed_bytes,
                    )
                )

        if self.collect_hits:
            job.hits = len(hits)
        job.error_count = self.scanner.error_count
        job.status = JobStatus.DONE
        return hits
