# Refactoring-Grenze der Hauptoberfläche

Stand: 2026-10-07

## Ziel

Die Hauptklasse `MainWindow` wurde schrittweise von Ablauf- und Zustandslogik entlastet, ohne das eingefrorene Erscheinungsbild oder den Bedienvertrag zu verändern.

Ausgelagert sind jetzt:

- Prozesssteuerung
- Textsuche
- Duplikatprüfung
- virtuelle Sammlungen
- Ergebnis-/Markierungslogik
- gemeinsame Suchordner-Auswahl
- zentrale Navigation
- gemeinsam genutzte Scan-UI-Helfer

## Bewusste Grenze

Die Methoden zum Aufbau der einzelnen Seiten bleiben in `MainWindow`.

Grund:

- Sie erzeugen überwiegend Widgets und Layouts.
- Die Widgets werden von mehreren Controllern über die bestehende Fensterinstanz angesprochen.
- Eine weitere Auslagerung würde viele UI-Referenzen und Übergabeobjekte erzeugen.
- Dadurch würde die Kopplung steigen, obwohl die Datei kleiner würde.
- Es gibt aktuell keine echte Mehrfachverwendung dieser Seitenaufbau-Logik.

Damit gilt für den aktuellen Stand:

**Keine weitere Aufteilung von `MainWindow` nur zur Dateiverkleinerung.**

Neue Auslagerungen sind erst wieder sinnvoll, wenn eine Verantwortung mehrfach verwendet wird, separat getestet werden muss oder eigenständig wachsen würde.
