from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/".provoware-state"/"error-catalog.jsonl"

def fingerprint(area:str,message:str)->str:
    normalized=" ".join(message.casefold().split())
    return hashlib.sha256(f"{area}|{normalized}".encode()).hexdigest()[:16]

def add(area:str,message:str,solution:str,status:str)->dict:
    entry={
        "timestamp":datetime.now().astimezone().isoformat(),
        "fingerprint":fingerprint(area,message),
        "area":area,"message":message,"solution":solution,"status":status,
    }
    CATALOG.parent.mkdir(parents=True,exist_ok=True)
    with CATALOG.open("a",encoding="utf-8") as f:
        f.write(json.dumps(entry,ensure_ascii=False)+"\n")
    return entry

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--area",required=True)
    p.add_argument("--message",required=True)
    p.add_argument("--solution",required=True)
    p.add_argument("--status",choices=["new","known","resolved"],default="new")
    a=p.parse_args()
    print(json.dumps(add(a.area,a.message,a.solution,a.status),ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
