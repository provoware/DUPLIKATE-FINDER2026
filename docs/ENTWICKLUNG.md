# Entwicklung

## Lokale Einrichtung

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m pytest
```

Danach:

```bash
./ENTWICKLUNG_STARTEN.sh
```

## Arbeitsregel

Änderungen erfolgen auf einem eigenen Zweig und über einen Änderungsantrag. `main` ist der freigegebene Stand.

## Pflicht vor Zusammenführung

- Tests grün
- Python-Kompilierung grün
- Oberflächenprüfungen 100/150/200 % grün
- Sicherheitsvertrag unverletzt
- Dokumentation bei Vertragsänderungen aktualisiert

## Keine Systemänderungen

Entwicklungsabhängigkeiten gehören in `.venv`. Release-Abhängigkeiten gehören in `runtime/`. Das Hauptsystem wird nicht verändert.
