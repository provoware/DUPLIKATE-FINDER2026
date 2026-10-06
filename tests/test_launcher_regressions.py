from __future__ import annotations

import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_development_progress_bar_runs_under_strict_bash():
    completed=subprocess.run(
        ["bash",str(ROOT/"ENTWICKLUNG_STARTEN.sh"),"--fortschrittstest"],
        cwd=ROOT,capture_output=True,text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "100%" in completed.stdout


def test_start_scripts_have_valid_bash_syntax():
    for name in ("ENTWICKLUNG_STARTEN.sh","STARTEN.sh","STARTEN_KONSOLE.sh"):
        completed=subprocess.run(["bash","-n",str(ROOT/name)],capture_output=True,text=True)
        assert completed.returncode == 0, f"{name}: {completed.stderr}"
