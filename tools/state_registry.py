from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

EXCLUDED_PARTS = {
    ".git", ".venv", ".provoware-dev", ".provoware-state", "__pycache__",
    ".pytest_cache", "artifacts", "runtime", "release", "out",
}
EXCLUDED_ROOT_DIRS = {"data", "logs", "recovery", "quarantine"}
AREA_RULES = (
    ("startup", ("STARTEN", "ENTWICKLUNG_STARTEN.sh", "dependencies.env", "app/startup/", "app/main.py", "app/workspace.py")),
    ("gui", ("app/gui/", "app/file_browser/widget.py", "resources/texts/", "standards/")),
    ("core", ("app/core/", "app/file_browser/classification.py", "app/file_browser/preview.py", "app/models/", "app/storage/", "app/safety/", "app/validation.py")),
    ("tests", ("tests/", "tools/autonomous_acceptance.py", "tools/ui_scale_check.py")),
    ("automation", (".github/workflows/", "agents/", "manifest/agents")),
    ("manifests", ("manifest/", "schemas/", "config/", "templates/")),
    ("docs", ("docs/", "README.md", "AGENTS.md", "CHANGELOG.md")),
)

def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]

def relevant(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if not path.is_file():
        return False
    if rel.parts and rel.parts[0] in EXCLUDED_ROOT_DIRS:
        return False
    return not any(part in EXCLUDED_PARTS for part in rel.parts)

def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def area_for(rel: str) -> set[str]:
    areas=set()
    for area,prefixes in AREA_RULES:
        if any(rel == p or rel.startswith(p) for p in prefixes):
            areas.add(area)
    return areas or {"other"}

def snapshot(root: Path) -> dict:
    files={}
    areas=set()
    for path in sorted(root.rglob("*")):
        if not relevant(path, root):
            continue
        rel=path.relative_to(root).as_posix()
        files[rel]={"sha256":digest(path),"size":path.stat().st_size}
        areas.update(area_for(rel))
    aggregate=hashlib.sha256(
        "\n".join(f"{name}:{meta['sha256']}" for name,meta in sorted(files.items())).encode()
    ).hexdigest()
    return {
        "schema_version":"1.0.0",
        "timestamp":datetime.now().astimezone().isoformat(),
        "aggregate_sha256":aggregate,
        "files":files,
        "areas":sorted(areas),
    }

def changed_files(old: dict, new: dict) -> list[str]:
    old_files=old.get("files",{})
    new_files=new.get("files",{})
    names=set(old_files)|set(new_files)
    return sorted(name for name in names if old_files.get(name)!=new_files.get(name))

def recommended_checks(changed: list[str]) -> list[str]:
    areas=set()
    for name in changed:
        areas.update(area_for(name))
    checks=["manifest"]
    if areas & {"core","startup","manifests","automation"}:
        checks += ["compile","unit","safety"]
    if "gui" in areas:
        checks += ["ui-100","ui-150","ui-200"]
    if "startup" in areas:
        checks += ["startup","console"]
    if areas & {"core","gui","startup","tests","manifests"}:
        checks += ["acceptance"]
    if areas <= {"docs"}:
        checks += ["docs"]
    return list(dict.fromkeys(checks))

def git_changed(root: Path, base: str | None) -> list[str]:
    if not base:
        return []
    proc=subprocess.run(["git","diff","--name-only",f"{base}...HEAD"],cwd=root,capture_output=True,text=True)
    return sorted({line.strip() for line in proc.stdout.splitlines() if line.strip()}) if proc.returncode==0 else []

def quick_signature(root: Path, changed: list[str]) -> str:
    h=hashlib.sha256()
    for name in sorted(changed):
        path=root/name
        h.update(name.encode())
        if path.is_file():
            h.update(digest(path).encode())
        else:
            h.update(b"<deleted>")
    return h.hexdigest()


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--record",action="store_true")
    parser.add_argument("--base")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    root=root_dir()
    state_path=root/".provoware-state"/"development-state.json"
    old={}
    if state_path.exists():
        try: old=json.loads(state_path.read_text(encoding="utf-8"))
        except Exception: old={}

    git_changes=git_changed(root,args.base)
    if args.base and not args.record:
        changed=git_changes
        aggregate=quick_signature(root,changed)
        timestamp=datetime.now().astimezone().isoformat()
        unchanged=not changed
        new=None
    else:
        new=snapshot(root)
        changed=git_changes or changed_files(old,new)
        aggregate=new["aggregate_sha256"]
        timestamp=new["timestamp"]
        unchanged=bool(old) and old.get("aggregate_sha256")==aggregate

    plan={
        "timestamp":timestamp,
        "unchanged":unchanged,
        "changed_files":changed,
        "areas":sorted({a for name in changed for a in area_for(name)}),
        "checks":recommended_checks(changed),
        "aggregate_sha256":aggregate,
    }
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(plan,ensure_ascii=False,indent=2))
    if args.record:
        assert new is not None
        state_path.parent.mkdir(parents=True,exist_ok=True)
        state_path.write_text(json.dumps(new,ensure_ascii=False,indent=2),encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
