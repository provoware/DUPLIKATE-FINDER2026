from __future__ import annotations

from datetime import datetime
from typing import Any

EXPORT_SCHEMA = "provoware-state-export-1"


class StateImportError(ValueError):
    pass


def build_export(settings: dict[str, Any], virtual_state: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": EXPORT_SCHEMA,
        "created_at": datetime.now().astimezone().isoformat(),
        "settings": settings,
        "virtual_state": virtual_state,
    }


def validate_import(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise StateImportError("Die Importdatei enthält kein gültiges PROVOWARE-Objekt.")
    if payload.get("schema") != EXPORT_SCHEMA:
        raise StateImportError("Die Importdatei besitzt einen unbekannten PROVOWARE-Stand.")
    settings = payload.get("settings")
    virtual_state = payload.get("virtual_state")
    if not isinstance(settings, dict):
        raise StateImportError("Einstellungen fehlen oder sind beschädigt.")
    if not isinstance(virtual_state, dict):
        raise StateImportError("Virtuelle Daten fehlen oder sind beschädigt.")
    if not isinstance(virtual_state.get("collections", []), list):
        raise StateImportError("Sammlungen sind beschädigt.")
    if not isinstance(virtual_state.get("virtual_items", []), list):
        raise StateImportError("Markierungen sind beschädigt.")
    return payload
