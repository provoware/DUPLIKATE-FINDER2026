# Release-Agent

## Aufgabe

Erzeugt reproduzierbare, portable Linux-Pakete und prüft sie vor Veröffentlichung.

## Regeln

- eigene Laufzeit im Paket,
- Runtime-Download per SHA-256 verifizieren,
- PySide6 in die Paketlaufzeit installieren,
- Selbsttest mit genau dieser Laufzeit ausführen,
- kein `sudo`, kein System-Python-Fallback,
- Archiv + SHA-256 erzeugen,
- Release erst nach grünen Kern- und UI-Prüfungen.
