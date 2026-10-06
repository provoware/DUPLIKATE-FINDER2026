from pathlib import Path

import pytest

from app.testing import (
    available_profiles,
    run_disturbance_suite,
    run_performance_profile,
    run_profile,
)
from app.testing.sandbox import MARKER, TestSandbox


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


def test_disturbance_suite_detects_change_cancel_and_pause():
    result = run_disturbance_suite()
    assert result.ok, result.detail
