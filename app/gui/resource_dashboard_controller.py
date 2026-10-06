from __future__ import annotations

from typing import Any

from app.formatting import format_bytes
from app.resource_monitor import ResourceMonitor


class ResourceDashboardController:
    """Aktualisiert ausschließlich die Ressourcenanzeige im Dashboard."""

    def __init__(self, window: Any, monitor: ResourceMonitor | None = None) -> None:
        self.window = window
        self.monitor = monitor or ResourceMonitor()

    def refresh(self) -> None:
        snapshot = self.monitor.sample()
        ram = format_bytes(snapshot.process_ram_bytes)
        swap_used = format_bytes(snapshot.swap_used_bytes)
        swap_total = format_bytes(snapshot.swap_total_bytes)
        swap_percent = (
            snapshot.swap_used_bytes / snapshot.swap_total_bytes * 100
            if snapshot.swap_total_bytes > 0
            else 0.0
        )
        self.window.dashboard_resource_value.setText(
            f"CPU {snapshot.process_cpu_percent:.0f}% · RAM {ram} · "
            f"SWAP {swap_percent:.0f}%"
        )
        sys_used = format_bytes(snapshot.system_ram_used_bytes)
        sys_total = format_bytes(snapshot.system_ram_total_bytes)
        self.window.dashboard_resource_value.setToolTip(
            f"PROVOWARE CPU: {snapshot.process_cpu_percent:.1f} %\n"
            f"PROVOWARE RAM: {ram}\n"
            f"System-RAM: {sys_used} von {sys_total}\n"
            f"SWAP (Auslagerung): {swap_used} von {swap_total}"
        )
