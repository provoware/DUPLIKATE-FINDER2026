# Wartbarkeits-Hotspots nach dem MainWindow-Refactoring

Stand: 2026-10-07

## Eingefrorene Architektur

Die bestehende MainWindow-/Controller-Aufteilung gilt als eingefroren.

Keine weitere kosmetische Klassenzerlegung ist vorgesehen. Eine erneute Aufteilung ist nur sinnvoll, wenn mindestens einer dieser Punkte erfüllt ist:

- eine Verantwortung wird mehrfach verwendet,
- eine Verantwortung muss unabhängig getestet werden,
- eine Komponente wächst fachlich eigenständig,
- konkrete Kopplung oder Doppelcode werden reduziert.

## enhancements.py

Refaktoriert:

- Ressourcenanzeige in `ResourceDashboardController`
- Zustands-Import/-Export in `StatePortabilityController`

Bewusst zusammengeblieben:

- Zoom
- Fenstergröße
- CPU-Begrenzung
- Autosave
- Tabellen-/Listen-Konfiguration
- Ereignisfilter für Strg+Mausrad und Drag&Drop

Diese Bereiche teilen denselben UI-Zustand und dieselben Bedienelemente. Eine weitere Aufteilung würde aktuell mehr Übergaben erzeugen als Nutzen bringen.

## table_models.py

Refaktoriert:

Die drei virtuellen Tabellenmodelle verwenden jetzt einen gemeinsamen internen Seitenpuffer-Vertrag für:

- Seitengröße
- maximale Cache-Seiten
- Zeilenanzahl
- Spaltenanzahl
- Kopfzeilen
- LRU-Seitenpuffer
- gemeinsame Zeilenauflösung
- gemeinsamen Sortierzustand

Die fachspezifische Datenaufbereitung bleibt in den drei Modellen getrennt.

## file_browser/widget.py

Bewusst nicht weiter zerlegt.

Die Vorschau-Fachlogik liegt bereits in `app/file_browser/preview.py`. Die verbleibenden Methoden im Widget steuern unmittelbar Auswahl, Navigation, Buttons und aktuellen Dateizustand.

Eine zusätzliche Controller-Schicht würde aktuell dieselben Widget-Referenzen nur weiterreichen und keine echte Wiederverwendung erzeugen.

## cli.py

Refaktoriert:

GUI-Suchworker und Konsole verwenden jetzt dieselbe Kernfunktion `run_search_to_database()`.

Damit liegen Inventarisierung, Trefferpufferung, Scan-Fehler, Datenbankabschluss, Abbruchstatus und Aufräumen nicht mehr doppelt in GUI und Konsole.

## Stop-Regel

Weitere Refactorings in diesen Bereichen nur, wenn ein messbarer Wartbarkeitsgewinn vorliegt. Dateigröße allein ist kein Grund für zusätzliche Abstraktion.
