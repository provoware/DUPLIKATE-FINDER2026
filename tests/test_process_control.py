from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from app.core.scanner import FileScanner, ScanOptions
from app.process_control import ProcessCancelled, ProcessControl, ProgressTracker


def test_scanner_excludes_python_project_dirs_by_default(tmp_path:Path):
    (tmp_path/"normal").mkdir()
    (tmp_path/"normal"/"a.txt").write_text("a",encoding="utf-8")
    (tmp_path/".venv").mkdir()
    (tmp_path/".venv"/"secret.txt").write_text("b",encoding="utf-8")
    paths=[r.path for r in FileScanner().iter_files(tmp_path)]
    assert tmp_path/"normal"/"a.txt" in paths
    assert tmp_path/".venv"/"secret.txt" not in paths


def test_scanner_excludes_selected_extensions(tmp_path:Path):
    (tmp_path/"a.txt").write_text("a",encoding="utf-8")
    (tmp_path/"b.log").write_text("b",encoding="utf-8")
    options=ScanOptions(excluded_extensions=frozenset({"log"}))
    paths=[r.path for r in FileScanner(options=options).iter_files(tmp_path)]
    assert tmp_path/"a.txt" in paths
    assert tmp_path/"b.log" not in paths


def test_process_control_cancel_is_safe():
    control=ProcessControl()
    control.cancel()
    with pytest.raises(ProcessCancelled):
        control.checkpoint()


def test_process_control_pause_and_resume():
    control=ProcessControl()
    control.pause()
    passed=[]
    def target():
        control.checkpoint()
        passed.append(True)
    thread=threading.Thread(target=target)
    thread.start()
    time.sleep(0.05)
    assert not passed
    control.resume()
    thread.join(timeout=1)
    assert passed==[True]


def test_progress_tracker_estimates_remaining_time():
    tracker=ProgressTracker(10,"Test")
    tracker.started-=9
    info=tracker.update(5)
    assert info.percent==50
    assert info.eta_seconds is not None
    assert info.eta_seconds>0


def test_pause_time_is_not_counted_in_eta():
    control=ProcessControl()
    tracker=ProgressTracker(10,"Test",lambda:control.paused_seconds)
    tracker.started-=10
    control._paused_total=5
    info=tracker.update(5)
    assert info.eta_seconds is not None
    assert 4 <= info.eta_seconds <= 7


def test_scanner_reports_inventory_phase(tmp_path:Path):
    for i in range(30):
        (tmp_path/f"{i}.txt").write_text("x",encoding="utf-8")
    events=[]
    scanner=FileScanner(progress=events.append)
    list(scanner.iter_files(tmp_path))
    assert any(event.total == 0 and "erfassen" in event.step for event in events)
    assert any("Dateiliste fertig" in event.step for event in events)


def test_progress_tracker_prefers_byte_weighted_eta_for_mixed_file_sizes():
    tracker=ProgressTracker(10,"Test",total_bytes=1_000)
    tracker.started-=10
    info=tracker.update(1,processed_bytes=500)
    assert info.eta_seconds is not None
    assert 8 <= info.eta_seconds <= 12
