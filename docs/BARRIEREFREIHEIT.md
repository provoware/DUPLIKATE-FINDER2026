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
- bei schmalen Fenstern ersetzt eine beschriftete Bereichsauswahl die Seitenleiste; beide Wege bleiben synchron,
- Statuskarten trennen Überschrift und Messwert und ordnen sich bei starker Vergrößerung neu,
- Statusmeldungen verwenden eindeutige Wörter wie „OK“, „Hinweis“ und „Fehler“; Farbe dient nur als Zusatz,
- Standardzeichen statt Schrift-Symbole halten Beschriftungen auch ohne Emoji-Schrift vollständig lesbar,
- Fokusrahmen sind per Tastatur sichtbar und Kontrollkästchen auch im gesperrten Zustand klar erkennbar.
- jeder Hauptbereich besitzt eine eigene Akzentfarbe; Überschriften, Beschriftungen und Fokuszustände bleiben zusätzlich textlich eindeutig,
- die neue Datei-Vorschau zeigt Metadaten als auswählbaren Text und bietet für nicht darstellbare Formate eine verständliche Textmeldung,
- Textvorschauen sind begrenzt, damit sehr große Dateien die Oberfläche nicht blockieren.
- Browseraktionen besitzen kurze sichtbare Beschriftungen und zusätzliche erklärende Tooltips,
- die Bedienfolge „Ordner wählen → Datei anklicken → Vorschau rechts“ ist direkt im Bereich sichtbar,
- PDF-Navigation zeigt aktuelle Seite und Gesamtseitenzahl zusätzlich als Text,
- fehlende Medien-Metadaten werden als verständlicher Hinweis statt als technischer Fehler dargestellt.

## Automatische Prüfung

`tools/ui_scale_check.py` öffnet jede Hauptseite mit PySide6 im unsichtbaren Testmodus und prüft definierte kritische Elemente.

`tools/autonomous_acceptance.py` prüft zusätzlich, ob die Bereichsauswahl je Fensterbreite passend erscheint und ob die Auswahl in beiden Navigationsansichten synchron bleibt. Das Prüfraster zeigt alle Hauptseiten in den geprüften Größen.

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
