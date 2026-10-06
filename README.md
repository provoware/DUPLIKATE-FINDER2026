# PROVOWARE DUPLIKATE-FINDER 2026

Lokales Linux-Werkzeug für **Textsuche**, **vollständige Duplikatprüfung** und **virtuelle Organisation**. Das Programm liest Originaldateien, verändert sie aber nie.

## Sicherheitsversprechen

- keine Originaldatei löschen
- keine Originaldatei verschieben
- keine Originaldatei umbenennen
- keine Originaldatei überschreiben
- kritische Linux-Systembereiche blockieren
- symbolische Verknüpfungen standardmäßig nicht verfolgen
- Duplikate erst nach vollständiger SHA-256-Prüfung als identisch anzeigen
- Sammlungen, Markierungen und Notizen nur in der lokalen SQLite-Datenbank speichern

Die später vorgesehenen Dateiaktionen **Verschieben**, **Umbenennen**, **Quarantäne** und **Löschen** sind im Dashboard sichtbar, aber doppelt gesperrt: Oberfläche deaktiviert + Datenbank-Schalter `enabled=0`, `locked=1`.

## Aktueller Funktionsumfang

### Textsuche
Unterstützte Textformate: `.txt`, `.md`, `.csv`, `.log`, `.json`, `.xml`, `.yaml`, `.yml`, `.ini`, `.conf`, `.py`, `.sh`.

Gesucht werden kann in Dateinamen und/oder Dateiinhalten.

### Duplikate
Die Duplikatprüfung kann reguläre Dateien aller Dateitypen prüfen. Ablauf:

1. Dateien speicherschonend in einem lokalen SQLite-Inventar erfassen.
2. Nur gleiche Dateigrößen als Kandidaten weiterprüfen.
3. Kandidaten mit einer kurzen Inhaltsprobe vorsortieren.
4. Verbleibende Kandidaten vollständig mit SHA-256 prüfen.
5. während der Prüfung kontrollieren, ob die Datei unverändert geblieben ist.
6. nur identische vollständige SHA-256-Prüfsummen als Duplikatgruppe anzeigen.

### Virtuelle Sammlungen
Treffer können markiert, kommentiert und Sammlungen zugeordnet werden. Die Originaldatei bleibt dabei unverändert an ihrem Speicherort.

## Oberfläche

Die grafische Oberfläche verwendet ausschließlich **PySide6/Qt**. Tkinter ist durch einen automatischen Architekturtest verboten.

Die Abnahme beginnt verbindlich bei **800 × 600**. Danach folgen größere Bildschirmprofile sowie **150 % und 200 %**. Zusätzlich entsteht ein HTML-Raster mit Prüfbildern aller Hauptseiten.

Die Prüfung wird automatisiert in GitHub Actions ausgeführt und erzeugt zusätzlich Prüfbilder.

## Portabler Start

Das veröffentlichte Linux-Paket enthält eine eigene Python-3.12-Laufzeit und PySide6. `STARTEN.sh` verwendet ausschließlich `runtime/bin/python3`.

Fehlt diese Laufzeit, bricht der Start verständlich ab. Es wird **nicht** heimlich auf System-Python ausgewichen und es werden keine Linux-Systempakete installiert.

## Entwicklung

Für die normale lokale Einrichtung genügt:

```bash
./ENTWICKLUNG_STARTEN.sh
```

Der Starter verwaltet sein eigenes Python 3.12.15 unter `.provoware-dev/`, prüft Paketversionen, repariert fehlende Python-Abhängigkeiten und schreibt ein wiederverwendbares Systemprofil. Ein vorhandenes Python 3.14 wird nicht als Projekt-Python benutzt.

Das **PROVOWARE-Vollpaket** bringt Runtime und Paketvorrat bereits mit. Beim nackten GitHub-Quellcode lädt der Starter fehlende Bestandteile automatisch nach.

**Kein Tk/Tkinter:** Die GUI verwendet ausschließlich PySide6/Qt.

Vollständige Liste: `docs/ABHAENGIGKEITEN.md`.

## Struktur

```text
app/
  core/       Suche, Scanner, Hashing, Duplikate
  gui/        PySide6-Oberfläche und Hintergrundarbeiten
  models/     Datenmodelle
  safety/     unverhandelbare Schutzregeln
  startup/    Selbsttest
  storage/    SQLite
agents/       feste Rollen für Entwicklungsagenten
docs/         Pflichtenheft, Architektur, Datenmodell, Sicherheit, Release
tests/        automatisierte Schutz- und Funktionstests
tools/        Prüfwerkzeuge
.github/      CI, Release-Bau, Vorlagen
```

## Dokumentation

- `docs/PFLICHTENHEFT_V1.md`
- `docs/ARCHITEKTUR.md`
- `docs/DATENMODELL.md`
- `docs/SICHERHEITSVERTRAG.md`
- `docs/BARRIEREFREIHEIT.md`
- `docs/PORTABLE_RELEASE.md`
- `docs/ENTWICKLUNG.md`
- `AGENTS.md`
- `agents/`

## Projektstatus

**v0.7.0 – robuste Scan-Pipeline / SQLite-Großlisten / Nur-Lesen-Sicherheitsstand**

Physische Dateiänderungen sind noch nicht freigegeben. Dieser Bereich bleibt gesperrt, bis ein eigener Änderungsvertrag, Vorschau, Transaktionsjournal, Rückgängig-Funktion und separate Abnahmetests existieren.

## Autonome Abnahme

    python tools/autonomous_acceptance.py --output artifacts/abnahme

Der Bericht `artifacts/abnahme/index.html` zeigt Maschinenstatus und sämtliche Prüfbilder in einem Raster.

## Konsolenmodus

Das Werkzeug ist zusätzlich ohne grafische Oberfläche bedienbar:

    ./STARTEN_KONSOLE.sh

Die Konsole verwendet nummerierte Menüs, sichere Vorauswahlen und dieselben Schutzregeln wie die GUI.

## Komfort und Diagnose

- automatische Bildschirmgrößen-Erkennung
- Ausgangsbasis 800 × 600
- auswählbare Fensterprofile
- Schrift-/Seitenzoom 80–200 %
- Strg + Mausrad für Zoom
- sortierbare Ergebnistabellen
- SQLite-seitenweise Suchtreffer, Sammlungen und Duplikatmitglieder
- sichtbare Anzahl übersprungener oder nicht lesbarer Dateien
- geprüfter SHA-256-Zwischenspeicher für unveränderte Dateien
- Drag & Drop von Suchtreffern in virtuelle Sammlungen
- farblich und textlich eindeutiger Status
- rotierende Protokolle im Ordner logs/
- lokaler Selbsttest im Dashboard

## PROVOWARE-Autonomiestandard 0.3

Neu hinzugekommen:

- automatischer Standard-Arbeitsordner unter `~/PROVOWARE/DUPLIKATE-FINDER-2026`
- Start-Checkpoints mit Ampelstatus
- Fortschritts- und Aktivitätsanzeige
- dreistufiges Hilfesystem
- globale Design- und Entwicklungsstandards
- versionierter deutscher Textkatalog
- JSON-Manifeste und JSON-Schema-Vorlagen
- Ein-Schreibagent-Modell
- zustandsbasierte gezielte Prüfplanung
- Fehlerkatalog mit Lösungspflicht
- wiederverwendete Abhängigkeiten per Fingerabdruck
- GitHub-Cache und Abbruch veralteter Prüfungen
- Build-Nachweis und SPDX-Komponentenliste

Für Laien: `docs/LAIENANLEITUNG.md`.

Für Entwickler: `docs/ENTWICKLERHANDBUCH.md`.
