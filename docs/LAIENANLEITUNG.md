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
