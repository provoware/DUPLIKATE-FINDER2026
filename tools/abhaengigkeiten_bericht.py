from __future__ import annotations

import argparse
import json
from pathlib import Path

def gib(value:int)->str:
    return f"{value/(1024**3):.2f} GiB" if value else "0"

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--profile",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    profile=json.loads(args.profile.read_text(encoding="utf-8"))
    out=args.output_dir
    out.mkdir(parents=True,exist_ok=True)
    system=profile["system"]
    resources=profile["resources"]
    display=profile["display"]
    python=profile["python"]
    lines=[
        "PROVOWARE DUPLIKATE-FINDER 2026 – SYSTEM- UND ABHAENGIGKEITSPROFIL",
        "="*76,
        f"Zeitpunkt: {profile['timestamp']}",
        f"Vorheriges Profil: {profile.get('previous_profile_timestamp') or '-'}",
        f"Gesamtstatus: {'BEREIT' if profile['ready'] else 'PRUEFUNG NOETIG'}",
        "",
        "SYSTEM",
        f"  Betriebssystem: {system['os_release'].get('PRETTY_NAME','unbekannt')}",
        f"  Kernel:         {system['kernel']}",
        f"  Architektur:    {system['machine']}",
        f"  CPU-Kerne:      {system['cpu_count']}",
        f"  RAM gesamt:     {gib(resources['ram_total_bytes'])}",
        f"  RAM frei:       {gib(resources['ram_available_bytes'])}",
        f"  SWAP:           {gib(resources['swap_total_bytes'])}",
        f"  Speicher frei:  {resources['disk_free_mb']} MB",
        "",
        "ANZEIGE",
        f"  Sitzung:        {display['session_type'] or '-'}",
        f"  DISPLAY:        {display['display'] or '-'}",
        f"  WAYLAND:        {display['wayland_display'] or '-'}",
        f"  Qt-Test:        {'OK' if profile['qt']['ok'] else 'FEHLER'}",
        f"  Qt-Plattform:   {profile['qt'].get('platform') or '-'}",
        "",
        "PROJEKT-PYTHON",
        f"  Version:        {python['version']}",
        f"  Datei:          {python['executable']}",
        "",
        "PYTHON-PAKETE",
    ]
    lines.extend(f"  {key:<36} {value}" for key,value in python["packages"].items())
    lines += ["","LINUX-PAKETE / BIBLIOTHEKEN"]
    lines.extend(f"  {key:<36} {value}" for key,value in profile["native_packages"].items())
    lines += ["","HILFSPROGRAMME"]
    lines.extend(f"  {key:<20} {'ja' if value['available'] else 'nein'}  {value['path']}" for key,value in profile["commands"].items())
    lines += ["","SCHREIBRECHTE"]
    lines.extend(f"  {key:<20} {'OK' if value['ok'] else 'FEHLER'}  {value['path']}" for key,value in profile["writable"].items())
    lines += ["","SICHERHEIT","  Kein Tk/Tkinter.","  GUI ausschliesslich PySide6/Qt.","  Keine systemweite pip-Installation.","  Keine Aenderung am System-Python.",""]
    (out/"ABHAENGIGKEITEN_AKTUELL.txt").write_text("\n".join(lines),encoding="utf-8")
    (out/"ABHAENGIGKEITEN_AKTUELL.json").write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
