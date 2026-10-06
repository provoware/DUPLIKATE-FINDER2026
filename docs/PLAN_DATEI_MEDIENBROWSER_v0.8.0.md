# Planung v0.8.0 – Datei- und Medienübersicht

**Umsetzung gestartet:** 2026-10-06 · ausschließlich Nur-Lesen-Funktionen.

## Ziel

Ein eigener Nur-Lesen-Bereich soll Dateien übersichtlich nach Typ erfassen, filtern und direkt vorschauen, ohne den Dateimanager des Systems zu ersetzen und ohne Originaldateien zu verändern.

## Geplanter eigener Bereich

**Dateien & Vorschau**

Links:
- Ordner-/Datenträgerauswahl
- Dateityp-Filter
- Suche nach Dateiname
- Sortierung nach Name, Größe, Datum und Typ

Mitte:
- seitenweise Dateiliste
- Dateiname
- Typ
- Größe
- Änderungsdatum
- Pfad

Rechts:
- große Vorschau
- wichtigste Metadaten
- Schaltfläche „Im System-Dateimanager zeigen“
- Schaltfläche „Mit Standardprogramm öffnen“

## Dateigruppen

### Text und strukturierte Dokumente
Erste Stufe:
- txt, md, csv, log
- json, xml, yaml, yml
- ini, conf
- py, sh
- toml, rst, sql, html, css, js, ts

Vorschau:
- reiner Text
- begrenzte Vorschaugröße
- verständliche Meldung bei unbekannter Zeichenkodierung

### Bilder
Geplant:
- png, jpg, jpeg, webp, bmp, gif, tif, tiff

Vorschau:
- skalierte Bildansicht
- Breite × Höhe
- Dateigröße
- keine Änderung der Bilddatei

### PDF
Geplant:
- PDF-Erkennung
- erste Seite bzw. ausgewählte Seite als Vorschau
- Seitenzahl
- Textvorschau, sofern sicher lesbar

### Video
Geplant:
- mp4, mkv, webm, avi, mov und weitere vom System unterstützte Formate

Erste sichere Stufe:
- Dateimetadaten
- Vorschaubild, wenn ohne zusätzliche schwere Laufzeit möglich
- Öffnen mit Standardprogramm

Eine vollständige Videowiedergabe innerhalb von PROVOWARE ist **nicht** Voraussetzung der ersten Stufe, weil dafür Qt Multimedia und zusätzliche Codecs das Portable-Paket deutlich vergrößern können.

### Audio
Geplant:
- mp3, wav, flac, ogg, m4a

Erste sichere Stufe:
- Metadaten
- Öffnen mit Standardprogramm
- interne Wiedergabe erst nach eigener Größen-/Abhängigkeitsanalyse

## Externe Datenträger

Linux bindet USB-Sticks, USB-Festplatten und andere Datenträger typischerweise unter Benutzerpfaden wie `/media/...` oder `/run/media/...` ein. Diese normalen eingehängten Benutzerpfade können wie andere Ordner ausgewählt werden, solange die zentrale Sicherheitsrichtlinie sie nicht sperrt.

## Dateimanager-Funktionen

Für v0.8.0 zunächst zulässig:
- Ordner auswählen
- Datei/Ordner anzeigen
- Pfad kopieren
- mit Standardprogramm öffnen
- im System-Dateimanager zeigen
- filtern
- sortieren
- Vorschau
- Metadaten lesen
- virtuelle Sammlung/Markierung

Weiterhin gesperrt:
- Löschen
- Verschieben
- Umbenennen
- Überschreiben
- Quarantäne
- automatisches Bearbeiten

## Architektur

Der Medienbrowser erhält einen eigenen Kernbereich, statt die bestehende Textsuche mit immer mehr Sonderfällen zu überladen:

- `app/file_browser/` – Dateiklassifikation und Metadaten
- `app/preview/` – Nur-Lesen-Vorschauadapter
- GUI-Tab „Dateien & Vorschau“
- SQLite-seitenweise Inventarisierung für große Bestände

Jeder Vorschauadapter muss fehlschlagen dürfen, ohne den restlichen Browser zu blockieren.

## Reihenfolge

1. allgemeine Dateiliste + Dateitypklassifikation + System-Öffnen
2. Text- und Bildvorschau
3. PDF-Vorschau
4. Video-/Audio-Metadaten und externe Wiedergabe
5. erst danach prüfen, ob interne Multimedia-Wiedergabe den zusätzlichen Paketumfang rechtfertigt
