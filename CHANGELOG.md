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

## [0.4.0] – 2026-10-06

### Hinzugefügt
- sichere Pause-, Fortsetzen- und Abbruchsteuerung für Hintergrundprüfungen
- Fortschrittsanzeige mit aktuellem Schritt und ungefährer Restzeit
- CPU-Kernbegrenzung für parallele SHA-256-Duplikatprüfung
- Filter für Entwicklungs-/Python-Arbeitsordner, versteckte Ordner und Dateitypen
- fünfminütige Autospeicherung als PROVOWARE-Wiederherstellungsstand
- sicherer Export/Import von Einstellungen und virtueller Organisation
- Pfadkopie und Öffnen des Trefferordners
- Textkatalog 1.1.0 mit manifestgesteuerter Auswahl
- zusätzliche autonome Regressionstests für Filter, Abbruch, Einstellungen und Zustandsübertragung

### Geändert
- dunkle Hochkontrast-Oberfläche mit Neon-Rahmen für Aktionstasten
- Listen und Tabellen mit klareren Kopfzeilen, Zeilenabständen und Bereichstrennung
- autonome Mindestabdeckung von 77 auf 82 Prüfungen erhöht

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
