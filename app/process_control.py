from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass


class ProcessCancelled(RuntimeError):
    pass


class ProcessControl:
    """Kooperative Pause-/Abbruchsteuerung für Hintergrundarbeiten."""

    def __init__(self) -> None:
        self._condition=threading.Condition()
        self._paused=False
        self._cancelled=False
        self._pause_started:float|None=None
        self._paused_total=0.0

    @property
    def paused(self)->bool:
        with self._condition:
            return self._paused

    @property
    def cancelled(self)->bool:
        with self._condition:
            return self._cancelled

    @property
    def paused_seconds(self)->float:
        with self._condition:
            current=self._paused_total
            if self._paused and self._pause_started is not None:
                current += max(0.0,time.monotonic()-self._pause_started)
            return current

    def pause(self)->None:
        with self._condition:
            if not self._cancelled and not self._paused:
                self._paused=True
                self._pause_started=time.monotonic()

    def resume(self)->None:
        with self._condition:
            if self._paused and self._pause_started is not None:
                self._paused_total += max(0.0,time.monotonic()-self._pause_started)
            self._pause_started=None
            self._paused=False
            self._condition.notify_all()

    def cancel(self)->None:
        with self._condition:
            if self._paused and self._pause_started is not None:
                self._paused_total += max(0.0,time.monotonic()-self._pause_started)
            self._pause_started=None
            self._cancelled=True
            self._paused=False
            self._condition.notify_all()

    def checkpoint(self)->None:
        with self._condition:
            while self._paused and not self._cancelled:
                self._condition.wait(timeout=0.20)
            if self._cancelled:
                raise ProcessCancelled("Vorgang wurde vom Nutzer sicher abgebrochen.")


@dataclass(frozen=True)
class ProgressInfo:
    step:str
    current:int
    total:int
    elapsed_seconds:float
    eta_seconds:float|None
    processed_bytes:int=0

    @property
    def percent(self)->int:
        if self.total<=0:
            return 0
        return max(0,min(100,round(self.current/self.total*100)))

    @property
    def items_per_second(self)->float:
        return self.current/self.elapsed_seconds if self.current>0 and self.elapsed_seconds>0 else 0.0

    @property
    def bytes_per_second(self)->float:
        return self.processed_bytes/self.elapsed_seconds if self.processed_bytes>0 and self.elapsed_seconds>0 else 0.0


class ProgressTracker:
    def __init__(
        self,
        total:int,
        step:str,
        paused_seconds:Callable[[],float]|None=None,
        total_bytes:int=0,
    )->None:
        self.total=max(0,total)
        self.total_bytes=max(0,int(total_bytes))
        self.step=step
        self.started=time.monotonic()
        self._paused_seconds=paused_seconds or (lambda:0.0)

    def update(self,current:int,step:str|None=None,processed_bytes:int=0)->ProgressInfo:
        elapsed=max(0.0,time.monotonic()-self.started-self._paused_seconds())
        active_step=step or self.step
        eta=None
        if (
            processed_bytes>0
            and self.total_bytes>processed_bytes
            and elapsed>0
        ):
            bytes_per_second=processed_bytes/elapsed
            eta=max(0.0,(self.total_bytes-processed_bytes)/bytes_per_second)
        elif current>0 and self.total>current:
            eta=max(0.0,(elapsed/current)*(self.total-current))
        elif self.total and current>=self.total:
            eta=0.0
        return ProgressInfo(active_step,current,self.total,elapsed,eta,max(0,int(processed_bytes)))
