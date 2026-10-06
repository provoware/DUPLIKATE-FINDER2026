#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  printf '%s\n' \
    'Entwicklungsumgebung fehlt.' \
    'Einmalig im Repository ausführen:' \
    '  python3 -m venv .venv' \
    '  .venv/bin/python -m pip install -e ".[test]"' >&2
  exit 21
fi
export PYTHONNOUSERSITE=1
export PYTHONPATH="$ROOT"
cd "$ROOT"
exec "$PYTHON" -m app.main
