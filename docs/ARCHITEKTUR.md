# Architektur

## Grundsatz

Die Anwendung trennt **Lesen**, **Analyse**, **virtuelle Organisation** und spätere **physische Änderungen** strikt.

```text
GUI
 │
 ├── Hintergrundarbeit ── Textsuche / Duplikatprüfung
 │                         │
 │                         └── Scanner + Sicherheitsrichtlinie
 │
 └── SQLite ── Markierungen / Notizen / Sammlungen / Prüfergebnisse

Originaldateien: nur lesen
```

## Schichten

### `app/core`
Reine fachliche Logik: Scanner, Textsuche, Hashing, Duplikatgruppen.

### `app/safety`
Zentrale Sicherheitsregeln. Andere Module dürfen Schutzentscheidungen nicht duplizieren oder umgehen.

### `app/storage`
SQLite-Schema und persistente virtuelle Daten.

### `app/gui`
PySide6-Darstellung. Lange Arbeiten laufen in Hintergrund-Threads, damit die Oberfläche bedienbar bleibt.

### `app/file_browser`
Modularer Nur-Lesen-Dateibrowser: Dateitypklassifikation, begrenzte Text-/Bild-/PDF-Vorschau und Qt-Dateisystemansicht. Der Browser besitzt keine physischen Schreibaktionen und nutzt die zentrale Sicherheitsrichtlinie.

### `app/startup`
Selbsttest vor Freigabe der Oberfläche.

## Verbotene Kopplungen

- GUI darf keine Dateien löschen/verschieben/umbenennen.
- Datenbank darf keine Originaldateien verändern.
- Scanner darf keine Schreiboperationen besitzen.
- Datei-Browser darf symbolische Verknüpfungen nicht automatisch verfolgen und keine Originaldateien verändern.
- Release-Start darf System-Python nicht als Ersatz verwenden.

## Erweiterungspfad

Schreibende Funktionen dürfen später nur über eine neue, isolierte Transaktionsschicht hinzukommen. Vorher sind Vorschau, Journal, Rückgängig, Vor-/Nachprüfung und eigene Tests Pflicht.
