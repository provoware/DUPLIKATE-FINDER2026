from __future__ import annotations

import threading
import time
from dataclasses import dataclass


class ProcessCancelled(RuntimeError):
    pass


class ProcessControl:
    """Kooperative Pause-/Abbruchsteuerung für Hintergrundarbeiten."""

    def __init__(self) -> None:
        self._condition=threading.Condition()
        self._paused=False
        self._cancelled=False

    @property
    def paused(self)->bool:
        with self._condition:
            return self._paused

    @property
    def cancelled(self)->bool:
        with self._condition:
            return self._cancelled

    def pause(self)->None:
        with self._condition:
            if not self._cancelled:
                self._paused=True

    def resume(self)->None:
        with self._condition:
            self._paused=False
            self._condition.notify_all()

    def cancel(self)->None:
        with self._condition:
            self._cancelled=True
            self._paused=False
            self._condition.notify_all()

    def checkpoint(self)->None:
        with self._condition:
            while self._paused and not self._cancelled:
                self._condition.wait(timeout=0.25)
            if self._cancelled:
                raise ProcessCancelled("Vorgang wurde vom Nutzer sicher abgebrochen.")


@dataclass(frozen=True)
class ProgressInfo:
    step: str
    current: int
    total: int
    elapsed_seconds: float
    eta_seconds: float | None

    @property
    def percent(self)->int:
        if self.total <= 0:
            return 0
        return max(0,min(100,round(self.current/self.total*100)))


class ProgressTracker:
    def __init__(self,total:int,step:str)->None:
        self.total=max(0,total)
        self.step=step
        self.started=time.monotonic()

    def update(self,current:int,step:str|None=None)->ProgressInfo:
        elapsed=max(0.0,time.monotonic()-self.started)
        active_step=step or self.step
        eta=None
        if current>0 and self.total>current:
            eta=max(0.0,(elapsed/current)*(self.total-current))
        elif self.total and current>=self.total:
            eta=0.0
        return ProgressInfo(active_step,current,self.total,elapsed,eta)
