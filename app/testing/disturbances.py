from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path

from app.core.hashing import FileChangedError, stable_sha256
from app.core.scanner import FileScanner
from app.models.entities import FileRecord
from app.process_control import ProcessCancelled, ProcessControl
from app.testing.sandbox import TestSandbox


@dataclass(frozen=True)
class DisturbanceResult:
    file_change_ok: bool
    cancel_ok: bool
    pause_resume_ok: bool

    @property
    def ok(self) -> bool:
        return self.file_change_ok and self.cancel_ok and self.pause_resume_ok

    @property
    def detail(self) -> str:
        return (
            f"Dateiänderung {'OK' if self.file_change_ok else 'FEHLER'} · "
            f"Abbruch {'OK' if self.cancel_ok else 'FEHLER'} · "
            f"Pause/Fortsetzen {'OK' if self.pause_resume_ok else 'FEHLER'}"
        )


def _record(path: Path) -> FileRecord:
    stat = path.stat()
    return FileRecord(
        path=path,
        size=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
        device=int(getattr(stat, "st_dev", 0)),
        inode=int(getattr(stat, "st_ino", 0)),
    )


def run_disturbance_suite(
    *,
    sandbox_parent: Path | None = None,
) -> DisturbanceResult:
    with TestSandbox.create(sandbox_parent) as sandbox:
        root = sandbox.files_dir
        target = root / "wechsel.txt"
        target.write_text("alt", encoding="utf-8")
        record = _record(target)
        time.sleep(0.002)
        target.write_text("neu-und-laenger", encoding="utf-8")
        try:
            stable_sha256(record)
            file_change_ok = False
        except FileChangedError:
            file_change_ok = True

        cancel_control = ProcessControl()
        cancel_control.cancel()
        try:
            list(FileScanner(control=cancel_control).iter_files(root))
            cancel_ok = False
        except ProcessCancelled:
            cancel_ok = True

        for index in range(50):
            (root / f"pause-{index}.txt").write_text("x", encoding="utf-8")
        pause_control = ProcessControl()
        pause_control.pause()
        result: list[int] = []

        def scan() -> None:
            result.append(
                sum(1 for _ in FileScanner(control=pause_control).iter_files(root))
            )

        thread = threading.Thread(target=scan, daemon=True)
        thread.start()
        time.sleep(0.05)
        blocked_while_paused = thread.is_alive() and not result
        pause_control.resume()
        thread.join(timeout=5)
        pause_resume_ok = blocked_while_paused and not thread.is_alive() and bool(result)

        return DisturbanceResult(
            file_change_ok=file_change_ok,
            cancel_ok=cancel_ok,
            pause_resume_ok=pause_resume_ok,
        )
