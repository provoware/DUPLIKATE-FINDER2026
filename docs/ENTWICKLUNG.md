# Entwicklung

## Ein-Klick-Start

```bash
./ENTWICKLUNG_STARTEN.sh
```

Der Starter erkennt und repariert die lokale Entwicklungsumgebung selbst.

Er verwendet Python 3.12.15 aus dem Vollpaket oder lädt beim nackten GitHub-Quellcode genau diese geprüfte Laufzeit in `.provoware-dev/`. Das System-Python bleibt unverändert.

## Weitere Modi

```bash
./ENTWICKLUNG_STARTEN.sh --konsole
./ENTWICKLUNG_STARTEN.sh --nur-pruefen
./ENTWICKLUNG_STARTEN.sh --tests
./ENTWICKLUNG_STARTEN.sh --abnahme
```

## Automatisches Profil

Jeder Lauf erfasst Betriebssystem, Kernel, Architektur, CPU, RAM, SWAP, freien Speicher, Anzeigeart, Schreibrechte, Paketversionen, Qt und vorhandene Hilfsprogramme.

Ergebnisse:

- `.provoware-dev/systemprofil.json`
- `logs/ABHAENGIGKEITEN_AKTUELL.txt`
- `logs/ABHAENGIGKEITEN_AKTUELL.json`

## Kein Tk/Tkinter

Die GUI verwendet ausschließlich PySide6/Qt. Tkinter ist durch Architekturtests verboten.

## Keine Systemänderungen

Kein sudo, keine Änderung des System-Python und keine systemweite pip-Installation.

Siehe `docs/ABHAENGIGKEITEN.md`.
