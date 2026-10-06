# Sicherheit

## Unterstützter Stand

Aktuell befindet sich das Projekt in der read-only Phase `0.1.x`.

## Sicherheitsrelevante Fehler

Besonders kritisch sind Änderungen, durch die das Programm:

- Originaldateien schreiben, löschen, verschieben oder umbenennen kann,
- kritische Systempfade durchsuchen kann,
- symbolischen Verknüpfungen folgt,
- System-Python oder Systempakete ungefragt verwendet,
- Dateien nur aufgrund gleicher Größe als Duplikate einstuft.

Solche Änderungen dürfen nicht zusammengeführt werden, bevor der Sicherheitsvertrag ausdrücklich angepasst und separat abgenommen wurde.
