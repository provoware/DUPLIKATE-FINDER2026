#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${PROVOWARE_PROJECT_DIR:-$ROOT/PROVOWARE-DATEN}"
export PROVOWARE_PROJECT_DIR="$WORKSPACE"

if [[ -x "$ROOT/runtime/bin/python3" ]]; then
  exec "$ROOT/STARTEN.sh"
fi

# Manche USB-Sticks werden unter Linux mit "noexec" eingehängt.
# Dann darf die Python-Laufzeit direkt vom Stick nicht ausgeführt werden.
# In diesem Fall wird nur der Programmordner in einen lokalen temporären
# Laufzeitordner kopiert; Nutzerdaten bleiben weiterhin im gewählten
# Arbeitsordner auf dem Stick.
CACHE_BASE="${XDG_CACHE_HOME:-$HOME/.cache}/provoware-duplikate-finder-portable"
PROFILE_HASH="$(sha256sum "$ROOT/pyproject.toml" "$ROOT/PAKET-PROFIL.json" 2>/dev/null | sha256sum | cut -d' ' -f1)"
LOCAL_ROOT="$CACHE_BASE/$PROFILE_HASH"

mkdir -p "$CACHE_BASE"
if [[ ! -x "$LOCAL_ROOT/runtime/bin/python3" ]]; then
  rm -rf "$LOCAL_ROOT"
  mkdir -p "$LOCAL_ROOT"
  cp -a "$ROOT/." "$LOCAL_ROOT/"
  chmod +x "$LOCAL_ROOT/STARTEN.sh" "$LOCAL_ROOT/STARTEN_KONSOLE.sh" 2>/dev/null || true
fi

exec "$LOCAL_ROOT/STARTEN.sh"
