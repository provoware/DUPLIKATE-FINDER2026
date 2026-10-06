from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.core.duplicates import scan_duplicate_groups
from app.core.scanner import FileScanner, ScanOptions
from app.core.search import TextSearcher
from app.models.entities import JobStatus, SearchHit, SearchJob
from app.process_control import ProcessCancelled, ProcessControl, ProgressInfo
from app.storage.database import Database

LOGGER=logging.getLogger(__name__)


class BaseControlledWorker(QThread):
    progress=Signal(object)
    paused_changed=Signal(bool)
    cancelled=Signal(str)

    def __init__(self)->None:
        super().__init__()
        self.control=ProcessControl()

    def pause(self)->None:
        self.control.pause()
        self.paused_changed.emit(True)

    def resume(self)->None:
        self.control.resume()
        self.paused_changed.emit(False)

    def cancel(self)->None:
        self.control.cancel()

    def _progress(self,info:ProgressInfo)->None:
        self.progress.emit(info)


class SearchWorker(BaseControlledWorker):
    completed=Signal(object,int,int)
    failed=Signal(str)

    def __init__(
        self,
        job:SearchJob,
        database:Database,
        options:ScanOptions|None=None,
        batch_size:int=200,
    )->None:
        super().__init__()
        self.job=job
        self.database=database
        self.options=options or ScanOptions()
        self.batch_size=max(25,int(batch_size))

    def run(self)->None:
        job_id=0
        buffer:list[SearchHit]=[]
        hit_count=0
        try:
            self.job.status=JobStatus.RUNNING
            job_id=self.database.create_search_job(self.job)

            def store_hit(hit:SearchHit)->None:
                nonlocal hit_count
                buffer.append(hit)
                hit_count+=1
                if len(buffer)>=self.batch_size:
                    self.database.append_search_hits(job_id,list(buffer))
                    buffer.clear()

            scanner=FileScanner(options=self.options,control=self.control,progress=self._progress)
            TextSearcher(
                scanner,
                progress=self._progress,
                on_hit=store_hit,
                collect_hits=False,
            ).search(self.job)
            if buffer:
                self.database.append_search_hits(job_id,buffer)
            self.job.hits=hit_count
            self.job.status=JobStatus.DONE
            self.database.finish_search_job(
                job_id,status=self.job.status.value,
                scanned_files=self.job.scanned_files,hit_count=hit_count,
            )
            self.completed.emit(self.job,job_id,hit_count)
        except ProcessCancelled as exc:
            if job_id:
                if buffer:
                    self.database.append_search_hits(job_id,buffer)
                self.database.finish_search_job(
                    job_id,status=JobStatus.CANCELLED.value,
                    scanned_files=self.job.scanned_files,hit_count=hit_count,
                )
            self.cancelled.emit(str(exc))
        except Exception as exc:
            if job_id:
                self.database.finish_search_job(
                    job_id,status=JobStatus.FAILED.value,
                    scanned_files=self.job.scanned_files,hit_count=hit_count,
                )
            LOGGER.exception("Hintergrundauftrag fehlgeschlagen")
            self.failed.emit(str(exc))


class DuplicateWorker(BaseControlledWorker):
    completed=Signal(int,object)
    failed=Signal(str)

    def __init__(self,root:Path,options:ScanOptions|None=None)->None:
        super().__init__()
        self.root=root
        self.options=options or ScanOptions()

    def run(self)->None:
        try:
            scanner=FileScanner(options=self.options,control=self.control,progress=self._progress)
            scanned,groups=scan_duplicate_groups(self.root,scanner=scanner,progress=self._progress)
            self.completed.emit(scanned,groups)
        except ProcessCancelled as exc:
            self.cancelled.emit(str(exc))
        except Exception as exc:
            LOGGER.exception("Hintergrundauftrag fehlgeschlagen")
            self.failed.emit(str(exc))
