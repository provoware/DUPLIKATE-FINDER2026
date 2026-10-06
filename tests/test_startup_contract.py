from pathlib import Path

from app.startup.bootstrap import bootstrap
from app.startup.selftest import run_selftest


def test_console_startup_does_not_require_pyside(tmp_path: Path):
    checks = run_selftest(tmp_path, require_gui=False)
    assert all(check.ok for check in checks)


def test_bootstrap_creates_only_internal_work_folders(tmp_path: Path):
    checks = bootstrap(tmp_path, require_gui=False)
    assert all(check.ok for check in checks)
    for name in ("data", "logs", "recovery", "quarantine"):
        assert (tmp_path / name).is_dir()
