from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LOG=ROOT/".provoware-state"/"agent-runs.jsonl"


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--plan",type=Path,default=ROOT/"artifacts"/"pruefplan.json")
    parser.add_argument("--output",type=Path,default=ROOT/"artifacts"/"agentenplan.json")
    args=parser.parse_args()
    plan=json.loads(args.plan.read_text(encoding="utf-8"))
    areas=set(plan.get("areas",[]))
    agents=["analyse","testplanung"]
    if areas & {"startup","core","manifests"}:
        agents.append("sicherheit")
    agents.append("operator")
    agents.append("regression")
    if areas & {"docs","manifests","automation"}:
        agents.append("dokumentation")
    record={
        "timestamp":datetime.now().astimezone().isoformat(),
        "input_sha256":plan.get("aggregate_sha256"),
        "areas":sorted(areas),
        "agents":[{"id":agent,"mode":"write" if agent=="operator" else "read_only"} for agent in agents],
        "single_writer":"operator",
        "status":"planned",
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
    LOG.parent.mkdir(parents=True,exist_ok=True)
    with LOG.open("a",encoding="utf-8") as handle:
        handle.write(json.dumps(record,ensure_ascii=False)+"\n")
    print(json.dumps(record,ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
