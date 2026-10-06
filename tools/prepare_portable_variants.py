from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


LITE_REMOVE = (
    "wheelhouse",
    "agents",
    "standards",
    "schemas",
    "templates",
)

LITE_DOCS_KEEP = {
    "LAIENANLEITUNG.md",
    "PORTABLE_RELEASE.md",
    "SICHERHEITSVERTRAG.md",
}


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def write_profile(root: Path, profile: str, offline_repair: bool) -> None:
    payload = {
        "schema_version": "1.0.0",
        "profile": profile,
        "portable": True,
        "offline_gui_repair": offline_repair,
        "runtime_pruned": False,
        "note": (
            "Recovery enthält den lokalen PySide6-Reparaturvorrat."
            if offline_repair
            else "Lite enthält die vollständige geprüfte Laufzeit, aber keinen doppelten Reparaturvorrat."
        ),
    }
    (root / "PAKET-PROFIL.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def make_lite(recovery: Path, lite: Path) -> None:
    if lite.exists():
        shutil.rmtree(lite)
    shutil.copytree(recovery, lite, symlinks=True)

    for relative in LITE_REMOVE:
        remove_path(lite / relative)

    docs = lite / "docs"
    if docs.is_dir():
        for item in docs.iterdir():
            if item.name not in LITE_DOCS_KEEP:
                remove_path(item)

    write_profile(lite, "lite", offline_repair=False)


def finalize_lite(lite: Path) -> None:
    # Prüfwerkzeuge werden nur für die E2E-Abnahme benötigt und gehören
    # nicht in das Endnutzerpaket.
    remove_path(lite / "tools")
    for pattern in ("__pycache__",):
        for path in lite.rglob(pattern):
            remove_path(path)
    for pattern in ("*.pyc", "*.pyo"):
        for path in lite.rglob(pattern):
            remove_path(path)


def directory_size(root: Path) -> int:
    total = 0
    for path in root.rglob("*"):
        try:
            if path.is_file() and not path.is_symlink():
                total += path.stat().st_size
        except OSError:
            pass
    return total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recovery", type=Path, required=True)
    parser.add_argument("--lite", type=Path, required=True)
    parser.add_argument("--finalize-lite", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    if not args.recovery.is_dir():
        raise SystemExit(f"Recovery-Verzeichnis fehlt: {args.recovery}")

    if not args.lite.exists():
        write_profile(args.recovery, "recovery", offline_repair=True)
        make_lite(args.recovery, args.lite)

    if args.finalize_lite:
        finalize_lite(args.lite)

    if args.report:
        recovery_bytes = directory_size(args.recovery)
        lite_bytes = directory_size(args.lite)
        reduction = 0.0 if recovery_bytes == 0 else (1 - lite_bytes / recovery_bytes) * 100
        payload = {
            "recovery_bytes": recovery_bytes,
            "lite_bytes": lite_bytes,
            "saved_bytes": max(0, recovery_bytes - lite_bytes),
            "reduction_percent": round(reduction, 2),
            "lite_removed": list(LITE_REMOVE),
            "lite_docs_kept": sorted(LITE_DOCS_KEEP),
            "runtime_pruned": False,
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
