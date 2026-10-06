from __future__ import annotations

import logging
import time
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.core.control import ProcessCancelled, ProcessControl
from app.core.duplicates import scan_duplicate_groups
from app.core.scanner import ScanOptions
from app.core.search import TextSearcher
from app.models.entities import JobStatus, SearchJob

LOGGER = logging.getLogger(__name__)


class ManagedWorker(QThread):
    progress = Signal(int, int, str, int)
    pause_changed = Signal(bool)
    cancelled = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.control = ProcessControl()
        self._phase = ""
        self._phase_started = time.monotonic()

    def request_pause(self) -> None:
        self.control.pause()
        self.pause_changed.emit(True)

    def request_resume(self) -> None:
        self.control.resume()
        self._phase_started = time.monotonic()
        self.pause_changed.emit(False)

    def request_cancel(self) -> None:
        self.control.cancel()

    def _report(self, current: int, total: int, phase: str) -> None:
        if phase != self._phase:
            self._phase = phase
            self._phase_started = time.monotonic()
        eta = -1
        if total > 0 and current > 0 and current < total:
            elapsed = max(0.001, time.monotonic() - self._phase_started)
            eta = max(0, round((elapsed / current) * (total - current)))
        elif total > 0 and current >= total:
            eta = 0
        self.progress.emit(current, total, phase, eta)


class SearchWorker(ManagedWorker):
    completed = Signal(object, object)
    failed = Signal(str)

    def __init__(self, job: SearchJob, options: ScanOptions | None = None) -> None:
        super().__init__()
        self.job = job
        self.options = options or ScanOptions()

    def request_pause(self) -> None:
        self.job.status = JobStatus.PAUSED
        super().request_pause()

    def request_resume(self) -> None:
        self.job.status = JobStatus.RUNNING
        super().request_resume()

    def request_cancel(self) -> None:
        self.job.status = JobStatus.CANCELLED
        super().request_cancel()

    def run(self) -> None:
        try:
            hits = TextSearcher().search(
                self.job,
                options=self.options,
                control=self.control,
                progress=self._report,
            )
            self.completed.emit(self.job, hits)
        except ProcessCancelled as exc:
            self.job.status = JobStatus.CANCELLED
            self.cancelled.emit(str(exc))
        except Exception as exc:  # GUI-Grenze
            self.job.status = JobStatus.FAILED
            LOGGER.exception("Hintergrundauftrag fehlgeschlagen")
            self.failed.emit(str(exc))


class DuplicateWorker(ManagedWorker):
    completed = Signal(int, object)
    failed = Signal(str)

    def __init__(
        self,
        root: Path,
        options: ScanOptions | None = None,
        max_workers: int = 1,
    ) -> None:
        super().__init__()
        self.root = root
        self.options = options or ScanOptions()
        self.max_workers = max(1, int(max_workers))

    def run(self) -> None:
        try:
            scanned, groups = scan_duplicate_groups(
                self.root,
                options=self.options,
                control=self.control,
                progress=self._report,
                max_workers=self.max_workers,
            )
            self.completed.emit(scanned, groups)
        except ProcessCancelled as exc:
            self.cancelled.emit(str(exc))
        except Exception as exc:  # GUI-Grenze
            LOGGER.exception("Hintergrundauftrag fehlgeschlagen")
            self.failed.emit(str(exc))
