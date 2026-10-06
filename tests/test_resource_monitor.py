from __future__ import annotations

from app.process_control import ProgressInfo
from app.resource_monitor import ResourceMonitor


def test_resource_monitor_returns_non_negative_values():
    monitor=ResourceMonitor()
    first=monitor.sample()
    second=monitor.sample()
    for sample in (first,second):
        assert sample.process_cpu_percent >= 0
        assert sample.process_ram_bytes >= 0
        assert sample.system_ram_used_bytes >= 0
        assert sample.system_ram_total_bytes >= 0
        assert sample.swap_used_bytes >= 0
        assert sample.swap_total_bytes >= 0


def test_progress_info_reports_speed_and_bytes_per_second():
    info=ProgressInfo(
        step="Test",
        current=10,
        total=20,
        elapsed_seconds=2.0,
        eta_seconds=2.0,
        processed_bytes=2_000,
    )
    assert info.items_per_second==5.0
    assert info.bytes_per_second==1_000.0
    assert info.percent==50
