from __future__ import annotations

import threading
import time

from app.core.control import ProcessControl


def test_pause_blocks_checkpoint_until_resume():
    control=ProcessControl()
    control.pause()
    reached=threading.Event()

    def worker():
        control.checkpoint()
        reached.set()

    thread=threading.Thread(target=worker)
    thread.start()
    time.sleep(0.05)
    assert not reached.is_set()
    control.resume()
    thread.join(timeout=1)
    assert reached.is_set()
