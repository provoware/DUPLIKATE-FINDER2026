#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/runtime/bin/python3"

if [[ ! -x "$PYTHON" ]]; then
  printf '%s\n' \
    'PROVOWARE DUPLIKATE-FINDER 2026 konnte nicht gestartet werden.' \
    'Die mitgelieferte portable Laufzeit fehlt oder ist unvollständig.' \
    'Es wird absichtlich NICHT auf das System-Python ausgewichen.' >&2
  exit 20
fi

export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$ROOT"
cd "$ROOT"
exec "$PYTHON" -m app.main
