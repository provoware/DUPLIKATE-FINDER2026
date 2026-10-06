# PROVOWARE DUPLIKATE-FINDER 2026 – v0.9.0

## Verbesserungen

- PDF-Vorschau mit Vor-/Zurück-Navigation und Seitenzahl.
- DOCX- und ODT-Textvorschau ohne neue Pflichtbibliothek. Formatierungen,
  eingebettete Bilder und Makros werden nicht ausgeführt oder dargestellt.
- Textvorschau mit Zeichencodierung und Zählwerten; gültiges JSON wird eingerückt.
- Bildinformationen: Format, Pixelmaße, Megapixel und Seitenverhältnis.
- WAV-Informationen: Dauer, Kanäle, Abtastrate und Bit-Tiefe.
- Verständliche Hilfetexte, Filterbeispiele und ausführlichere Laienanleitung.

## Robustheit und Sicherheit

Textdateien werden bereits beim Einlesen auf 512 KiB begrenzt. Windows-Texte
werden ohne UTF-16-Kennung nicht mehr fälschlich als UTF-16 gelesen. Defekte
WAV-Dateien und sehr tief verschachtelte JSON-Dateien bringen die Vorschau
nicht zum Absturz. Dokumentvorschauen begrenzen internen XML-Text auf 4 MiB
und angezeigten Text auf 100.000 Zeichen; DTD-Strukturen werden abgelehnt.
Originaldateien bleiben unverändert. Löschen, Verschieben, Umbenennen,
Überschreiben und Quarantäne bleiben gesperrt.

## Downloads und Prüfungen

- **Lite tar.gz / ZIP:** für die normale Nutzung, eigene Python-/Qt-Laufzeit.
- **Recovery tar.gz:** zusätzlich lokale Bausteine zur Offline-Reparatur.
- **SHA-256-Dateien:** Prüfsummen für alle Downloadpakete.
- **PRUEFNACHWEISE:** Paketgrößen, automatische Abnahmeberichte und
  Build-/Komponentennachweise mit Versions- und Commitbezug.

Die Veröffentlichung ist an erfolgreiche Kern-/Sicherheitstests, autonome
Abnahme mit 800×600-Basisprofil, 100/150/200-%-Oberflächenprüfungen sowie
Start und Funktionsgleichheit beider Paketvarianten gebunden.

Das separat geprüfte AppImage bleibt ein Prototyp als GitHub-Actions-Artefakt.
Die Starttests auf Ubuntu 22.04/24.04 und einem simulierten USB-Pfad ersetzen
keinen Test auf jedem Linux-System oder einem physischen USB-Stick.
Audio/Video öffnen sich im Standardprogramm. Erweiterte Metadaten anderer
Medienformate und ein interner Player sind nicht Bestandteil dieser Version.

## Start

1. Lite herunterladen und vollständig entpacken.
2. `STARTEN.sh` starten; auf einem USB-Stick `STARTEN_VOM_STICK.sh` verwenden.
3. Ordner wählen, Dateien suchen oder im Bereich „Dateien & Vorschau“ anklicken.

Projekt: https://github.com/provoware/DUPLIKATE-FINDER2026
Anleitung: https://github.com/provoware/DUPLIKATE-FINDER2026/blob/main/docs/LAIENANLEITUNG.md
Probleme melden: https://github.com/provoware/DUPLIKATE-FINDER2026/issues
