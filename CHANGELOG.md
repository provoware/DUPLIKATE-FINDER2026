# Änderungsprotokoll

## [Unveröffentlicht]

### Geplant
- weitere Dateiformate und spätere, separat freizugebende Schreibfunktionen

## [0.8.0] – 2026-10-06

### Dateien & Vorschau
- eigener modularer Nur-Lesen-Dateibrowser auf Basis des Qt-Dateisystemmodells
- Dateiname- und Dateigruppenfilter ohne vollständigen Verzeichnisbestand in Python zu laden
- sichere Textvorschau mit 512-KiB-Grenze und mehreren üblichen Zeichenkodierungen
- skalierte Bildvorschau für verbreitete Bildformate
- PDF-Erstseitenvorschau über vorhandenes QtPdf ohne neue schwere Fremdbibliothek
- Audio/Video zunächst nur als Metadaten plus Öffnen im Standardprogramm
- Pfad kopieren, Ordner anzeigen, extern öffnen
- virtuelle Markierung und Sammlungszuordnung
- symbolische Verknüpfungen werden nicht automatisch verfolgt
- sichere Benutzer-Mounts unter /run/media gezielt erlaubt; /run bleibt gesperrt

### Erscheinungsbild
- jeder Hauptbereich besitzt eine eigene kontrastreiche Akzentfarbe
- einheitliche dunkle Basis bleibt erhalten
- Dateien-&-Vorschau-Bereich nutzt Orange/Gold als klaren eigenen Funktionsakzent

### Qualität
- Dateityp-, Text-, Bild- und Medienfallback-Tests
- Datei-Browser in gezielte Prüfplanung und autonome UI-Abnahme aufgenommen
- UI-/Prozessbereich nach vollständiger 800×600-/100/150/200-%-, autonomer und Portable-Abnahme wieder FROZEN 🟢
- Lite gegenüber Recovery entpackt um 25,64 % bzw. 252,7 MiB reduziert, ohne aggressive Laufzeitbeschneidung
- Audio/Video und AppImage anschließend separat analysiert; keine zusätzliche Multimedia-Abhängigkeit in v0.8.0 aufgenommen

## [0.7.1] – 2026-10-06

### Wartbarkeit und Entwicklung
- wiederverwendbare Byte-/Größenformatierung zentralisiert
- Dashboard-Karten auf eine gemeinsame Erzeugungsfunktion vereinheitlicht
- gezielte Entwicklungsprüfung verwendet denselben Prüfplan nur einmal
- Git-Diff-Schnellpfad vermeidet unnötiges Hashen des gesamten Projektbaums
- Entwicklungs-Vollpaket läuft nur noch bei relevanten Dateiänderungen
- Laufzeit-/Paketversionen in CI aus `dependencies.env` zentralisiert
- einmaligen v0.7.0-Promotionsworkflow nach erfolgreichem Release entfernt
- Laufzeitordner-Platzhalter aus dem Quellrepository entfernt

### Portable Pakete
- konservatives `Lite`-Profil ohne doppelten PySide6-Reparaturvorrat
- `Recovery`-Profil mit Offline-Reparatur bleibt erhalten
- Python- und Wheel-Bausteine werden im Build gecacht
- Lite und Recovery werden automatisch auf Startfähigkeit und Funktionsgleichheit geprüft
- Lite zusätzlich als ZIP
- `STARTEN_VOM_STICK.sh` mit Fallback für Linux-`noexec`-Datenträger
- keine aggressive Beschneidung der Python-/Qt-Laufzeit

### Bedienung und Sichtbarkeit
- Arbeitsablauf direkt auf der Übersicht sichtbar
- stärkere Navigation-, Fokus-, Tabellen- und Statuskontraste
- Primäraktionen deutlicher hervorgehoben
- Bedienoberfläche für diesen gezielten Auftrag kontrolliert wieder geöffnet; erneute vollständige Abnahme vor Re-Freeze

## [0.7.0] – 2026-10-06

### Robustheit
- versionierte, transaktionale SQLite-Migrationen statt reinem `CREATE TABLE IF NOT EXISTS`
- Dateidentität über Größe, Änderungszeit, Gerät und Inode geprüft
- Dateiänderungen während Kurz- oder SHA-256-Prüfung werden verworfen und protokolliert
- Lesefehler werden gezählt und in der Oberfläche als übersprungene Dateien sichtbar
- Einstellungen und Zustandsexporte werden atomar geschrieben
- beschädigte Einstellungen werden gesichert und sichtbar auf Standardwerte zurückgesetzt
- Zustandsimport wird vollständig vorgeprüft und innerhalb einer Transaktion nachgeprüft

### Skalierung
- Robustheit / Skalierung nach vollständiger Abnahme als FROZEN 🟢 markiert
- produktive Such- und Duplikatläufe verwenden SQLite-Inventare statt vollständiger Python-Dateilisten
- Duplikatpipeline: Dateigröße → kurze Inhaltsprobe → vollständiges SHA-256
- SHA-256 wird nur für unveränderte Dateien wiederverwendet
- alte Such- und Scanläufe werden begrenzt aufbewahrt
- Sammlungen und Duplikatmitglieder werden SQLite-seitenweise geladen
- neue Regressionstests für Migrationen, Rollback, Hash-Stabilität und Großlisten

## [0.6.0] – 2026-10-06

### Verbessert
- Bereichsauswahl wechselt bei schmalen Fenstern in eine klar beschriftete obere Auswahl
- Statuskarten ordnen Überschrift und Wert getrennt an und passen sich bei 200 % an
- gesperrte Dateiaktionen sind kompakt und ausdrücklich beschriftet
- Fokus-, Tabellen- und Kontrollkästchen-Stile verbessert; Statusmeldungen bleiben auch ohne Symbole verständlich
- Bedienoberfläche bei 800×600 sowie 100/150/200 % geprüft und anschließend erneut eingefroren

### Behoben
- Symbolzeichen, die in der Standardschrift als leere Kästchen erschienen, aus der Oberfläche entfernt
- Kartenbeschriftungen auf dunklen Flächen lesbar gemacht
- überbreite Seitenleiste auf kleinen Fenstern durch kompakte Bereichsauswahl ersetzt
- Markierungsänderungen in großen Treffermengen aktualisieren nur die betroffenen Tabellenzeilen statt bis zu 100.000 Zeilen
- Programmversion wird aus den Projektmetadaten gelesen; auch der direkte Build-Nachweis nutzt denselben Stand
- README und Projektmanifest auf v0.6.0 aktualisiert

## [0.5.1] – 2026-10-06

### Korrektur des eingefrorenen Leistungsumfangs
- Suchtreffer jetzt tatsächlich datenvirtualisiert: SQLite ist die Quelle, nicht mehr eine vollständige Python-Trefferliste
- GUI lädt Treffer in Seiten zu 200 Zeilen
- maximal acht Seiten gleichzeitig im GUI-Puffer (standardmäßig höchstens 1.600 Treffer)
- 100.000-Treffer-Regression prüft begrenzten Seitencache
- Sortierung großer Trefferlisten erfolgt datenbankgestützt
- Treffer werden während der Suche in kleinen Blöcken gespeichert
- Bedienoberfläche / Prozesssteuerung bleibt FROZEN; Änderung ist eine Regression-/Vertragskorrektur

## [0.5.0] – 2026-10-06

### Leistung und Überwachung
- Suchtreffer, Duplikatmitglieder und Sammlungseinträge auf virtuelle Qt-Tabellenmodelle umgestellt
- keine Tabellenzeilen-Widgets mehr für jeden einzelnen Treffer
- Regressionstest mit 100.000 Suchtreffern und 20.000 Sammlungseinträgen
- CPU-, RAM- und SWAP-Anzeige ohne zusätzliche externe Bibliothek
- Verarbeitungsgeschwindigkeit in Dateien pro Sekunde
- verarbeitete Datenmenge im laufenden Prozess
- datenmengengewichtete Restzeitschätzung bei Dateiinhalt- und Hash-Prüfungen
- Markierungszustände für große Trefferlisten gebündelt aus SQLite geladen
- Bedienoberfläche / Prozesssteuerung nach vollständiger Abnahme als FROZEN 🟢 markiert

## [0.4.0] – 2026-10-06

### Verbessert
- zweiphasige Fortschrittsanzeige: Dateien erfassen → Dateien prüfen
- Restzeit ignoriert Pausenzeiten
- sicherer Abbruch mit Rückfrage
- modernere, klarer getrennte Listen und Kopfzeilen
- Neonrand nur für Hauptaktionen; ruhigere Sekundärknöpfe
- dunkle kontrastreiche Statusflächen
- CPU-Voreinstellungen 25/50/75/100 Prozent mit echter Kernzahl
- Autosave zeigt letzte Sicherungszeit
- Import legt vor Übernahme automatisch eine Wiederherstellungssicherung an
- Dateityp-Ausschlüsse mit laiengerechten Voreinstellungen
- strengere Import-Versionsprüfung

## [0.3.1] – 2026-10-06

### Hinzugefügt
- kooperative Pause/Fortsetzen-/Abbruchsteuerung für Suche und Duplikatprüfung
- Prozentfortschritt, aktueller Schritt und grobe Restzeitschätzung
- Ausschluss von Python-/Entwicklungsordnern und auswählbaren Dateitypen
- CPU-Kernbegrenzer nur für den PROVOWARE-Prozess
- Autosave der Einstellungen alle fünf Minuten
- sicherer JSON-Import/-Export für Einstellungen und virtuelle Organisation
- Nachvalidierung beim Import
- verbessertes Listenbild mit Sortierung, alternierenden Zeilen und klaren Kopfzeilen
- dunkles Hochkontrast-Design mit Neon-Aktionsrändern
- farblich deutlicher getrennte Bereiche und verbesserte Tooltips
- zweizeiliger Prozessstatus für kleine Fenster

### Behoben
- beschädigte Style-Zeile im bisherigen Qt-Farbschema entfernt

## [0.3.0] – 2026-10-06

### Hinzugefügt
- PROVOWARE-Mastermanifest und globale Standards
- JSON Schema 2020-12 für zentrale Verträge
- triggerbasiertes Agentenmodell mit genau einem Schreibagenten
- Zustandsregister mit SHA-256 und gezielter Prüfplanung
- Standard-Arbeitsordner mit automatischer Erstellung
- Start-Checkpoints mit Ampel, Fortschritt und Aktivitätsanzeige
- dreistufiges Hilfesystem
- versionierter deutscher Textkatalog
- intelligente Fehlerregistrierung mit Lösung
- reproduzierbarer Vollpaketbau, Build-Nachweis und SPDX-Bestandsliste
- GitHub-Caching und Abbruch veralteter Läufe

## [0.2.0] – 2026-10-06

### Hinzugefügt
- professionelle Repository-Grundstruktur
- read-only Sicherheitskern
- Textsuche nach Namen und Inhalt
- Duplikatprüfung für reguläre Dateien über Größe + SHA-256
- gruppierte Duplikatansicht
- virtuelle Markierungen, Notizen und Sammlungen
- gesperrte spätere Dateiaktions-Schalter im Dashboard
- SQLite-Datenmodell
- automatischer Selbsttest
- automatische 100/150/200-%-Sichtbarkeitsprüfung
- portabler Release-Bau mit eigener Python-Laufzeit und PySide6
- Agentenverträge und Entwicklungsdokumentation

- Konsolenmodus mit nummerierten Menüs
- autonome 800×600-/100/150/200-%-Abnahme mit HTML-Bildraster
- professionelles Logging und Diagnose-Dashboard
- Offline-Selbstheilung von PySide6 aus dem portablen wheelhouse
- echter End-to-End-Test des erzeugten und frisch entpackten Release-Pakets
