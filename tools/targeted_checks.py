from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run(command:list[str],env:dict[str,str]|None=None)->None:
    print("▶"," ".join(command))
    completed=subprocess.run(command,cwd=ROOT,env=env)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def plan(base:str|None)->dict:
    output=ROOT/"artifacts"/"pruefplan.json"
    command=[sys.executable,"tools/state_registry.py","--output",str(output)]
    if base:
        command += ["--base",base]
    run(command)
    return json.loads(output.read_text(encoding="utf-8"))


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--full",action="store_true")
    args=parser.parse_args()

    run([sys.executable,"tools/validate_manifests.py"])
    current=plan(args.base)
    checks=set(current["checks"])
    changed=current["changed_files"]
    print("Betroffene Bereiche:",", ".join(current["areas"]) or "keine")
    print("Geplante Prüfungen:",", ".join(current["checks"]))

    if args.full:
        run([sys.executable,"-m","compileall","-q","app","tests","tools"])
        run([sys.executable,"-m","pytest"])
        env=os.environ.copy(); env.setdefault("QT_QPA_PLATFORM","offscreen")
        for zoom in (100,150,200):
            run([sys.executable,"tools/ui_scale_check.py","--zoom",str(zoom),"--output",f"artifacts/ui-{zoom}.png"],env)
        run([sys.executable,"tools/autonomous_acceptance.py","--output","artifacts/abnahme"],env)
    else:
        test_files={"tests/test_governance.py","tests/test_architecture_guards.py"}
        areas=set(current["areas"])
        if "startup" in areas:
            test_files |= {"tests/test_startup_contract.py","tests/test_workspace.py"}
        if "core" in areas:
            test_files |= {"tests/test_search.py","tests/test_duplicates.py","tests/test_scanner.py","tests/test_safety.py","tests/test_database.py"}
        if "gui" in areas:
            env=os.environ.copy(); env.setdefault("QT_QPA_PLATFORM","offscreen")
            run([sys.executable,"tools/ui_scale_check.py","--zoom","100","--output","artifacts/ui-schnelltest.png"],env)
        if test_files:
            run([sys.executable,"-m","pytest",*sorted(test_files)])
        if not changed:
            print("🟢 Kein Quellzustand geändert – keine redundanten Fachtests nötig.")

    run([sys.executable,"tools/state_registry.py","--record"])
    print("🟢 Prüfzustand erfolgreich registriert.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
