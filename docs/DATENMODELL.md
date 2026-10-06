# Datenmodell

## `files`
Technische Dateiinformationen für spätere Indexierung: Pfad, Größe, Änderungszeit, optionale SHA-256-Prüfsumme.

## `search_jobs` / `search_hits`
Vorbereitet für dauerhaft gespeicherte Suchläufe und Treffer.

## `duplicate_groups`
Eine Gruppe wird durch SHA-256 und Dateigröße beschrieben.

## `duplicate_members`
Ordnet Dateipfade einer Duplikatgruppe zu.

## `virtual_items`
Speichert nur virtuelle Nutzerdaten:

- Pfad
- Markierung ja/nein
- Notiz
- Aktualisierungszeit

## `collections`
Virtuelle Sammlungen mit Name und Beschreibung.

## `collection_items`
Ordnet einen Dateipfad einer Sammlung zu. Es findet keine Dateioperation statt.

## `feature_flags`
Vier spätere Dateiaktionen. In Version 1 zwingend:

```text
enabled = 0
locked  = 1
```

## `change_journal`
Schema für spätere physische Transaktionen. In Version 1 werden keine physischen Änderungen erzeugt.

## `app_state`
Enthält unter anderem:

- `safety_mode = read_only`
- `schema_version = 1`


## Ergänzung ab v0.7.0

Für skalierbare Scans existieren zusätzlich `scan_runs`, `scan_inventory` und `scan_errors`.
Das Inventar speichert Dateimetadaten und temporäre Prüfwerte pro Lauf. `files` dient als wiederverwendbarer SHA-256-Zwischenspeicher, dessen Treffer nur bei identischer Dateidentität verwendet werden.

Das Schema wird nicht mehr nur implizit erzeugt, sondern über `app/storage/migrations.py` versioniert weiterentwickelt. Die aktuelle Schema-Version steht in `app_state.schema_version`.
