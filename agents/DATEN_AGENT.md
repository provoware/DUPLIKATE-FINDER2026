# Daten-Agent

## Aufgabe

Pflegt SQLite-Schema und virtuelle Organisationsdaten.

## Regeln

- Originaldateien sind keine Datenbankobjekte, die verändert werden dürfen.
- Migrationen müssen rückwärts nachvollziehbar dokumentiert werden.
- Fremdschlüssel aktivieren.
- Sammlungen, Notizen und Markierungen bleiben virtuelle Metadaten.
- `feature_flags` der Schreibfunktionen bleiben in v0.1.x gesperrt.
