from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.storage.atomic_io import atomic_write_text
from app.storage.database import Database


FORMAT_VERSION = "1.0.0"


def export_state(database: Database, path: Path, settings: dict) -> dict:
    payload = {
        "format": "PROVOWARE-DUPLIKATE-FINDER-STATE",
        "version": FORMAT_VERSION,
        "exported_at": datetime.now().astimezone().isoformat(),
        "settings": settings,
        "virtual_state": database.export_virtual_state(),
    }
    atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )
    return payload


def _require_dict_rows(value: object, name: str) -> list[dict]:
    if not isinstance(value, list):
        raise ValueError(f"{name} sind ungültig.")
    result: list[dict] = []
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{name}: Eintrag {index + 1} ist ungültig.")
        result.append(row)
    return result


def validate_import_payload(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Die Importdatei enthält kein gültiges PROVOWARE-Objekt.")
    if payload.get("format") != "PROVOWARE-DUPLIKATE-FINDER-STATE":
        raise ValueError("Die Datei ist kein unterstützter PROVOWARE-Export.")
    if payload.get("version") != FORMAT_VERSION:
        raise ValueError(
            f"Nicht unterstützte Exportversion: {payload.get('version')!r}. "
            f"Erwartet wird {FORMAT_VERSION}."
        )

    settings = payload.get("settings", {})
    if not isinstance(settings, dict):
        raise ValueError("Der Einstellungsbereich ist ungültig.")

    state = payload.get("virtual_state")
    if not isinstance(state, dict):
        raise ValueError("Der virtuelle Datenbereich fehlt.")

    collections = _require_dict_rows(state.get("collections", []), "Sammlungen")
    items = _require_dict_rows(
        state.get("collection_items", []),
        "Sammlungseinträge",
    )
    virtual = _require_dict_rows(
        state.get("virtual_items", []),
        "Virtuelle Markierungen",
    )

    known_ids: set[int] = set()
    for index, row in enumerate(collections):
        try:
            collection_id = int(row["id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Sammlung {index + 1} besitzt keine gültige Kennung."
            ) from exc
        name = str(row.get("name", "")).strip()
        if not name:
            raise ValueError(f"Sammlung {index + 1} besitzt keinen Namen.")
        if collection_id in known_ids:
            raise ValueError("Sammlungskennungen sind nicht eindeutig.")
        known_ids.add(collection_id)

    for index, row in enumerate(items):
        try:
            collection_id = int(row["collection_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Sammlungseintrag {index + 1} besitzt keine gültige Sammlungskennung."
            ) from exc
        if collection_id not in known_ids:
            raise ValueError(
                f"Sammlungseintrag {index + 1} verweist auf eine unbekannte Sammlung."
            )
        if not str(row.get("path", "")).strip():
            raise ValueError(
                f"Sammlungseintrag {index + 1} besitzt keinen Dateipfad."
            )

    for index, row in enumerate(virtual):
        if not str(row.get("path", "")).strip():
            raise ValueError(
                f"Virtuelle Markierung {index + 1} besitzt keinen Dateipfad."
            )

    return payload


def import_state(database: Database, path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Importdatei konnte nicht gelesen werden: {exc}"
        ) from exc

    valid = validate_import_payload(payload)
    expected_names = {
        str(item.get("name", "")).strip()
        for item in valid["virtual_state"].get("collections", [])
        if str(item.get("name", "")).strip()
    }
    database.import_virtual_state_atomic(
        valid["virtual_state"],
        expected_names=expected_names,
    )
    return valid
