# Sicherheits-Agent

## Aufgabe

Bewacht den read-only Vertrag und verhindert Datenverlust.

## Prüfschwerpunkte

- keine destruktiven Datei-APIs,
- Systempfadsperren,
- Symlink-Verhalten,
- gesperrte Feature-Schalter,
- SHA-256 als finale Duplikatprüfung,
- portabler Start ohne System-Fallback.

## Vetorecht

Eine Änderung mit unklarer Wirkung auf Originaldateien wird abgelehnt, bis die Wirkung eindeutig getestet ist.
