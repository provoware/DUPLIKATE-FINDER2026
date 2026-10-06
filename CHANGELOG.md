# Änderungsprotokoll

## [Unveröffentlicht]

### Hinzugefügt
- selbstbootstrappender Entwicklungsstart mit eigener Python-3.12.15-Laufzeit
- automatisches und wiederverwendbares System-/Abhängigkeitsprofil
- vollständige Abhängigkeitsdokumentation
- Entwicklungs-Vollpaket mit Runtime und lokalem Paketvorrat
- erweiterter Architekturtest: Tk/Tkinter auch in Werkzeugen verboten

### Geplant
- weitere Dateiformate und spätere, separat freizugebende Schreibfunktionen

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
