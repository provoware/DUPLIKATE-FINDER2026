from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.core.scanner import FileScanner, ScanOptions
from app.core.search import TextSearcher
from app.models.entities import FileRecord, JobStatus, ScanIssue, SearchHit, SearchJob
from app.process_control import ProcessCancelled, ProcessControl, ProgressInfo
from app.storage.database import Database


ProgressCallback = Callable[[ProgressInfo], None]


@dataclass(frozen=True)
class SearchPipelineResult:
    job_id: int
    hit_count: int
    error_count: int


def run_search_to_database(
    job: SearchJob,
    database: Database,
    *,
    scanner: FileScanner | None = None,
    options: ScanOptions | None = None,
    control: ProcessControl | None = None,
    progress: ProgressCallback | None = None,
    batch_size: int = 200,
    run_kind: str = "search",
) -> SearchPipelineResult:
    """Führt den gemeinsamen Suchablauf für GUI und Konsole aus."""

    job_id = 0
    run_id = 0
    hit_count = 0
    hit_buffer: list[SearchHit] = []
    inventory_buffer: list[FileRecord] = []
    batch_size = max(25, int(batch_size))

    try:
        job.status = JobStatus.RUNNING
        job_id = database.create_search_job(job)
        run_id = database.create_scan_run(run_kind, job.root)

        def record_issue(issue: ScanIssue) -> None:
            database.record_scan_issue(run_id, issue)

        active_scanner = scanner or FileScanner(
            options=options or ScanOptions(),
            control=control,
            progress=progress,
        )

        with active_scanner.temporary_error_handler(record_issue):
            for record in active_scanner.iter_text_files(job.root):
                inventory_buffer.append(record)
                if len(inventory_buffer) >= 500:
                    database.append_scan_inventory(run_id, inventory_buffer)
                    inventory_buffer.clear()
            if inventory_buffer:
                database.append_scan_inventory(run_id, inventory_buffer)
                inventory_buffer.clear()

            total_records, total_bytes = database.scan_inventory_totals(run_id)

            def store_hit(hit: SearchHit) -> None:
                nonlocal hit_count
                hit_count += 1
                hit_buffer.append(hit)
                if len(hit_buffer) >= batch_size:
                    database.append_search_hits(job_id, list(hit_buffer))
                    hit_buffer.clear()

            TextSearcher(
                active_scanner,
                progress=progress,
                on_hit=store_hit,
                collect_hits=False,
            ).search(
                job,
                records=database.iter_scan_records(run_id),
                total_records=total_records,
                total_bytes=total_bytes,
            )

        if hit_buffer:
            database.append_search_hits(job_id, hit_buffer)

        error_count = database.scan_error_count(run_id)
        job.hits = hit_count
        job.error_count = error_count
        job.status = JobStatus.DONE
        database.finish_scan_run(run_id, "fertig", job.scanned_files)
        database.finish_search_job(
            job_id,
            status=job.status.value,
            scanned_files=job.scanned_files,
            hit_count=hit_count,
            error_count=error_count,
        )
        database.prune_search_jobs()
        database.prune_scan_runs()
        return SearchPipelineResult(job_id, hit_count, error_count)

    except ProcessCancelled:
        if run_id:
            database.finish_scan_run(run_id, "abgebrochen", job.scanned_files)
        if job_id:
            if hit_buffer:
                database.append_search_hits(job_id, hit_buffer)
            database.finish_search_job(
                job_id,
                status=JobStatus.CANCELLED.value,
                scanned_files=job.scanned_files,
                hit_count=hit_count,
                error_count=database.scan_error_count(run_id) if run_id else 0,
            )
        raise
    except Exception:
        if run_id:
            database.finish_scan_run(run_id, "fehler", job.scanned_files)
        if job_id:
            database.finish_search_job(
                job_id,
                status=JobStatus.FAILED.value,
                scanned_files=job.scanned_files,
                hit_count=hit_count,
                error_count=database.scan_error_count(run_id) if run_id else 0,
            )
        raise
