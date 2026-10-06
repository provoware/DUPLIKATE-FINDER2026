# Freeze-Vertrag – Bedienoberfläche / Prozesssteuerung

**Status:** FROZEN
**Seit:** v0.6.0
**Datum:** 2026-10-06

## Wiederöffnung und erneute Einfrierung

Der Bereich wurde am 2026-10-06 aus v0.5.1 auf ausdrücklichen Nutzerauftrag geöffnet. Anlass waren überfüllte Informationskarten, Ersatzzeichen statt Symbolen und ein zu enges Layout. Nach der Überarbeitung und der vollständigen autonomen Abnahme mit 800×600 sowie 100/150/200 % wurde der Bereich für v0.6.0 erneut eingefroren.

## Eingefrorener Umfang

- Erscheinungsbild, Kontraste und Hauptaktionsdarstellung
- 800×600-Grundlayout sowie 100/150/200-%-Verhalten
- virtuelle Such-, Duplikat- und Sammlungslisten
- Pause, Fortsetzen und sicherer Abbruch
- Fortschritt, aktueller Schritt und Restzeit
- Dateien pro Sekunde und verarbeitete Datenmenge
- CPU-/RAM-/SWAP-Anzeige
- CPU-Kernbegrenzung
- Ausschlussdialoge und Filterdarstellung
- Autosave sowie Bedienung von Import/Export
- Strg+Mausrad-Zoom und Größenwahl

## Ohne Wiederöffnung erlaubt

Nur gezielte Sicherheitskorrekturen, reproduzierbare Regressionskorrekturen und zwingende Plattform-Kompatibilitätskorrekturen.

Keine neue Komfortfunktion und keine reine Kosmetik.

## Wiederöffnung

Eine bewusste Wiederöffnung erfordert:

1. ausdrückliche neue Aufgabenabgrenzung,
2. Vorvalidierung,
3. gezielte Regressionstests,
4. kleinen gezielten Patch,
5. vollständige 800×600-/100/150/200-%-Abnahme,
6. Nachvalidierung und erneute Freeze-Entscheidung.


## Kontrollierte Wiederöffnung für v0.7.1

Am 2026-10-06 wurde der Bereich auf ausdrücklichen Nutzerauftrag erneut begrenzt geöffnet. Umfang:

- bessere Toolführung auf der Übersicht,
- stärkere Farben und Kontraste,
- bessere Sichtbarkeit von Navigation, Status und Hauptaktionen,
- wartungsneutrales Zusammenführen doppelter UI-Hilfslogik.

Neue Fachfunktionen gehören nicht zu dieser Wiederöffnung. Vor dem Merge ist erneut die vollständige 800×600-/100/150/200-%-Abnahme erforderlich. Danach wird der Bereich wieder auf **FROZEN** gesetzt.


## Re-Freeze v0.7.1

Nach der begrenzten Wiederöffnung wurden erneut erfolgreich geprüft:

- Kern- und Sicherheitstests,
- Oberfläche 100 %,
- Oberfläche 150 %,
- Oberfläche 200 %,
- autonome Gesamt-Abnahme einschließlich 800×600.

Der Bereich **Bedienoberfläche / Prozesssteuerung ist damit für v0.7.1 wieder FROZEN 🟢**.


## Kontrollierte Wiederöffnung für v0.8.0

Am 2026-10-06 wurde der Bereich auf ausdrücklichen Nutzerauftrag erneut begrenzt geöffnet. Umfang:

- neuer Hauptbereich „Dateien & Vorschau“,
- unterschiedliche, kontrastreiche Akzentfarben je Hauptbereich,
- bessere Sichtbarkeit und Toolführung im neuen Datei-Browser,
- keine Freigabe physischer Dateiänderungen.

Vor dem Merge sind erneut 800×600 sowie 100/150/200 % und die autonome Gesamt-Abnahme Pflicht. Erst danach wird der Bereich wieder auf FROZEN gesetzt.


## Re-Freeze v0.8.0

Nach Umsetzung des modularen Datei-/Medienbrowsers und der bereichsspezifischen Akzentfarben wurden erneut erfolgreich geprüft:

- gezielte Entwicklungsprüfung,
- Kern- und Sicherheitstests,
- Basisprofil 800×600,
- Oberfläche 100 %, 150 % und 200 %,
- autonome Gesamt-Abnahme,
- Portable Lite/Recovery einschließlich Funktionsgleichheit.

Der Bereich **Bedienoberfläche / Prozesssteuerung ist damit für v0.8.0 wieder FROZEN 🟢**.


## Re-Freeze v0.9.0

Der Bereich wurde für die ausdrücklich beauftragte Laienoptimierung und Vorschau-Erweiterung erneut begrenzt geöffnet.

Nach Umsetzung wurden erfolgreich geprüft:

- gezielte Entwicklungsprüfung,
- Kern- und Sicherheitstests,
- 800 × 600,
- 100 %, 150 % und 200 %,
- autonome Gesamt-Abnahme,
- Portable Lite/Recovery einschließlich Funktionsgleichheit,
- AppImage-Bau auf Ubuntu 22.04,
- AppImage-Start auf Ubuntu 22.04 und 24.04,
- AppImage-Start aus simuliertem USB-Pfad mit Leerzeichen.

**Bedienoberfläche / Prozesssteuerung = FROZEN 🟢 ab v0.9.0.**

### Abschlusskorrekturen vor Veröffentlichung v0.9.0

Der Nutzerauftrag „vervollständige und verbessere bis zum release“ vom
2026-10-06 umfasst die Zusammenführung der vorbereiteten Dokumentvorschau
und begrenzte Robustheitskorrekturen. Der Dokumentfilter wird ergänzt;
veraltete PDF-Navigation bei Auswahl eines Symlinks wird ausgeblendet.
Vor Veröffentlichung erzwingt der Paketworkflow erneut die vollständige
Regression, autonome Abnahme und 100/150/200-%-Prüfung. Der bisherige
Freeze gilt nach diesen Abschlussprüfungen weiter.
