from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.core.duplicates import scan_duplicate_groups
from app.core.scanner import FileScanner, ScanOptions
from app.core.search import TextSearcher
from app.models.entities import SearchJob
from app.process_control import ProcessCancelled, ProcessControl, ProgressInfo

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
    completed=Signal(object,object)
    failed=Signal(str)

    def __init__(self,job:SearchJob,options:ScanOptions|None=None)->None:
        super().__init__()
        self.job=job
        self.options=options or ScanOptions()

    def run(self)->None:
        try:
            scanner=FileScanner(options=self.options,control=self.control,progress=self._progress)
            hits=TextSearcher(scanner,progress=self._progress).search(self.job)
            self.completed.emit(self.job,hits)
        except ProcessCancelled as exc:
            self.cancelled.emit(str(exc))
        except Exception as exc:
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
