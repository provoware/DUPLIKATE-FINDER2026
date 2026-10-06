# Intelligentes Fehlermanagement

Jeder Fehler folgt demselben Vertrag:

1. sicher stoppen oder betroffenen Vorgang isolieren,
2. Fehler mit Zeitstempel protokollieren,
3. Fingerabdruck erzeugen,
4. Ursache bestimmen,
5. konkrete Lösung hinterlegen,
6. nach der Lösung denselben Fall erneut prüfen,
7. bei reproduzierbaren Fehlern einen Regressionstest ergänzen.

Ein Fehler ohne Lösung darf als `new` registriert werden, aber ein Release darf bekannte kritische `new`-Fehler nicht ignorieren.

Werkzeug:

```bash
python tools/error_catalog.py --area startup --message "..." --solution "..." --status resolved
```
