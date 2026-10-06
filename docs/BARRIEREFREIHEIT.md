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

## Erweiterte Pflichtprofile

Die visuelle Regression beginnt bei 800 × 600 mit 100 %.
Danach folgen 1024 × 768 sowie 150 % und 200 % auf größeren Prüfprofilen.

Die Oberfläche bietet zusätzlich:
- automatische Bildschirmgrößen-Erkennung,
- feste Größenprofile per Auswahlfeld,
- Zoomauswahl ohne Freitexteingabe,
- Strg + Mausrad als direkte Zoomsteuerung,
- moderne kontrastreiche Fokusrahmen und Statusflächen.

Das autonome Abnahmewerkzeug erzeugt zu jeder Hauptseite ein Prüfbild und fasst alle Bilder in einem HTML-Raster zusammen.


## Kontrast- und Listenstandard 0.4

- dunkler Hauptuntergrund mit heller Schrift,
- cyanfarbene Aktions- und Fokusrahmen,
- Warn-/Abbruchfarben zusätzlich immer mit Text,
- Tabellenkopf deutlich vom Inhalt getrennt,
- wechselnde Zeilenhintergründe,
- Mindestzeilenhöhe 34 px,
- Prozessstatus mit Text, Fortschrittsbalken und Restzeitanzeige,
- Pause und Abbruch als direkt sichtbare Tasten,
- keine kritische Prozesssteuerung nur über Farbe.
