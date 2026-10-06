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
├── manifest/ standards/ schemas/ resources/
├── data/
├── logs/
├── recovery/
├── quarantine/       nur im Paket für Kompatibilität; Nutzerdaten liegen im Projektordner
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

Danach folgt die End-to-End-Abnahme des **wirklich erzeugten Archivs**:

1. SHA-256 des Archivs prüfen.
2. Archiv in einen frischen Ordner entpacken.
3. `STARTEN.sh` mit echtem PySide6/Qt im unsichtbaren Starttest ausführen.
4. `STARTEN_KONSOLE.sh --selftest` ausführen.
5. PySide6 im entpackten Paket absichtlich entfernen.
6. Internetzugriff für pip deaktivieren und `STARTEN.sh` erneut ausführen.
7. prüfen, dass PySide6 ausschließlich aus dem mitgelieferten `wheelhouse/` repariert wurde.
8. die autonome 73/73-Abnahme direkt mit der entpackten portablen Laufzeit ausführen.
9. HTML-Prüfraster, JSON-Bericht, Startprotokolle und Paket-Prüfsumme als Evidenz sichern.

Erst danach gilt der portable Stand als abgenommen.

Danach werden erzeugt:

- `.tar.gz`
- `.tar.gz.sha256`

## Plattform

v0.3.0 baut zunächst Linux `x86_64`. Weitere Rechner derselben Architektur werden über System-/Startprüfung automatisch erkannt. Weitere Architekturen erhalten erst nach eigenem E2E-Test ein freigegebenes Paket. Weitere Architekturen werden erst nach eigenem Testpfad ergänzt.
