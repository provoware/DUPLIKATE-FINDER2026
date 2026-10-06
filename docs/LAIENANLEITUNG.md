# Laienanleitung – PROVOWARE DUPLIKATE-FINDER 2026

## Normaler Start

Beim offiziellen Vollpaket:

1. Paket entpacken.
2. `STARTEN.desktop` doppelt anklicken.
3. Falls Linux nach Vertrauen fragt: „Ausführbar machen“ bzw. „Starten“ bestätigen.
4. Die Startprüfung läuft automatisch.
5. Danach öffnet sich das Werkzeug.

Es sind keine Python-Befehle nötig.

## Entwicklungs-Vollpaket

Doppelklick auf `ENTWICKLUNG_STARTEN.desktop` oder:

```bash
./ENTWICKLUNG_STARTEN.sh
```

Das Werkzeug prüft Python, Qt, Pakete, Speicher, Schreibrechte und Systemzustand selbst.

## Ampel

- 🟢 **Grün:** bereit oder erfolgreich.
- 🟡 **Gelb:** Prüfung läuft oder Eingabe wird benötigt.
- 🔴 **Rot:** Vorgang wurde sicher gestoppt.

Neben der Farbe steht immer Text.

## Projektordner

Standard:

```text
~/PROVOWARE/DUPLIKATE-FINDER-2026/
```

Fehlt er, wird er automatisch erstellt. Dort liegen nur PROVOWARE-Arbeitsdaten, Protokolle, Berichte und virtuelle Daten.

## Hilfe in drei Stufen

1. kurze Erklärung direkt im Bereich,
2. Tooltip beim Überfahren eines Bedienelements,
3. ausführliche Hilfeseite im Werkzeug.

## Bei einem Fehler

Die Anwendung stoppt den betroffenen Vorgang sicher und zeigt eine Lösung an. Zusätzlich wird der Fehler mit Zeitstempel und Fingerabdruck protokolliert.

Originaldateien bleiben im aktuellen Sicherheitsstand unverändert.


## Prozesssteuerung ab 0.3.1

Laufende Suche und Duplikatprüfung können mit **Pause** angehalten, mit **Fortsetzen** weitergeführt und mit **Abbrechen** sauber beendet werden.

Der untere Statusbereich zeigt:
- aktuellen Schritt,
- Prozentfortschritt,
- grobe Restzeit,
- Anzahl verarbeiteter Dateien.

## Ausschlüsse

Mit **Dateitypen auswählen** lassen sich häufige Typen per Ankreuzen auslassen. Python-/Entwicklungsordner wie `.venv`, `__pycache__`, `.git`, `build` und `dist` werden standardmäßig ausgelassen.

## CPU-Kerne

Im Dashboard kann festgelegt werden, wie viele Prozessorkerne PROVOWARE benutzen darf. Das verändert nicht die Systemeinstellungen des Rechners.

## Autosave / Import / Export

Einstellungen werden alle fünf Minuten automatisch gespeichert. Virtuelle Sammlungen und Markierungen werden ohnehin direkt in der lokalen Datenbank gespeichert.

**Zustand exportieren** sichert Einstellungen und virtuelle Organisation als JSON-Datei. Originaldateien werden nicht kopiert.

**Zustand importieren** prüft die Datei vor und nach der Übernahme. Originaldateien bleiben unverändert.


## Dateien ansehen – ohne etwas zu verändern

Öffne den Bereich **„Dateien & Vorschau“**.

1. Klicke auf **Ordner wählen**.
2. Wähle einen normalen Ordner oder einen eingehängten USB-Datenträger.
3. Klicke einmal auf eine Datei.
4. Rechts erscheint die Vorschau oder eine verständliche Information zum Dateityp.

Du kannst die Liste über das Suchfeld nach Dateinamen filtern. Daneben lässt sich auswählen, ob nur Text, Bilder, PDF, Dokumente, Audio, Video oder andere Dateien gezeigt werden sollen.

### Was kann direkt angezeigt werden?

- Textdateien
- DOCX-Dokumente als Textvorschau
- ODT-Dokumente als Textvorschau
- Bilder
- PDF-Dateien
- PDF-Seiten können mit **← Seite** und **Seite →** durchgeblättert werden

Bei Bildern werden zusätzlich Originalgröße, Bildformat und Seitenverhältnis angezeigt.

Bei Audio und Video zeigt PROVOWARE verfügbare technische Angaben wie Dauer, Format, Bildgröße oder Tonkanäle. Fehlen auf dem Linux-System die dafür nötigen Analysefunktionen, funktioniert das Werkzeug trotzdem weiter.

### Was bedeuten die Knöpfe?

- **Öffnen:** Datei mit dem normalen Linux-Standardprogramm öffnen.
- **Ordner:** Speicherort im Dateimanager öffnen.
- **Pfad kopieren:** vollständigen Speicherpfad kopieren.
- **Markieren:** Datei nur innerhalb von PROVOWARE kennzeichnen.
- **Zu Sammlung:** Datei einer virtuellen Sammlung zuordnen.

**Keiner dieser Knöpfe löscht, verschiebt, benennt um oder überschreibt die Originaldatei.**

## PDF durchblättern

Wird eine PDF-Datei ausgewählt, zeigt PROVOWARE die aktuelle Seite und die Gesamtzahl an, zum Beispiel:

`Seite 2 / 14`

Mit den beiden Seitenknöpfen kann vor- und zurückgeblättert werden. Die PDF-Datei selbst wird dabei nicht verändert.

## Wenn keine Vorschau erscheint

Das ist nicht automatisch ein Fehler.

Mögliche Gründe:

- das Dateiformat besitzt noch keine interne Vorschau,
- die Datei ist beschädigt,
- eine optionale Linux-Medienanalyse ist nicht vorhanden,
- es handelt sich um eine symbolische Verknüpfung, die aus Sicherheitsgründen nicht automatisch geöffnet wird.

In diesen Fällen kann die Datei – sofern sicher zulässig – über **Öffnen** an das Linux-Standardprogramm übergeben werden.
