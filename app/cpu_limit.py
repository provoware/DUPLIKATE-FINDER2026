from __future__ import annotations

import os


class CpuLimiter:
    """Begrenzt nur den laufenden PROVOWARE-Prozess, niemals das System."""

    def __init__(self)->None:
        try:
            self.original=tuple(sorted(os.sched_getaffinity(0)))
        except (AttributeError,OSError):
            self.original=tuple(range(os.cpu_count() or 1))

    @property
    def available(self)->int:
        return max(1,len(self.original))

    def apply(self,cores:int)->int:
        requested=self.available if cores<=0 else max(1,min(int(cores),self.available))
        selected=set(self.original[:requested])
        if hasattr(os,"sched_setaffinity"):
            task_root="/proc/self/task"
            try:
                tids=[int(name) for name in os.listdir(task_root) if name.isdigit()]
            except OSError:
                tids=[0]
            for tid in tids:
                try:
                    os.sched_setaffinity(tid,selected)
                except (OSError,PermissionError):
                    continue
        return requested
