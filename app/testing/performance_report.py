from __future__ import annotations

import html
import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from app.storage.atomic_io import atomic_write_text
from app.testing.performance import PerformanceResult


REPORT_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class PerformanceComparison:
    baseline_version: str
    rate_change_percent: float | None
    elapsed_change_percent: float | None
    peak_rss_change_mib: float | None


@dataclass(frozen=True)
class PerformanceSnapshot:
    schema_version: str
    project_version: str
    created_at: str
    python: str
    platform: str
    files: int
    elapsed_seconds: float
    files_per_second: float
    peak_rss_mib: float
    comparison: PerformanceComparison | None = None


def _project_version() -> str:
    try:
        return version("provoware-duplicate-finder-2026")
    except PackageNotFoundError:
        return "unbekannt"


def _percent_change(current: float, baseline: float) -> float | None:
    if baseline == 0:
        return None
    return ((current - baseline) / baseline) * 100.0


def load_snapshot(path: Path) -> PerformanceSnapshot:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise ValueError("Nicht unterstützte Leistungsbericht-Version.")
    comparison = raw.get("comparison")
    return PerformanceSnapshot(
        schema_version=str(raw["schema_version"]),
        project_version=str(raw["project_version"]),
        created_at=str(raw["created_at"]),
        python=str(raw["python"]),
        platform=str(raw["platform"]),
        files=int(raw["files"]),
        elapsed_seconds=float(raw["elapsed_seconds"]),
        files_per_second=float(raw["files_per_second"]),
        peak_rss_mib=float(raw["peak_rss_mib"]),
        comparison=(
            PerformanceComparison(
                baseline_version=str(comparison["baseline_version"]),
                rate_change_percent=(
                    None
                    if comparison.get("rate_change_percent") is None
                    else float(comparison["rate_change_percent"])
                ),
                elapsed_change_percent=(
                    None
                    if comparison.get("elapsed_change_percent") is None
                    else float(comparison["elapsed_change_percent"])
                ),
                peak_rss_change_mib=(
                    None
                    if comparison.get("peak_rss_change_mib") is None
                    else float(comparison["peak_rss_change_mib"])
                ),
            )
            if isinstance(comparison, dict)
            else None
        ),
    )


def snapshot_from_result(
    result: PerformanceResult,
    *,
    baseline: PerformanceSnapshot | None = None,
) -> PerformanceSnapshot:
    comparison = None
    if baseline is not None:
        comparison = PerformanceComparison(
            baseline_version=baseline.project_version,
            rate_change_percent=_percent_change(
                result.files_per_second,
                baseline.files_per_second,
            ),
            elapsed_change_percent=_percent_change(
                result.elapsed_seconds,
                baseline.elapsed_seconds,
            ),
            peak_rss_change_mib=result.peak_rss_mib - baseline.peak_rss_mib,
        )

    return PerformanceSnapshot(
        schema_version=REPORT_SCHEMA_VERSION,
        project_version=_project_version(),
        created_at=datetime.now().astimezone().isoformat(),
        python=platform.python_version(),
        platform=platform.platform(),
        files=result.files,
        elapsed_seconds=result.elapsed_seconds,
        files_per_second=result.files_per_second,
        peak_rss_mib=result.peak_rss_mib,
        comparison=comparison,
    )


def _unique_target(report_dir: Path, suffix: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = report_dir / f"testlab-performance-{stamp}.{suffix}"
    if not base.exists():
        return base
    index = 2
    while True:
        candidate = report_dir / f"testlab-performance-{stamp}-{index}.{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _format_percent(value: float | None) -> str:
    return "–" if value is None else f"{value:+.1f} %"


def _html(snapshot: PerformanceSnapshot) -> str:
    comparison = snapshot.comparison
    comparison_html = "<p>Keine Vergleichsbasis angegeben.</p>"
    if comparison is not None:
        comparison_html = f"""
        <table>
          <tr><th>Vergleich</th><th>Änderung</th></tr>
          <tr><td>Dateien/s</td><td>{html.escape(_format_percent(comparison.rate_change_percent))}</td></tr>
          <tr><td>Zeit</td><td>{html.escape(_format_percent(comparison.elapsed_change_percent))}</td></tr>
          <tr><td>RAM-Spitze</td><td>{comparison.peak_rss_change_mib:+.1f} MiB</td></tr>
        </table>
        <p>Basisversion: {html.escape(comparison.baseline_version)}</p>
        """

    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>PROVOWARE Leistungsbericht</title>
<style>
body {{ font-family: sans-serif; max-width: 900px; margin: 2rem auto; line-height: 1.5; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #777; padding: .55rem; text-align: left; }}
th {{ background: #eee; color: #111; }}
code {{ background: #eee; color: #111; padding: .1rem .3rem; }}
</style>
</head>
<body>
<h1>PROVOWARE Leistungs-/Regressionsbericht</h1>
<table>
<tr><th>Version</th><td>{html.escape(snapshot.project_version)}</td></tr>
<tr><th>Zeitpunkt</th><td>{html.escape(snapshot.created_at)}</td></tr>
<tr><th>Dateien</th><td>{snapshot.files}</td></tr>
<tr><th>Dauer</th><td>{snapshot.elapsed_seconds:.3f} s</td></tr>
<tr><th>Geschwindigkeit</th><td>{snapshot.files_per_second:.1f} Dateien/s</td></tr>
<tr><th>RAM-Spitze</th><td>{snapshot.peak_rss_mib:.1f} MiB</td></tr>
<tr><th>Python</th><td>{html.escape(snapshot.python)}</td></tr>
<tr><th>System</th><td>{html.escape(snapshot.platform)}</td></tr>
</table>
<h2>Vergleich</h2>
{comparison_html}
<p>Hinweis: Die RAM-Spitze ist der maximale Resident-Set-Wert des laufenden Testprozesses.</p>
</body>
</html>
"""


def write_performance_report(
    result: PerformanceResult,
    report_dir: Path,
    *,
    baseline_path: Path | None = None,
) -> tuple[Path, Path, PerformanceSnapshot]:
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    baseline = load_snapshot(baseline_path) if baseline_path is not None else None
    snapshot = snapshot_from_result(result, baseline=baseline)

    json_path = _unique_target(report_dir, "json")
    html_path = json_path.with_suffix(".html")
    atomic_write_text(
        json_path,
        json.dumps(asdict(snapshot), ensure_ascii=False, indent=2) + "\n",
    )
    atomic_write_text(html_path, _html(snapshot))
    return json_path, html_path, snapshot
