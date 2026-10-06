# Autonomes Abnahmesystem

## Zweck

Jede relevante Änderung wird nicht nur mit Einzeltests, sondern mit einer mehrstufigen Abnahme geprüft.

## Prüfschichten

1. Kern- und Sicherheitstests – Suche, Duplikate, SQLite und Schutzregeln.
2. Reale Testdateien – feste positive und negative Kontrollfälle unter tests/fixtures/.
3. Startprüfung – interne Ordner, Datenbank, freier Speicher, Schutzvertrag und optionale GUI-Abhängigkeit.
4. Oberflächenprüfung – beginnt bei 800 × 600 und prüft danach weitere Größen sowie 150/200-%-Schrift.
5. Visueller Bericht – Screenshots jeder Hauptseite werden in einem HTML-Raster dargestellt.
6. Regressionsvertrag – fehlende Kernelemente, falsche Trefferzahlen, falsche Duplikatgruppen oder übergroße Mindestlayouts machen die Abnahme rot.

## Ausgabe

    python tools/autonomous_acceptance.py --output artifacts/abnahme

Erzeugt werden:
- artifacts/abnahme/index.html
- artifacts/abnahme/report.json
- Prüfbilder aller Hauptseiten

Die HTML-Datei benötigt keinen Server und kann lokal geöffnet werden.

## Freigaberegel

Kein Merge bei roter Abnahme. Ein visuell auffälliger, aber maschinell grüner Stand wird anhand des HTML-Rasters geprüft, bevor der betroffene UI-Bereich eingefroren wird.
