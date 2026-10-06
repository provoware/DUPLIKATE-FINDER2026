# Robustheit und Skalierung – v0.7.0

## Ziel

Dieser Entwicklungsblock verbessert ausschließlich Robustheit, Datenkonsistenz und Verhalten bei großen Datenmengen. Der Nur-Lesen-Vertrag für Originaldateien bleibt unverändert.

## Scan-Pipeline

Dateien werden nicht mehr für produktive Such- und Duplikatläufe vollständig in Python-Listen gesammelt. Stattdessen entsteht pro Lauf ein lokales SQLite-Inventar.

Für Duplikate gilt:

1. Metadaten inventarisieren.
2. Gleiche Dateigrößen bestimmen.
3. Kurze Inhaltsprobe als reinen Vorfilter berechnen.
4. Nur verbleibende Kandidaten vollständig mit SHA-256 prüfen.
5. Vor und nach jedem Inhaltslesen die Dateidentität kontrollieren.
6. Nur vollständige identische SHA-256-Prüfsummen als Duplikate speichern.

Die kurze Inhaltsprobe entscheidet niemals über die Gleichheit zweier Dateien.

## Dateistabilität

Ein Inventareintrag enthält:

- Pfad
- Größe
- Änderungszeit in Nanosekunden
- Gerät
- Inode

Ändert sich eine dieser verfügbaren Eigenschaften zwischen Inventarisierung und Inhaltsprüfung, wird das Ergebnis für diese Datei verworfen. Der Vorgang läuft mit den übrigen Dateien weiter und meldet die übersprungene Datei.

## Fehlertransparenz

Nicht lesbare, verschwundene oder während des Scans veränderte Dateien werden in `scan_errors` protokolliert. Die Oberfläche zeigt nach Abschluss die Anzahl übersprungener Dateien.

## SHA-256-Zwischenspeicher

Ein vollständiger Hash wird nur wiederverwendet, wenn Pfad, Größe, Änderungszeit, Gerät und Inode weiterhin zum gespeicherten Zustand passen. Andernfalls wird neu geprüft.

## Datenbankmigrationen

Das Datenbankschema besitzt eine explizite Versionsnummer. Änderungen werden als geordnete Migrationen ausgeführt. Jede Migration läuft innerhalb eines SQLite-Sicherungspunkts und wird bei Fehlern zurückgerollt.

## Atomare Zustandsdateien

Einstellungen und JSON-Exporte werden zuerst in eine temporäre Datei geschrieben, auf den Datenträger synchronisiert und danach atomar an die Zielstelle gesetzt. Dadurch wird das Risiko halb geschriebener JSON-Dateien deutlich reduziert.

Beschädigte Einstellungen werden vor der Rückkehr auf Standardwerte als Diagnosekopie gesichert.

## Import

Importdaten werden strukturell vorgeprüft. Die Übernahme virtueller Sammlungen und Markierungen läuft innerhalb einer Datenbanktransaktion. Auch die Nachprüfung findet vor dem endgültigen Commit statt.

## Großlisten

Folgende Ansichten laden produktiv nur kleine Seiten aus SQLite:

- Suchtreffer
- Sammlungseinträge
- Mitglieder einer Duplikatgruppe

Der Standardpuffer umfasst 200 Zeilen pro Seite und höchstens acht Seiten je Modell.

## Aufbewahrung

Historische Such- und Scanläufe werden begrenzt aufbewahrt, damit die lokale Datenbank bei regelmäßiger Nutzung nicht unbegrenzt durch technische Zwischenstände wächst.

## Sicherheitsgrenze

Diese Änderungen geben keine physische Dateiaktion frei. Löschen, Verschieben, Umbenennen und Quarantäne bleiben gesperrt.
