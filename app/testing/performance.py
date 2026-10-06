from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from app.core.scanner import FileScanner
from app.testing.sandbox import TestSandbox


@dataclass(frozen=True)
class PerformanceResult:
    files: int
    elapsed_seconds: float
    files_per_second: float
    ok: bool
    detail: str


def run_performance_profile(
    *,
    file_count: int = 100_000,
    sandbox_parent: Path | None = None,
) -> PerformanceResult:
    file_count = max(1, int(file_count))
    with TestSandbox.create(sandbox_parent) as sandbox:
        root = sandbox.files_dir
        buckets = max(1, min(1000, file_count // 100 or 1))
        for index in range(file_count):
            folder = root / f"d{index % buckets:04d}"
            folder.mkdir(exist_ok=True)
            (folder / f"f{index:07d}.txt").write_text(
                f"Testdatei {index}\n",
                encoding="utf-8",
            )

        started = time.perf_counter()
        scanned = sum(1 for _ in FileScanner().iter_files(root))
        elapsed = max(0.000001, time.perf_counter() - started)
        rate = scanned / elapsed
        ok = scanned == file_count
        return PerformanceResult(
            files=scanned,
            elapsed_seconds=elapsed,
            files_per_second=rate,
            ok=ok,
            detail=(
                f"{scanned}/{file_count} Dateien · "
                f"{elapsed:.2f} s · {rate:.1f} Dateien/s"
            ),
        )
