from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.core.duplicates import scan_duplicate_groups_to_database
from app.core.scanner import FileScanner, ScanOptions
from app.core.search import TextSearcher
from app.models.entities import FileRecord, JobStatus, ScanIssue, SearchHit, SearchJob
from app.process_control import ProcessCancelled, ProcessControl, ProgressInfo
from app.storage.database import Database

LOGGER = logging.getLogger(__name__)


class BaseControlledWorker(QThread):
    progress = Signal(object)
    paused_changed = Signal(bool)
    cancelled = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.control = ProcessControl()

    def pause(self) -> None:
        self.control.pause()
        self.paused_changed.emit(True)

    def resume(self) -> None:
        self.control.resume()
        self.paused_changed.emit(False)

    def cancel(self) -> None:
        self.control.cancel()

    def _progress(self, info: ProgressInfo) -> None:
        self.progress.emit(info)


class SearchWorker(BaseControlledWorker):
    completed = Signal(object, int, int, int)
    failed = Signal(str)

    def __init__(
        self,
        job: SearchJob,
        database: Database,
        options: ScanOptions | None = None,
        batch_size: int = 200,
    ) -> None:
        super().__init__()
        self.job = job
        self.database = database
        self.options = options or ScanOptions()
        self.batch_size = max(25, int(batch_size))

    def run(self) -> None:
        job_id = 0
        run_id = 0
        hit_buffer: list[SearchHit] = []
        inventory_buffer: list[FileRecord] = []
        hit_count = 0

        try:
            self.job.status = JobStatus.RUNNING
            job_id = self.database.create_search_job(self.job)
            run_id = self.database.create_scan_run("search", self.job.root)

            def record_issue(issue: ScanIssue) -> None:
                self.database.record_scan_issue(run_id, issue)

            scanner = FileScanner(
                options=self.options,
                control=self.control,
                progress=self._progress,
                on_error=record_issue,
            )

            for record in scanner.iter_text_files(self.job.root):
                inventory_buffer.append(record)
                if len(inventory_buffer) >= 500:
                    self.database.append_scan_inventory(run_id, inventory_buffer)
                    inventory_buffer.clear()
            if inventory_buffer:
                self.database.append_scan_inventory(run_id, inventory_buffer)
                inventory_buffer.clear()

            total_records, total_bytes = self.database.scan_inventory_totals(run_id)

            def store_hit(hit: SearchHit) -> None:
                nonlocal hit_count
                hit_buffer.append(hit)
                hit_count += 1
                if len(hit_buffer) >= self.batch_size:
                    self.database.append_search_hits(job_id, list(hit_buffer))
                    hit_buffer.clear()

            TextSearcher(
                scanner,
                progress=self._progress,
                on_hit=store_hit,
                collect_hits=False,
            ).search(
                self.job,
                records=self.database.iter_scan_records(run_id),
                total_records=total_records,
                total_bytes=total_bytes,
            )

            if hit_buffer:
                self.database.append_search_hits(job_id, hit_buffer)

            error_count = self.database.scan_error_count(run_id)
            self.job.hits = hit_count
            self.job.error_count = error_count
            self.job.status = JobStatus.DONE
            self.database.finish_scan_run(run_id, "fertig", self.job.scanned_files)
            self.database.finish_search_job(
                job_id,
                status=self.job.status.value,
                scanned_files=self.job.scanned_files,
                hit_count=hit_count,
                error_count=error_count,
            )
            self.database.prune_search_jobs()
            self.database.prune_scan_runs()
            self.completed.emit(self.job, job_id, hit_count, error_count)
        except ProcessCancelled as exc:
            if run_id:
                self.database.finish_scan_run(
                    run_id, "abgebrochen", self.job.scanned_files
                )
            if job_id:
                if hit_buffer:
                    self.database.append_search_hits(job_id, hit_buffer)
                self.database.finish_search_job(
                    job_id,
                    status=JobStatus.CANCELLED.value,
                    scanned_files=self.job.scanned_files,
                    hit_count=hit_count,
                    error_count=(
                        self.database.scan_error_count(run_id) if run_id else 0
                    ),
                )
            self.cancelled.emit(str(exc))
        except Exception as exc:
            if run_id:
                self.database.finish_scan_run(
                    run_id, "fehler", self.job.scanned_files
                )
            if job_id:
                self.database.finish_search_job(
                    job_id,
                    status=JobStatus.FAILED.value,
                    scanned_files=self.job.scanned_files,
                    hit_count=hit_count,
                    error_count=(
                        self.database.scan_error_count(run_id) if run_id else 0
                    ),
                )
            LOGGER.exception("Hintergrundauftrag fehlgeschlagen")
            self.failed.emit(str(exc))


class DuplicateWorker(BaseControlledWorker):
    completed = Signal(int, int, int)
    failed = Signal(str)

    def __init__(
        self,
        root: Path,
        database: Database,
        options: ScanOptions | None = None,
    ) -> None:
        super().__init__()
        self.root = root
        self.database = database
        self.options = options or ScanOptions()

    def run(self) -> None:
        try:
            scanner = FileScanner(
                options=self.options,
                control=self.control,
                progress=self._progress,
            )
            scanned, group_count, error_count = scan_duplicate_groups_to_database(
                self.root,
                self.database,
                scanner=scanner,
                progress=self._progress,
            )
            self.completed.emit(scanned, group_count, error_count)
        except ProcessCancelled as exc:
            self.cancelled.emit(str(exc))
        except Exception as exc:
            LOGGER.exception("Hintergrundauftrag fehlgeschlagen")
            self.failed.emit(str(exc))
