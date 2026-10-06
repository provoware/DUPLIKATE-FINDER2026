# Sicherheit

## Unterstützter Stand

Aktuell wird der Nur-Lesen-Sicherheitsstand `0.8.0` vorbereitet. Physische Dateiänderungen bleiben weiterhin vollständig gesperrt.

## Sicherheitsrelevante Fehler

Besonders kritisch sind Änderungen, durch die das Programm:

- Originaldateien schreiben, löschen, verschieben oder umbenennen kann,
- kritische Systempfade durchsuchen kann,
- symbolischen Verknüpfungen folgt,
- System-Python oder Systempakete ungefragt verwendet,
- Dateien nur aufgrund gleicher Größe als Duplikate einstuft.

Solche Änderungen dürfen nicht zusammengeführt werden, bevor der Sicherheitsvertrag ausdrücklich angepasst und separat abgenommen wurde.


## Datei- und Medienbrowser

- Vorschauen lesen Originaldateien ausschließlich.
- Symbolische Verknüpfungen werden im Browser nicht automatisch geöffnet.
- Externe Datenträger unter normalen Benutzerpfaden sind zulässig.
- Unter `/run` bleibt nur der eng begrenzte Benutzer-Mountpfad `/run/media/<Benutzer>/<Datenträger>` zugelassen; der übrige Systembereich bleibt gesperrt.
- Externes Öffnen übergibt die Datei an das vom Linux-System konfigurierte Standardprogramm; PROVOWARE selbst verändert die Datei dabei nicht.
