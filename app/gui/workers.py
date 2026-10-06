from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.core.duplicates import scan_duplicate_groups_to_database
from app.core.scanner import FileScanner, ScanOptions
from app.models.entities import SearchJob
from app.process_control import ProcessCancelled, ProcessControl, ProgressInfo
from app.storage.database import Database
from app.core.search_pipeline import run_search_to_database

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
        try:
            scanner = FileScanner(
                options=self.options,
                control=self.control,
                progress=self._progress,
            )
            result = run_search_to_database(
                self.job,
                self.database,
                scanner=scanner,
                progress=self._progress,
                batch_size=self.batch_size,
                run_kind="search",
            )
            self.completed.emit(
                self.job,
                result.job_id,
                result.hit_count,
                result.error_count,
            )
        except ProcessCancelled as exc:
            self.cancelled.emit(str(exc))
        except Exception as exc:
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
