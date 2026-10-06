from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import platform
import sys
import tomllib
import uuid
from datetime import datetime, timezone
from pathlib import Path


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def dependencies()->list[dict[str,str]]:
    names=("PySide6","PySide6_Addons","PySide6_Essentials","shiboken6","pytest","setuptools","wheel","pip")
    result=[]
    for name in names:
        try: version=metadata.version(name)
        except metadata.PackageNotFoundError: version="nicht-installiert"
        result.append({"name":name,"version":version})
    return result


def project_version()->str:
    metadata_file=Path(__file__).resolve().parents[1]/"pyproject.toml"
    try:
        project=tomllib.loads(metadata_file.read_text(encoding="utf-8"))["project"]
        return str(project["version"])
    except (OSError,KeyError,tomllib.TOMLDecodeError):
        return "0+unbekannt"


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--commit",required=True)
    p.add_argument("--project-version",default=project_version())
    args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    created=datetime.now(timezone.utc).isoformat()
    archive_hash=sha256(args.archive)
    deps=dependencies()
    build={
        "schema_version":"1.0.0",
        "created":created,
        "commit":args.commit,
        "project_version":args.project_version,
        "archive":{"name":args.archive.name,"sha256":archive_hash,"bytes":args.archive.stat().st_size},
        "runtime":{"python":platform.python_version(),"machine":platform.machine(),"system":platform.system()},
        "dependencies":deps,
        "provenance_note":"Schlanker Build-Nachweis nach SLSA-Provenienzprinzipien; keine formale SLSA-Level-Zertifizierung.",
    }
    (args.output_dir/"BUILD-NACHWEIS.json").write_text(json.dumps(build,ensure_ascii=False,indent=2),encoding="utf-8")

    namespace=f"https://provoware.local/spdx/{uuid.uuid4()}"
    packages=[{
        "SPDXID":"SPDXRef-Package-Project",
        "name":"PROVOWARE-DUPLIKATE-FINDER-2026",
        "versionInfo":args.project_version,
        "downloadLocation":"NOASSERTION",
        "filesAnalyzed":False,
        "supplier":"Organization: PROVOWARE",
    }]
    relationships=[]
    for index,dep in enumerate(deps,1):
        spdxid=f"SPDXRef-Package-Dependency-{index}"
        packages.append({"SPDXID":spdxid,"name":dep["name"],"versionInfo":dep["version"],"downloadLocation":"NOASSERTION","filesAnalyzed":False})
        relationships.append({"spdxElementId":"SPDXRef-Package-Project","relationshipType":"DEPENDS_ON","relatedSpdxElement":spdxid})
    spdx={
        "spdxVersion":"SPDX-2.3",
        "dataLicense":"CC0-1.0",
        "SPDXID":"SPDXRef-DOCUMENT",
        "name":"PROVOWARE DUPLIKATE-FINDER 2026 SBOM",
        "documentNamespace":namespace,
        "creationInfo":{"created":created.replace("+00:00","Z"),"creators":["Tool: PROVOWARE build_metadata.py"]},
        "packages":packages,
        "relationships":[{"spdxElementId":"SPDXRef-DOCUMENT","relationshipType":"DESCRIBES","relatedSpdxElement":"SPDXRef-Package-Project"},*relationships],
    }
    (args.output_dir/"SBOM.spdx.json").write_text(json.dumps(spdx,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"OK | Build-Nachweis | {args.archive.name} | sha256={archive_hash}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
