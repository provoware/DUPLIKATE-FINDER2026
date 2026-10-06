from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

REQUIRED={
    "manifest/project.manifest.json":["schema_version","project","runtime","workspace","safety","quality","state","texts","agents"],
    "manifest/agents.manifest.json":["schema_version","single_writer","agents"],
    "standards/global-standard.json":["standard_version","language","ui","development","network","errors","logging"],
    "resources/texts/manifest.json":["schema_version","active_locale","catalogs"],
}

def main()->int:
    failures=[]
    for rel,keys in REQUIRED.items():
        path=ROOT/rel
        try: data=json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"{rel}: nicht lesbar: {exc}")
            continue
        for key in keys:
            if key not in data: failures.append(f"{rel}: Feld fehlt: {key}")
    agents=json.loads((ROOT/"manifest/agents.manifest.json").read_text(encoding="utf-8"))
    writers=[a["id"] for a in agents["agents"] if a.get("mode")=="write"]
    if writers != [agents["single_writer"]]:
        failures.append(f"Agentenvertrag: genau ein Schreibagent erwartet, gefunden: {writers}")
    project=json.loads((ROOT/"manifest/project.manifest.json").read_text(encoding="utf-8"))
    if project["runtime"].get("tkinter_allowed") is not False:
        failures.append("Tk/Tkinter muss im Manifest verboten sein.")
    for item in failures: print("FEHLER |",item)
    if failures: return 1
    print("OK | Manifeste und globale Verträge konsistent")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
