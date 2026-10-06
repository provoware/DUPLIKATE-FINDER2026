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


## Dateien & Vorschau ab v0.9.0

Der Bereich **Dateien & Vorschau** ist zum Anschauen und virtuellen Organisieren gedacht.

1. **Ordner wählen** anklicken.
2. Gewünschten Ordner oder USB-Datenträger auswählen.
3. Eine Datei **einmal anklicken**. Rechts erscheint die Vorschau.
4. Einen Ordner **doppelt anklicken**, um hineinzuwechseln.

Die kurzen Knöpfe bedeuten:

- **Hoch:** einen Ordner nach oben wechseln.
- **Neu laden:** nur die Anzeige aktualisieren.
- **Öffnen:** Datei mit dem normalen Linux-Standardprogramm öffnen.
- **Ordner:** den zugehörigen Ordner im Linux-Dateimanager anzeigen.
- **Pfad kopieren:** vollständigen Dateipfad kopieren.
- **Markieren:** nur innerhalb von PROVOWARE markieren.
- **Zu Sammlung:** Datei virtuell einer Sammlung zuordnen; sie wird nicht verschoben.

### Was kann direkt angezeigt werden?

- Textdateien: Vorschau bis 512 KiB, zusätzlich Zeichencodierung sowie Zeilen-, Wort- und Zeichenzahl.
- JSON: wenn möglich eingerückt und leichter lesbar.
- Bilder: Vorschau plus Format, Pixelgröße, Megapixel und Seitenverhältnis.
- PDF: Seiten einzeln ansehen und mit **Vorherige Seite / Nächste Seite** blättern.
- WAV: zusätzlich Dauer, Kanäle, Abtastrate und Bit-Tiefe.
- andere Audio-/Videoformate: sichere Grunddaten; für vollständige Wiedergabe weiterhin das normale Linux-Programm verwenden.

## AppImage-Prototyp

Das AppImage ist in v0.9.0 zunächst **nur eine getestete Zusatzvariante**, nicht der normale empfohlene Download.

Der automatische Test prüft unter Ubuntu 22.04 und 24.04:
- Startfähigkeit,
- SHA-256-Prüfsumme,
- Paketgröße,
- Start aus einem simulierten USB-Pfad mit Leerzeichen.

Lite und Recovery bleiben die stabilen Paketformen, bis der AppImage-Prototyp vollständig freigegeben ist.
