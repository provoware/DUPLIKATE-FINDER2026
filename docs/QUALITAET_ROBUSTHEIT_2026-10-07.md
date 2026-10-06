# Qualitäts- und Robustheitsprüfung · 2026-10-07

## Anlass

Gezielte Wiederöffnung der eingefrorenen Bereiche „Bedienoberfläche / Prozesssteuerung“
und „Robustheit / Skalierung“ nach ausdrücklichem Nutzerauftrag. Ziel ist kein Redesign,
sondern die Beseitigung messbarer Kontrast-, Robustheits- und Wartbarkeitsprobleme.

## Visuelle Befunde

- Fortschrittsbalken: weiße Schrift auf sehr hellem Cyan lag nur bei ungefähr 1,79:1.
- Platzhaltertexte waren im dunklen Eingabefeld visuell zu schwach.
- Tabellen und Listen hatten keinen gleich deutlichen Tastatur-Fokus wie Schaltflächen.
- Statusfarben lagen teilweise als Inline-Stile in `UiEnhancements` statt zentral im Theme.

## Änderungen

- Fortschrittsfüllung dunkler gesetzt; Weiß auf Füllung liegt jetzt über 4,5:1.
- Platzhalterfarbe explizit über die Qt-Palette gesetzt.
- Fokusrahmen für Tabellen und Listen ergänzt.
- Tabellen-Hoverzustand ergänzt.
- Statusfarben über `statusLevel` zentral im Theme definiert.
- Kritische Farbrollen in `design_tokens.py` zentralisiert.
- Automatische WCAG-AA-Kontrasttests für kritische Farbpaare ergänzt.

## Robustheit

- Textsuche liest sehr lange physische Zeilen in begrenzten 256-KiB-Blöcken.
- Suchbegriffe über einer Blockgrenze bleiben durch Überlappung auffindbar.
- Vor dem Lesen eines inventarisierten Textes wird geprüft, ob sich die Datei seit der
  Inventarisierung verändert hat.
- Sammlungsfehler unterscheiden leeren Namen, doppelten Namen und Datenbankfehler.
- Import-/Export-Ausnahmen werden zusätzlich vollständig protokolliert.
- TestSandbox nutzt keine automatische Löschung mehr, wenn ihre Sicherheitsmarkierung
  fehlt.

## Bewusste Nicht-Änderungen

- Keine neue MainWindow-/Controller-Zerlegung.
- Kein Umbau der Navigation oder Seitenstruktur.
- Keine Änderung an Duplikat-Hashing, SQLite-Schema oder Nur-Lesen-Sicherheitsmodell.
- Breite Ausnahmebehandlung bleibt ausschließlich an bewussten Sicherheitsgrenzen
  wie Worker-Threads und Import/Export-UI erhalten, damit Hintergrundfehler die GUI
  nicht unkontrolliert beenden; dort werden Fehler protokolliert.

## Wiedereinfrierung

Nach vollständigen Kern-, Sicherheits-, UI-100/150/200-%-, autonomen, AppImage- und
Portable-Prüfungen werden die beiden Bereiche wieder als FROZEN behandelt.
