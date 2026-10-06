# Barrierefreiheit und Sichtbarkeit

## Ziel

Die Oberfläche soll auch ohne technische Vorkenntnisse und bei vergrößerter Schrift nutzbar bleiben.

## Regeln

- wichtige Hauptfunktionen erhalten sichtbare Textbeschriftungen,
- Status enthält Symbol **und** Text,
- Warnungen werden nicht nur durch Farbe dargestellt,
- längere Hinweise verwenden Wortumbruch,
- Bedienelemente besitzen keine absichtlich winzige Schrift,
- zentrale Ansichten verwenden klare Gruppen statt versteckter Menüs,
- Tabellen sind nur Ergebnisdarstellung, nicht einzige Bedienmöglichkeit.

## Automatische Prüfung

`tools/ui_scale_check.py` öffnet jede Hauptseite mit PySide6 im unsichtbaren Testmodus und prüft definierte kritische Elemente.

Geprüft wird bei:

- 100 %
- 150 %
- 200 %

Zusätzlich wird je Stufe ein Prüfbild als GitHub-Aktionsartefakt gespeichert.

## Grenze

Automatisierung ersetzt keine spätere menschliche Sichtprüfung. Sie verhindert jedoch früh grobe Regressionen wie verschwundene Hauptknöpfe oder übergroße Mindestlayouts.
