#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CFG="$ROOT/dependencies.env"
DEV="$ROOT/.provoware-dev"
RUNTIME="$DEV/runtime"
CACHE="$DEV/cache"
WHEELS="$DEV/wheelhouse"
PY="$RUNTIME/bin/python3"
PROFILE="$DEV/systemprofil.json"
DEPS_STAMP="$DEV/dependency-fingerprint.sha256"

[[ -f "$CFG" ]] || { echo "FEHLER: dependencies.env fehlt. Repository unvollstaendig." >&2; exit 20; }
# shellcheck disable=SC1090
source "$CFG"

mkdir -p "$DEV" "$CACHE" "$WHEELS" "$ROOT/logs"

if [[ -t 1 ]]; then
  G=$'\033[1;32m'; Y=$'\033[1;33m'; R=$'\033[1;31m'; C=$'\033[1;36m'; N=$'\033[0m'
else
  G=""; Y=""; R=""; C=""; N=""
fi
step(){ printf '%s▶%s %s\n' "$C" "$N" "$*"; }
progress(){
  local pct="$1" label="$2" filled=$((pct/10)) bar="" i
  for ((i=0;i<10;i++)); do
    if (( i < filled )); then bar+="█"; else bar+="░"; fi
  done
  printf '[%s] %3d%% · %s\n' "$bar" "$pct" "$label"
}
ok(){ printf '%s✔%s %s\n' "$G" "$N" "$*"; }
warn(){ printf '%s⚠%s %s\n' "$Y" "$N" "$*"; }
die(){ printf '%s✖ FEHLER:%s %s\n' "$R" "$N" "$*" >&2; exit 1; }

sha256_of(){
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; return; fi
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$1" <<'PY'
import hashlib, sys
h=hashlib.sha256()
with open(sys.argv[1],"rb") as f:
    for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
print(h.hexdigest())
PY
    return
  fi
  command -v openssl >/dev/null 2>&1 || die "Keine SHA-256-Pruefung verfuegbar."
  openssl dgst -sha256 "$1" | awk '{print $NF}'
}

download(){
  local url="$1" out="$2" tmp="$2.part"
  rm -f -- "$tmp"
  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --retry 3 --output "$tmp" "$url"
  elif command -v wget >/dev/null 2>&1; then
    wget --tries=3 --output-document="$tmp" "$url"
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "$url" "$tmp" <<'PY'
import sys, urllib.request
with urllib.request.urlopen(sys.argv[1], timeout=60) as src, open(sys.argv[2],"wb") as dst:
    while True:
        block=src.read(1024*1024)
        if not block: break
        dst.write(block)
PY
  else
    die "Beim nackten Quellcode fehlt ein Downloader. Das PROVOWARE-Vollpaket benoetigt diesen Schritt nicht."
  fi
  mv -- "$tmp" "$out"
}

runtime_ok(){
  [[ -x "$PY" ]] || return 1
  "$PY" - "$PYTHON_VERSION" <<'PY' >/dev/null 2>&1
import sys
wanted=tuple(map(int,sys.argv[1].split(".")))
raise SystemExit(0 if sys.version_info[:3]==wanted else 1)
PY
}

copy_bundled_runtime_if_present(){
  local bundled="$ROOT/runtime/bin/python3"
  [[ -x "$bundled" ]] || return 1
  "$bundled" - "$PYTHON_VERSION" <<'PY' >/dev/null 2>&1 || return 1
import sys
wanted=tuple(map(int,sys.argv[1].split(".")))
raise SystemExit(0 if sys.version_info[:3]==wanted else 1)
PY
  step "Mitgelieferte Python-Laufzeit fuer die Entwicklung verwenden"
  rm -rf -- "$RUNTIME"
  cp -a "$ROOT/runtime" "$RUNTIME"
  ok "Mitgeliefertes Python wurde lokal fuer die Entwicklung vorbereitet."
}

ensure_runtime(){
  step "Projekt-Python pruefen"
  if runtime_ok; then ok "Python $PYTHON_VERSION bereits vorhanden."; return; fi
  if copy_bundled_runtime_if_present && runtime_ok; then return; fi
  local archive="$CACHE/$PYTHON_ARCHIVE"
  mkdir -p "$CACHE"
  if [[ -f "$archive" ]] && [[ "$(sha256_of "$archive")" != "$PYTHON_SHA256" ]]; then
    warn "Zwischengespeichertes Python ist ungueltig und wird verworfen."
    rm -f -- "$archive"
  fi
  if [[ ! -f "$archive" ]]; then
    warn "Dies ist nur der GitHub-Quellcode. Das Vollpaket wuerde Python bereits mitbringen."
    step "Python $PYTHON_VERSION automatisch in den Projektordner laden"
    download "$PYTHON_URL" "$archive"
  fi
  [[ "$(sha256_of "$archive")" == "$PYTHON_SHA256" ]] || die "Python-Pruefsumme stimmt nicht."
  local unpack="$DEV/unpack"
  rm -rf -- "$unpack" "$RUNTIME"
  mkdir -p "$unpack"
  if command -v tar >/dev/null 2>&1; then
    tar -xzf "$archive" -C "$unpack"
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "$archive" "$unpack" <<'PY'
import sys, tarfile
with tarfile.open(sys.argv[1],"r:gz") as f: f.extractall(sys.argv[2], filter="data")
PY
  else
    die "Python-Archiv kann nicht entpackt werden."
  fi
  [[ -x "$unpack/python/bin/python3" ]] || die "Unerwartete Python-Archivstruktur."
  mv "$unpack/python" "$RUNTIME"
  rm -rf -- "$unpack"
  runtime_ok || die "Lokales Python konnte nicht eingerichtet werden."
  ok "Python $PYTHON_VERSION ist lokal startbereit."
}

ensure_pip(){
  "$PY" -m pip --version >/dev/null 2>&1 || "$PY" -m ensurepip --upgrade
}

copy_bundled_wheels(){
  [[ -d "$ROOT/wheelhouse" ]] || return 1
  step "Mitgelieferten Paketvorrat uebernehmen"
  cp -an "$ROOT/wheelhouse/." "$WHEELS/" || true
}

wheel_present(){ compgen -G "$WHEELS/$1" >/dev/null; }

ensure_wheels(){
  copy_bundled_wheels || true
  if { wheel_present "pyside6-$PYSIDE6_VERSION-*.whl" || wheel_present "PySide6-$PYSIDE6_VERSION-*.whl"; } && wheel_present "pytest-*.whl" && wheel_present "setuptools-*.whl" && wheel_present "wheel-*.whl"; then
    ok "Alle benoetigten Python-Pakete liegen lokal vor."
    return
  fi
  warn "Lokaler Paketvorrat ist unvollstaendig. Fehlende Pakete werden einmalig geladen."
  "$PY" -m pip download --disable-pip-version-check --only-binary=:all: --dest "$WHEELS" "PySide6==$PYSIDE6_VERSION" "$PYTEST_SPEC" "$SETUPTOOLS_SPEC" "$WHEEL_SPEC"
  ok "Lokaler Paketvorrat vervollstaendigt."
}

dependency_fingerprint(){
  "$PY" - "$CFG" "$ROOT/pyproject.toml" <<'PY'
import hashlib,sys
h=hashlib.sha256()
for name in sys.argv[1:]:
    with open(name,"rb") as handle: h.update(handle.read())
print(h.hexdigest())
PY
}

dependencies_healthy(){
  "$PY" - "$PYSIDE6_VERSION" <<'PY' >/dev/null 2>&1
import importlib.metadata as m, sys
wanted=sys.argv[1]
raise SystemExit(0 if m.version("PySide6")==wanted else 1)
PY
}

install_dependencies(){
  local current
  current="$(dependency_fingerprint)"
  if [[ -f "$DEPS_STAMP" ]] && [[ "$(cat "$DEPS_STAMP")" == "$current" ]] && dependencies_healthy; then
    ok "Abhängigkeiten unverändert – vorhandenen geprüften Zustand wiederverwenden."
    return
  fi
  step "Abhaengigkeiten lokal pruefen und reparieren"
  "$PY" -m pip install --disable-pip-version-check --no-index --find-links "$WHEELS" "$SETUPTOOLS_SPEC" "$WHEEL_SPEC" "PySide6==$PYSIDE6_VERSION" "$PYTEST_SPEC"
  # Das Projekt selbst wird nicht installiert. PYTHONPATH zeigt beim Start direkt auf den Projektordner.
  "$PY" - <<PY
import importlib.metadata as m
assert m.version("PySide6") == "$PYSIDE6_VERSION"
print("PySide6", m.version("PySide6"))
print("pytest", m.version("pytest"))
PY
  printf '%s\n' "$current" > "$DEPS_STAMP"
  ok "Python-Abhaengigkeiten sind in Ordnung und registriert."
}

run_profile(){
  step "System, Bildschirm und Abhaengigkeiten vollautomatisch pruefen"
  "$PY" "$ROOT/tools/system_preflight.py" --root "$ROOT" --output "$PROFILE"
  "$PY" "$ROOT/tools/abhaengigkeiten_bericht.py" --profile "$PROFILE" --output-dir "$ROOT/logs"
  "$PY" "$ROOT/tools/state_registry.py" --output "$ROOT/logs/PRUEFPLAN_AKTUELL.json"
  "$PY" "$ROOT/tools/agent_router.py" --plan "$ROOT/logs/PRUEFPLAN_AKTUELL.json" --output "$ROOT/logs/AGENTENPLAN_AKTUELL.json"
  ok "Systemprofil gespeichert: .provoware-dev/systemprofil.json"
  ok "Lesbarer Bericht: logs/ABHAENGIGKEITEN_AKTUELL.txt"
}

MODE="${1:-gui}"
case "$MODE" in
  gui|--gui) MODE="gui" ;;
  --konsole) MODE="console" ;;
  --nur-pruefen) MODE="check" ;;
  --schnelltest) MODE="quicktests" ;;
  --tests) MODE="tests" ;;
  --abnahme) MODE="acceptance" ;;
  -h|--hilfe|--help)
    cat <<'EOF'
PROVOWARE Entwicklungsstart
  ./ENTWICKLUNG_STARTEN.sh              automatisch vorbereiten und GUI starten
  ./ENTWICKLUNG_STARTEN.sh --konsole    Konsolenoberflaeche starten
  ./ENTWICKLUNG_STARTEN.sh --nur-pruefen alles pruefen/reparieren, dann beenden
  ./ENTWICKLUNG_STARTEN.sh --schnelltest gezielte Prüfungen für geänderte Bereiche
  ./ENTWICKLUNG_STARTEN.sh --tests      vollständige Kompilierung + Tests
  ./ENTWICKLUNG_STARTEN.sh --abnahme    autonome 73/73-Abnahme
EOF
    exit 0 ;;
  *) die "Unbekannte Option: $MODE" ;;
esac

progress 5 "Start vorbereiten"
ensure_runtime
progress 20 "Python bereit"
ensure_pip
ensure_wheels
progress 40 "Lokaler Paketvorrat bereit"
install_dependencies
progress 65 "Abhängigkeiten geprüft"
run_profile
progress 90 "System- und Projektzustand geprüft"

export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$ROOT"
cd "$ROOT"

progress 100 "Bereit"
printf '\n%sPROVOWARE Entwicklungsumgebung BEREIT 🟢%s\n' "$G" "$N"
printf 'Python: %s\n' "$("$PY" --version)"
printf 'PySide6: %s\n' "$("$PY" -c 'import PySide6; print(PySide6.__version__)')"
printf 'Keine Tk/Tkinter-Oberflaeche · GUI ausschliesslich PySide6/Qt\n\n'

case "$MODE" in
  gui) exec "$PY" -m app.main ;;
  console) exec "$PY" -m app.cli ;;
  check) "$PY" -m app.startup.bootstrap ;;
  quicktests) exec "$PY" tools/targeted_checks.py ;;
  tests) exec "$PY" tools/targeted_checks.py --full ;;
  acceptance) export QT_QPA_PLATFORM=offscreen; exec "$PY" tools/autonomous_acceptance.py --output artifacts/abnahme ;;
esac
