# Portabler Linux-Release

## Ziel

Der Endnutzer soll keine Python-Pakete und keine Linux-Systempakete installieren müssen.

## Release-Aufbau

```text
PROVOWARE-DUPLIKATE-FINDER-2026/
├── runtime/          eigene Python-Laufzeit + PySide6
├── app/
├── docs/
├── agents/
├── data/
├── logs/
├── recovery/
├── quarantine/
├── STARTEN.sh
└── STARTEN.desktop
```

## Laufzeit

Der automatische Release-Bau verwendet eine fest definierte portable CPython-3.12-Laufzeit und prüft deren SHA-256 vor dem Entpacken.

Anschließend wird PySide6 direkt in diese Laufzeit installiert.

## Startvertrag

`STARTEN.sh` akzeptiert ausschließlich `runtime/bin/python3`.

Fehlt die Datei, wird beendet. Kein Fallback auf `/usr/bin/python`, keine Paketinstallation, kein `sudo`.

## Paketprüfung

Vor Erzeugung des Archivs läuft der Selbsttest mit genau der gebündelten Laufzeit.

Danach werden erzeugt:

- `.tar.gz`
- `.tar.gz.sha256`

## Plattform

v0.1.0 baut zunächst Linux `x86_64`. Weitere Architekturen werden erst nach eigenem Testpfad ergänzt.
