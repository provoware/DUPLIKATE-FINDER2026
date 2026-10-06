# PROVOWARE DUPLIKATE-FINDER 2026 – v0.8.0

## Überblick

v0.8.0 erweitert den stabilen Nur-Lesen-Stand um einen modularen Bereich **„Dateien & Vorschau“**. Text-, Bild- und PDF-Dateien können direkt im Tool betrachtet werden, ohne Originaldateien zu verändern. Audio und Video werden erkannt, mit Metadaten angezeigt und weiterhin sicher an das Linux-Standardprogramm übergeben.

## Neue Funktionen

- eigener Datei-/Medienbrowser auf Basis des Qt-Dateisystemmodells
- Auswahl normaler Ordner und eingehängter externer Datenträger
- Filter nach Dateiname und Dateigruppe
- Navigation eine Ebene höher und Aktualisieren
- Textvorschau bis 512 KiB
- Textkodierungen unter anderem UTF-8, UTF-16 und Windows-1252
- skalierte Bildvorschau
- PDF-Erstseitenvorschau über QtPdf
- Audio-/Video-Erkennung ohne zusätzlichen internen Player
- Datei extern öffnen
- übergeordneten Ordner öffnen
- Pfad kopieren
- virtuelle Markierungen
- Zuordnung zu virtuellen Sammlungen
- sichere Behandlung symbolischer Verknüpfungen
- Benutzer-Mounts unter /run/media gezielt unterstützt

## Bedienoberfläche

Jeder Hauptbereich besitzt eine eigene Akzentfarbe bei einheitlicher dunkler Grundgestaltung:

- Übersicht: Cyan
- Textsuche: Blau
- Ergebnisse: Hellblau
- Duplikate: Rot/Rosa
- Sammlungen: Violett
- Dateien & Vorschau: Orange/Gold
- Journal: Grün
- Hilfe: helles Blau/Violett

Informationen werden weiterhin nicht ausschließlich durch Farbe vermittelt.

## Sicherheitsmodell

PROVOWARE DUPLIKATE-FINDER 2026 bleibt ein Nur-Lesen-Werkzeug für Originaldateien.

Weiterhin gesperrt:

- Löschen
- Verschieben
- Umbenennen
- Überschreiben
- Quarantäne

Symbolische Verknüpfungen werden im Dateibrowser nicht automatisch geöffnet oder verfolgt. Der Systembereich /run bleibt gesperrt; nur der eng begrenzte Benutzer-Mountpfad /run/media/<Benutzer>/<Datenträger> ist für externe Datenträger zugelassen.

## Qualitätsnachweise

Der finale v0.8.0-Stand wurde erfolgreich geprüft mit:

- Kern- und Sicherheitstests
- 800×600-Basisprofil
- Oberfläche bei 100 %
- Oberfläche bei 150 %
- Oberfläche bei 200 %
- autonomer Gesamt-Abnahme
- Portable-Lite-/Recovery-Abnahme
- Funktionsgleichheit von Lite und Recovery
- GUI-Start
- Konsolenstart
- Entwicklungs-Vollpaket auf main

Der Bedienoberflächen-/Prozessbereich wurde anschließend wieder auf **FROZEN** gesetzt.

## Paketgrößen

Gemessener v0.8.0-Stand:

| Paket | Größe |
| --- | ---: |
| Recovery entpackt | 985,7 MiB |
| Lite entpackt | 733,0 MiB |
| Einsparung Lite | 252,7 MiB / 25,64 % |
| Lite tar.gz | ca. 274 MB |
| Lite ZIP | ca. 310 MB |
| Recovery tar.gz | ca. 520 MB |

Die Python-/Qt-Laufzeit wurde bewusst nicht aggressiv beschnitten.

## Pakete

Der Release stellt bereit:

- Portable Lite als tar.gz
- Portable Lite als ZIP
- Portable Recovery als tar.gz
- SHA-256-Prüfsummen
- Build-/Abnahmenachweise

## Hinweise

Audio und Video bleiben in v0.8.0 bewusst ohne internen Player. Damit werden zusätzliche Codec-, Backend- und Paketabhängigkeiten vermieden.

Ein AppImage wird separat als Prototyp untersucht und gehört nicht zum stabilen v0.8.0-Funktionsumfang.

## Links

- Repository: https://github.com/provoware/DUPLIKATE-FINDER2026
- Releases: https://github.com/provoware/DUPLIKATE-FINDER2026/releases
- Probleme und Verbesserungsvorschläge: https://github.com/provoware/DUPLIKATE-FINDER2026/issues
- Sicherheitsinformationen: https://github.com/provoware/DUPLIKATE-FINDER2026/blob/main/SECURITY.md
- Änderungsprotokoll: https://github.com/provoware/DUPLIKATE-FINDER2026/blob/main/CHANGELOG.md
