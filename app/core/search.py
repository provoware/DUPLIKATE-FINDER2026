from __future__ import annotations

from collections.abc import Callable

from app.core.scanner import FileScanner
from app.models.entities import JobStatus, SearchHit, SearchJob
from app.process_control import ProgressInfo, ProgressTracker


ProgressCallback=Callable[[ProgressInfo],None]
HitCallback=Callable[[SearchHit],None]


class TextSearcher:
    def __init__(
        self,
        scanner:FileScanner|None=None,
        progress:ProgressCallback|None=None,
        on_hit:HitCallback|None=None,
        collect_hits:bool=True,
    )->None:
        self.scanner=scanner or FileScanner()
        self.progress=progress
        self.on_hit=on_hit
        self.collect_hits=collect_hits

    def _record_hit(self,hits:list[SearchHit],hit:SearchHit)->None:
        if self.collect_hits:
            hits.append(hit)
        if self.on_hit:
            self.on_hit(hit)

    def search(self,job:SearchJob)->list[SearchHit]:
        query=job.query.casefold().strip()
        if not query:
            return []

        hits:list[SearchHit]=[]
        job.status=JobStatus.RUNNING
        records=list(self.scanner.iter_text_files(job.root))
        pause_provider=(lambda:self.scanner.control.paused_seconds) if self.scanner.control else None
        total_bytes=sum(record.size for record in records) if job.search_contents else 0
        tracker=ProgressTracker(
            len(records),"Textdateien durchsuchen",pause_provider,total_bytes=total_bytes
        )
        processed_bytes=0

        for index,record in enumerate(records,start=1):
            self.scanner._checkpoint()
            job.scanned_files+=1
            path=record.path

            if job.search_names and query in path.name.casefold():
                self._record_hit(
                    hits,
                    SearchHit(path=path,line_number=None,excerpt=path.name,source="dateiname"),
                )

            if job.search_contents:
                try:
                    with path.open("r",encoding="utf-8",errors="replace") as handle:
                        for number,line in enumerate(handle,start=1):
                            self.scanner._checkpoint()
                            if query in line.casefold():
                                self._record_hit(
                                    hits,
                                    SearchHit(
                                        path=path,line_number=number,excerpt=line.strip()[:300],source="inhalt"
                                    ),
                                )
                    processed_bytes+=record.size
                except (OSError,PermissionError):
                    job.errors.append(str(path))

            if self.progress:
                self.progress(tracker.update(
                    index,
                    f"Text prüfen · Datei {index} von {len(records)}",
                    processed_bytes=processed_bytes,
                ))

        if self.collect_hits:
            job.hits=len(hits)
        job.status=JobStatus.DONE
        return hits
