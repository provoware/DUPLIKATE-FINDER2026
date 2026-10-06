#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/runtime/bin/python3"
if [[ ! -x "$PYTHON" ]]; then
  printf '%s\n' 'PROVOWARE DUPLIKATE-FINDER 2026 kann nicht gestartet werden.' 'Die portable Laufzeit fehlt. Das System-Python wird absichtlich nicht benutzt.' >&2
  exit 20
fi
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$ROOT"
cd "$ROOT"
"$PYTHON" -m app.startup.bootstrap --console
exec "$PYTHON" -m app.cli "$@"
