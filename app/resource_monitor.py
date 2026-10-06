from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResourceSnapshot:
    process_cpu_percent:float
    process_ram_bytes:int
    system_ram_used_bytes:int
    system_ram_total_bytes:int
    swap_used_bytes:int
    swap_total_bytes:int


class ResourceMonitor:
    """Sehr leichter Linux-Monitor ohne externe Abhängigkeiten."""

    def __init__(self)->None:
        self._last_wall=time.monotonic()
        self._last_cpu=self._process_cpu_seconds()
        try:
            self._ticks=float(os.sysconf("SC_CLK_TCK"))
        except (ValueError,OSError,AttributeError):
            self._ticks=100.0

    @staticmethod
    def _read_meminfo()->dict[str,int]:
        values={}
        try:
            for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                key,raw=line.split(":",1)
                number=raw.strip().split()[0]
                values[key]=int(number)*1024
        except (OSError,ValueError,IndexError):
            pass
        return values

    def _process_cpu_seconds(self)->float:
        try:
            raw=Path("/proc/self/stat").read_text(encoding="utf-8").split()
            ticks=float(os.sysconf("SC_CLK_TCK"))
            return (float(raw[13])+float(raw[14]))/ticks
        except (OSError,ValueError,IndexError,AttributeError):
            return time.process_time()

    @staticmethod
    def _process_ram()->int:
        try:
            for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])*1024
        except (OSError,ValueError,IndexError):
            pass
        return 0

    def sample(self)->ResourceSnapshot:
        now=time.monotonic()
        cpu_now=self._process_cpu_seconds()
        wall=max(0.001,now-self._last_wall)
        cpu_percent=max(0.0,(cpu_now-self._last_cpu)/wall*100.0)
        self._last_wall=now
        self._last_cpu=cpu_now

        mem=self._read_meminfo()
        total=mem.get("MemTotal",0)
        available=mem.get("MemAvailable",mem.get("MemFree",0))
        used=max(0,total-available)
        swap_total=mem.get("SwapTotal",0)
        swap_free=mem.get("SwapFree",0)
        return ResourceSnapshot(
            process_cpu_percent=cpu_percent,
            process_ram_bytes=self._process_ram(),
            system_ram_used_bytes=used,
            system_ram_total_bytes=total,
            swap_used_bytes=max(0,swap_total-swap_free),
            swap_total_bytes=swap_total,
        )
