from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class CheckpointRecorder:
    def __init__(self,path:Path)->None:
        self.path=path
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def add(self,checkpoint_id:str,status:str,message:str)->dict:
        if status not in {"green","yellow","red"}:
            raise ValueError("Ungültiger Ampelstatus")
        entry={
            "timestamp":datetime.now().astimezone().isoformat(),
            "id":checkpoint_id,
            "status":status,
            "message":message,
        }
        with self.path.open("a",encoding="utf-8") as handle:
            handle.write(json.dumps(entry,ensure_ascii=False)+"\n")
        return entry
