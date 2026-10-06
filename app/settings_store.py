from __future__ import annotations

import json
from pathlib import Path


DEFAULT_SETTINGS = {
    "schema_version":"1.0.0",
    "zoom_percent":100,
    "window_width":1280,
    "window_height":800,
    "cpu_cores":0,
    "exclude_python_project_dirs":True,
    "excluded_extensions":[],
}


class SettingsStore:
    def __init__(self,path:Path)->None:
        self.path=path

    def load(self)->dict:
        data=dict(DEFAULT_SETTINGS)
        try:
            raw=json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw,dict):
                for key in data:
                    if key in raw:
                        data[key]=raw[key]
        except (OSError,json.JSONDecodeError):
            pass
        return data

    def save(self,data:dict)->None:
        self.path.parent.mkdir(parents=True,exist_ok=True)
        clean=dict(DEFAULT_SETTINGS)
        clean.update({key:data[key] for key in clean if key in data})
        self.path.write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding="utf-8")
