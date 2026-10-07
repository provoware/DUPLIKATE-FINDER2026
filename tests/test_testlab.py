from pathlib import Path

import pytest

from app.testing import (
    available_profiles,
    run_disturbance_suite,
    run_fault_injection_suite,
    run_performance_profile,
    run_profile,
    write_performance_report,
)
from app.testing.sandbox import MARKER, TestSandbox
from app.testing.performance import PerformanceResult
from app.testing.performance_report import snapshot_from_result


@pytest.mark.parametrize("profile", available_profiles())
def test_testlab_profiles_match_expected_results(profile: str):
    result = run_profile(profile)
    assert result.ok, result.detail


def test_sandbox_requires_marker_before_cleanup(tmp_path: Path):
    sandbox = TestSandbox.create(tmp_path)
    marker = sandbox.root / MARKER
    marker.unlink()
    with pytest.raises(RuntimeError, match="Test-Markierung fehlt"):
        sandbox.cleanup()


def test_small_performance_profile_counts_all_files():
    result = run_performance_profile(file_count=250)
    assert result.ok
    assert result.files == 250
    assert result.files_per_second > 0
    assert result.peak_rss_mib > 0
    assert result.benchmark_id == "filesystem-scan"
    assert result.workload_version == "1"
    assert len(result.workload_fingerprint) == 16


def test_disturbance_suite_detects_change_cancel_and_pause():
    result = run_disturbance_suite()
    assert result.ok, result.detail


def test_fault_injection_suite_handles_all_expected_failures():
    result = run_fault_injection_suite()
    assert result.ok, result.detail


def test_performance_report_writes_json_html_and_comparison(tmp_path: Path):
    first = run_performance_profile(file_count=40)
    json_path, html_path, snapshot = write_performance_report(
        first,
        tmp_path,
    )
    assert json_path.is_file()
    assert html_path.is_file()
    assert snapshot.files == 40
    assert snapshot.peak_rss_mib > 0

    second = run_performance_profile(file_count=40)
    second_json, second_html, compared = write_performance_report(
        second,
        tmp_path,
        baseline_path=json_path,
    )
    assert second_json != json_path
    assert second_html.is_file()
    assert compared.comparison is not None
    assert compared.comparison.baseline_version == snapshot.project_version
    assert compared.comparison.workload_verified is True
    assert compared.comparison.environment_matches is True


def test_performance_report_rejects_different_file_counts(tmp_path: Path):
    first = run_performance_profile(file_count=20)
    json_path, _html_path, _snapshot = write_performance_report(first, tmp_path)
    second = run_performance_profile(file_count=21)

    with pytest.raises(ValueError, match="dieselbe Dateianzahl"):
        write_performance_report(
            second,
            tmp_path,
            baseline_path=json_path,
        )


def test_performance_report_rejects_changed_workload(tmp_path: Path):
    first = run_performance_profile(file_count=20)
    json_path, _html_path, _snapshot = write_performance_report(first, tmp_path)
    raw = json_path.read_text(encoding="utf-8")
    json_path.write_text(
        raw.replace(first.workload_fingerprint, "0" * 16),
        encoding="utf-8",
    )
    second = run_performance_profile(file_count=20)

    with pytest.raises(ValueError, match="Arbeitslast"):
        write_performance_report(
            second,
            tmp_path,
            baseline_path=json_path,
        )


def test_performance_comparison_flags_clear_regression():
    baseline_result = PerformanceResult(
        benchmark_id="filesystem-scan",
        workload_version="1",
        workload_fingerprint="abc123abc123abcd",
        files=100,
        elapsed_seconds=1.0,
        files_per_second=100.0,
        peak_rss_mib=100.0,
        ok=True,
        detail="Basis",
    )
    baseline = snapshot_from_result(baseline_result)

    slower = PerformanceResult(
        benchmark_id="filesystem-scan",
        workload_version="1",
        workload_fingerprint="abc123abc123abcd",
        files=100,
        elapsed_seconds=1.25,
        files_per_second=80.0,
        peak_rss_mib=180.0,
        ok=True,
        detail="Regression",
    )
    current = snapshot_from_result(slower, baseline=baseline)

    assert current.comparison is not None
    assert current.comparison.regression_warning is True
    assert len(current.comparison.regression_reasons) == 3
