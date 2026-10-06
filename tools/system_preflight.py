from __future__ import annotations

import argparse
import json
import locale
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from importlib import metadata
from pathlib import Path

COMMANDS = ("bash","curl","wget","tar","sha256sum","openssl","dpkg-query","dpkg-deb","apt","apt-get","xdg-open")
NATIVE_PACKAGES = (
    "libegl1","libgl1","libxkbcommon0","libfontconfig1","libdbus-1-3",
    "libx11-6","libxcb1","libxext6","libxrender1","libsm6","libice6",
    "libxkbcommon-x11-0","libxcb-cursor0","libxcb-xinerama0","libxcb-randr0",
    "libxcb-render-util0","libxcb-keysyms1","libxcb-icccm4","libxcb-image0","libxcb-shape0",
)
PY_PACKAGES = ("provoware-duplicate-finder-2026","PySide6","PySide6_Addons","PySide6_Essentials","shiboken6","pytest","setuptools","wheel","pip")

def read_os_release() -> dict[str,str]:
    result={}
    path=Path("/etc/os-release")
    if not path.exists():
        return result
    for raw in path.read_text(encoding="utf-8",errors="replace").splitlines():
        if "=" in raw:
            key,value=raw.split("=",1)
            result[key]=value.strip().strip('"')
    return result

def pkg_version(name:str)->str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "NICHT INSTALLIERT"

def native_version(name:str)->str:
    if not shutil.which("dpkg-query"):
        return "nicht ueber dpkg ermittelbar"
    proc=subprocess.run(["dpkg-query","-W","-f=${Status}|${Version}",name],capture_output=True,text=True)
    return proc.stdout.strip() if proc.returncode==0 else "nicht systemweit installiert"

def command_data(name:str)->dict[str,object]:
    path=shutil.which(name)
    return {"available":bool(path),"path":path or ""}

def writable(path:Path)->dict[str,object]:
    try:
        path.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path,prefix=".probe_") as handle:
            handle.write(b"ok")
            handle.flush()
        return {"ok":True,"detail":"schreibbar","path":str(path)}
    except OSError as exc:
        return {"ok":False,"detail":str(exc),"path":str(path)}

def qt_probe()->dict[str,object]:
    env=os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM","offscreen")
    code="from PySide6.QtWidgets import QApplication; app=QApplication([]); print(app.platformName()); app.quit()"
    proc=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,env=env)
    return {"ok":proc.returncode==0,"platform":proc.stdout.strip(),"error":proc.stderr.strip()[-2000:]}

def memory()->dict[str,int]:
    out={}
    path=Path("/proc/meminfo")
    if path.exists():
        for raw in path.read_text(encoding="utf-8",errors="replace").splitlines():
            if ":" not in raw:
                continue
            key,value=raw.split(":",1)
            parts=value.split()
            if parts and parts[0].isdigit():
                out[key]=int(parts[0])*1024
    return out

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve()
    output=args.output.resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    old={}
    if output.exists():
        try:
            old=json.loads(output.read_text(encoding="utf-8"))
        except Exception:
            old={}
    disk=shutil.disk_usage(root)
    mem=memory()
    release=read_os_release()
    workdirs={name:writable(path) for name,path in {
        "projekt":root,"data":root/"data","logs":root/"logs","recovery":root/"recovery",
        "quarantine":root/"quarantine","entwicklung":root/".provoware-dev",
    }.items()}
    profile={
        "schema":1,
        "timestamp":datetime.now().astimezone().isoformat(),
        "epoch":time.time(),
        "previous_profile_timestamp":old.get("timestamp"),
        "system":{
            "os_release":release,"kernel":platform.release(),"machine":platform.machine(),
            "cpu_count":os.cpu_count(),"hostname":platform.node(),"locale":locale.getlocale(),
        },
        "display":{
            "session_type":os.environ.get("XDG_SESSION_TYPE",""),
            "display":os.environ.get("DISPLAY",""),
            "wayland_display":os.environ.get("WAYLAND_DISPLAY",""),
        },
        "resources":{
            "ram_total_bytes":mem.get("MemTotal",0),
            "ram_available_bytes":mem.get("MemAvailable",0),
            "swap_total_bytes":mem.get("SwapTotal",0),
            "disk_total_bytes":disk.total,
            "disk_free_bytes":disk.free,
            "disk_free_mb":disk.free//(1024*1024),
        },
        "python":{"version":platform.python_version(),"executable":sys.executable,
                  "packages":{name:pkg_version(name) for name in PY_PACKAGES}},
        "commands":{name:command_data(name) for name in COMMANDS},
        "native_packages":{name:native_version(name) for name in NATIVE_PACKAGES},
        "writable":workdirs,
        "qt":qt_probe(),
        "decisions":{
            "architecture_supported":platform.machine() in {"x86_64","AMD64"},
            "python_312":sys.version_info[:2]==(3,12),
            "enough_disk":disk.free>=2*1024*1024*1024,
            "all_workdirs_writable":all(value["ok"] for value in workdirs.values()),
        },
    }
    profile["ready"]=all(profile["decisions"].values()) and bool(profile["qt"]["ok"])
    output.write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding="utf-8")
    print("SYSTEMPROFIL:", "BEREIT" if profile["ready"] else "PRUEFUNG NOETIG")
    print("  Betriebssystem:", release.get("PRETTY_NAME",platform.platform()))
    print("  Architektur:", platform.machine())
    print("  Python:", platform.python_version())
    print("  Freier Speicher:", profile["resources"]["disk_free_mb"],"MB")
    print("  Qt:", "OK" if profile["qt"]["ok"] else "FEHLER")
    return 0 if profile["ready"] else 2

if __name__=="__main__":
    raise SystemExit(main())
