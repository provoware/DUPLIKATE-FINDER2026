from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.safety.policy import SafetyPolicy, SafetyViolation


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    title: str
    message: str


def validate_scan_root(root: Path | None) -> ValidationResult:
    if root is None:
        return ValidationResult(False, "Ordner fehlt", "Bitte zuerst einen Ordner über „Ordner wählen“ auswählen.")
    try:
        safe = SafetyPolicy().ensure_scan_root_allowed(root)
    except SafetyViolation as exc:
        return ValidationResult(False, "Ordner aus Sicherheitsgründen gesperrt", str(exc))
    if not safe.exists():
        return ValidationResult(False, "Ordner nicht gefunden", "Der gewählte Ordner existiert nicht mehr. Bitte erneut auswählen.")
    if not safe.is_dir():
        return ValidationResult(False, "Kein Ordner", "Die Auswahl ist kein Ordner. Bitte einen Ordner auswählen.")
    return ValidationResult(True, "OK", "Ordner ist sicher nutzbar.")


def validate_search_request(root: Path | None, query: str, search_names: bool, search_contents: bool) -> ValidationResult:
    root_result = validate_scan_root(root)
    if not root_result.ok:
        return root_result
    if not query.strip():
        return ValidationResult(False, "Suchbegriff fehlt", "Bitte einen Suchbegriff eingeben.")
    if len(query) > 500:
        return ValidationResult(False, "Suchbegriff zu lang", "Bitte den Suchbegriff auf höchstens 500 Zeichen kürzen.")
    if not (search_names or search_contents):
        return ValidationResult(False, "Suchart fehlt", "Bitte Dateinamen und/oder Dateiinhalte auswählen.")
    return ValidationResult(True, "OK", "Suchauftrag ist gültig.")
