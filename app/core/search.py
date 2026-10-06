from __future__ import annotations

from collections.abc import Callable

from app.core.scanner import FileScanner
from app.models.entities import JobStatus, SearchHit, SearchJob
from app.process_control import ProgressInfo, ProgressTracker


ProgressCallback=Callable[[ProgressInfo],None]


class TextSearcher:
    def __init__(self,scanner:FileScanner|None=None,progress:ProgressCallback|None=None)->None:
        self.scanner=scanner or FileScanner()
        self.progress=progress

    def search(self,job:SearchJob)->list[SearchHit]:
        query=job.query.casefold().strip()
        if not query:
            return []

        hits:list[SearchHit]=[]
        job.status=JobStatus.RUNNING
        records=list(self.scanner.iter_text_files(job.root))
        pause_provider=(lambda:self.scanner.control.paused_seconds) if self.scanner.control else None
        tracker=ProgressTracker(len(records),"Textdateien durchsuchen",pause_provider)
        processed_bytes=0

        for index,record in enumerate(records,start=1):
            self.scanner._checkpoint()
            job.scanned_files+=1
            path=record.path

            if job.search_names and query in path.name.casefold():
                hits.append(SearchHit(path=path,line_number=None,excerpt=path.name,source="dateiname"))

            if job.search_contents:
                try:
                    with path.open("r",encoding="utf-8",errors="replace") as handle:
                        for number,line in enumerate(handle,start=1):
                            self.scanner._checkpoint()
                            if query in line.casefold():
                                hits.append(SearchHit(
                                    path=path,line_number=number,excerpt=line.strip()[:300],source="inhalt"
                                ))
                    processed_bytes+=record.size
                except (OSError,PermissionError):
                    job.errors.append(str(path))

            if self.progress:
                self.progress(tracker.update(
                    index,
                    f"Text prüfen · Datei {index} von {len(records)}",
                    processed_bytes=processed_bytes,
                ))

        job.hits=len(hits)
        job.status=JobStatus.DONE
        return hits
