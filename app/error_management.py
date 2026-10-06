from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


def solution_for(message:str)->str:
    lower=message.casefold()
    if "permission" in lower or "berecht" in lower:
        return "Prüfe die Schreibrechte des PROVOWARE-Projektordners und starte den Selbsttest erneut."
    if "no space" in lower or "speicher" in lower:
        return "Schaffe freien Speicherplatz und starte danach den Selbsttest erneut."
    if "not found" in lower or "nicht gefunden" in lower:
        return "Prüfe, ob die ausgewählte Datei oder der Ordner noch vorhanden ist, und wähle ihn gegebenenfalls neu."
    if "pyside" in lower or "qt" in lower:
        return "Starte die automatische Startprüfung erneut. Sie prüft die lokale PySide6/Qt-Laufzeit und den Reparaturbestand."
    return "Öffne den Protokollordner, führe den Selbsttest aus und wiederhole den letzten Schritt. Originaldateien bleiben geschützt."


def record_error(log_dir:Path,area:str,message:str,solution:str|None=None,status:str="new")->dict:
    normalized=" ".join(message.casefold().split())
    fingerprint=hashlib.sha256(f"{area}|{normalized}".encode()).hexdigest()[:16]
    entry={
        "timestamp":datetime.now().astimezone().isoformat(),
        "fingerprint":fingerprint,
        "area":area,
        "message":message,
        "solution":solution or solution_for(message),
        "status":status,
    }
    log_dir.mkdir(parents=True,exist_ok=True)
    with (log_dir/"fehlerkatalog.jsonl").open("a",encoding="utf-8") as handle:
        handle.write(json.dumps(entry,ensure_ascii=False)+"\n")
    return entry
