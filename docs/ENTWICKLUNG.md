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

## Autonome Gesamt-Abnahme

Vor einer Freigabe zusätzlich ausführen:

    QT_QPA_PLATFORM=offscreen python tools/autonomous_acceptance.py --output artifacts/abnahme

Der erzeugte HTML-Bericht ist Teil der Regressionsevidenz. Neue Funktionen müssen bestehende Testdateiverträge und UI-Profile bestehen.
