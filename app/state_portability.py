from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.storage.database import Database


FORMAT_VERSION="1.0.0"


def export_state(database:Database,path:Path,settings:dict)->dict:
    payload={
        "format":"PROVOWARE-DUPLIKATE-FINDER-STATE",
        "version":FORMAT_VERSION,
        "exported_at":datetime.now().astimezone().isoformat(),
        "settings":settings,
        "virtual_state":database.export_virtual_state(),
    }
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    tmp.replace(path)
    return payload


def validate_import_payload(payload:object)->dict:
    if not isinstance(payload,dict):
        raise ValueError("Die Importdatei enthält kein gültiges PROVOWARE-Objekt.")
    if payload.get("format")!="PROVOWARE-DUPLIKATE-FINDER-STATE":
        raise ValueError("Die Datei ist kein unterstützter PROVOWARE-Export.")
    state=payload.get("virtual_state")
    if not isinstance(state,dict):
        raise ValueError("Der virtuelle Datenbereich fehlt.")
    if not isinstance(state.get("collections",[]),list):
        raise ValueError("Sammlungen sind ungültig.")
    if not isinstance(state.get("virtual_items",[]),list):
        raise ValueError("Virtuelle Markierungen sind ungültig.")
    return payload


def import_state(database:Database,path:Path)->dict:
    try:
        payload=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        raise ValueError(f"Importdatei konnte nicht gelesen werden: {exc}") from exc
    valid=validate_import_payload(payload)
    database.import_virtual_state(valid["virtual_state"])
    return valid
