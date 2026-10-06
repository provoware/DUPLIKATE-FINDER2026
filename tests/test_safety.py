from pathlib import Path

import pytest

from app.safety.policy import SafetyPolicy, SafetyViolation


def test_system_directories_are_blocked():
    with pytest.raises(SafetyViolation):
        SafetyPolicy().ensure_scan_root_allowed(Path("/etc"))


def test_root_is_blocked():
    with pytest.raises(SafetyViolation):
        SafetyPolicy().ensure_scan_root_allowed(Path("/"))


def test_write_actions_are_blocked():
    policy = SafetyPolicy(read_only=True)
    for action in ("move_files", "rename_files", "quarantine", "delete_files"):
        with pytest.raises(SafetyViolation):
            policy.ensure_write_action_allowed(action)


def test_run_media_user_mount_is_allowed():
    allowed = SafetyPolicy().ensure_scan_root_allowed(Path("/run/media/testuser/teststick"))
    assert allowed == Path("/run/media/testuser/teststick")


def test_run_itself_remains_blocked():
    with pytest.raises(SafetyViolation):
        SafetyPolicy().ensure_scan_root_allowed(Path("/run"))
