from __future__ import annotations

from pathlib import Path
import logging

from PySide6.QtCore import QThread, Signal

from app.core.duplicates import scan_duplicate_groups
from app.core.search import TextSearcher
from app.models.entities import SearchJob

LOGGER = logging.getLogger(__name__)


class SearchWorker(QThread):
    completed = Signal(object, object)
    failed = Signal(str)

    def __init__(self, job: SearchJob) -> None:
        super().__init__()
        self.job = job

    def run(self) -> None:
        try:
            hits = TextSearcher().search(self.job)
            self.completed.emit(self.job, hits)
        except Exception as exc:  # GUI-Grenze
            LOGGER.exception("Hintergrundauftrag fehlgeschlagen")
            self.failed.emit(str(exc))


class DuplicateWorker(QThread):
    completed = Signal(int, object)
    failed = Signal(str)

    def __init__(self, root: Path) -> None:
        super().__init__()
        self.root = root

    def run(self) -> None:
        try:
            scanned, groups = scan_duplicate_groups(self.root)
            self.completed.emit(scanned, groups)
        except Exception as exc:  # GUI-Grenze
            LOGGER.exception("Hintergrundauftrag fehlgeschlagen")
            self.failed.emit(str(exc))
