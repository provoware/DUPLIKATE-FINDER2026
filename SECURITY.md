# Sicherheit

## Unterstützter Stand

Aktuell befindet sich das Projekt im freigegebenen Nur-Lesen-Sicherheitsstand `0.7.0`.

## Sicherheitsrelevante Fehler

Besonders kritisch sind Änderungen, durch die das Programm:

- Originaldateien schreiben, löschen, verschieben oder umbenennen kann,
- kritische Systempfade durchsuchen kann,
- symbolischen Verknüpfungen folgt,
- System-Python oder Systempakete ungefragt verwendet,
- Dateien nur aufgrund gleicher Größe als Duplikate einstuft.

Solche Änderungen dürfen nicht zusammengeführt werden, bevor der Sicherheitsvertrag ausdrücklich angepasst und separat abgenommen wurde.
