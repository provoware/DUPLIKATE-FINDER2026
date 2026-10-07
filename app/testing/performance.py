from __future__ import annotations

import hashlib
import resource
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from app.core.scanner import FileScanner
from app.testing.sandbox import TestSandbox


BENCHMARK_ID = "filesystem-scan"
WORKLOAD_VERSION = "1"


@dataclass(frozen=True)
class PerformanceResult:
    benchmark_id: str
    workload_version: str
    workload_fingerprint: str
    files: int
    elapsed_seconds: float
    files_per_second: float
    peak_rss_mib: float
    ok: bool
    detail: str


def workload_fingerprint(file_count: int) -> str:
    payload = (
        f"{BENCHMARK_ID}|{WORKLOAD_VERSION}|files={int(file_count)}|"
        "content=Testdatei-{index}|buckets=min(1000,file_count//100)"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def run_performance_profile(
    *,
    file_count: int = 100_000,
    sandbox_parent: Path | None = None,
) -> PerformanceResult:
    file_count = max(1, int(file_count))
    fingerprint = workload_fingerprint(file_count)

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
        max_rss = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        peak_rss_mib = (
            max_rss / (1024 * 1024)
            if sys.platform == "darwin"
            else max_rss / 1024
        )
        ok = scanned == file_count
        return PerformanceResult(
            benchmark_id=BENCHMARK_ID,
            workload_version=WORKLOAD_VERSION,
            workload_fingerprint=fingerprint,
            files=scanned,
            elapsed_seconds=elapsed,
            files_per_second=rate,
            peak_rss_mib=peak_rss_mib,
            ok=ok,
            detail=(
                f"{scanned}/{file_count} Dateien · "
                f"{elapsed:.2f} s · {rate:.1f} Dateien/s · "
                f"RAM-Spitze {peak_rss_mib:.1f} MiB · "
                f"Arbeitslast {fingerprint}"
            ),
        )
