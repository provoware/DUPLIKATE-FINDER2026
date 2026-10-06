# AGENTS.md – verbindlicher Entwicklungsvertrag

Dieses Dokument gilt für alle KI- und Automationsagenten, die an diesem Repository arbeiten.

## 1. Oberstes Ziel

Robustes, laienfreundliches Linux-Werkzeug für Textsuche, Duplikatprüfung und virtuelle Organisation – mit maximalem Schutz der Originaldateien.

## 2. Unverhandelbare Regeln

1. **Kein Tkinter.** GUI ausschließlich PySide6/Qt.
2. **Keine physischen Änderungen an Originaldateien im aktuellen Sicherheitsstand.**
3. Keine direkten Lösch-, Verschiebe-, Umbenenn- oder Ersetz-APIs im Anwendungscode.
4. Kritische Linux-Systembereiche bleiben gesperrt.
5. Symlinks werden standardmäßig nicht verfolgt.
6. Duplikate benötigen vollständige SHA-256-Gleichheit.
7. Start darf kein `sudo`, keine Systempaketinstallation und keinen System-Python-Fallback verwenden.
8. Schreibfunktionen im Dashboard bleiben sichtbar, `disabled`, `enabled=0`, `locked=1`.
9. Änderungen müssen mit Tests abgesichert werden.
10. Vertragsänderungen müssen gleichzeitig in den passenden Dokumenten aktualisiert werden.

## 3. Architekturgrenzen

- `app/core`: Fachlogik, keine GUI.
- `app/safety`: einzige Quelle für Schutzentscheidungen.
- `app/storage`: SQLite und persistente virtuelle Daten.
- `app/gui`: Darstellung und Benutzerinteraktion; keine Dateischreiblogik.
- `app/startup`: Selbsttest.
- `tools`: Prüf- und Bauwerkzeuge, nicht Anwendungslaufzeit.

## 4. Bedienregeln

- Deutsch und laienverständlich.
- Hauptaktionen sichtbar beschriften.
- Status immer mit Text, nicht nur Farbe.
- 100/150/200-%-Prüfung nicht umgehen.
- keine wichtige Hauptfunktion nur in Kontextmenüs verstecken.

## 5. Pflichtprüfung vor Abschluss

```bash
python -m compileall -q app tests tools
python -m pytest
```

Mit PySide6 zusätzlich:

```bash
QT_QPA_PLATFORM=offscreen python tools/ui_scale_check.py --zoom 100 --output artifacts/ui-100.png
QT_QPA_PLATFORM=offscreen python tools/ui_scale_check.py --zoom 150 --output artifacts/ui-150.png
QT_QPA_PLATFORM=offscreen python tools/ui_scale_check.py --zoom 200 --output artifacts/ui-200.png
```

## 6. Agentenrouting

Für spezialisierte Arbeiten gelten zusätzlich:

- `agents/ARCHITEKTUR_AGENT.md`
- `agents/SICHERHEITS_AGENT.md`
- `agents/GUI_AGENT.md`
- `agents/DATEN_AGENT.md`
- `agents/RELEASE_AGENT.md`

Bei Konflikt gilt die strengere Sicherheitsregel.

## 7. Autonome Abnahme und Startup

Zusätzlich gelten:
- agents/ABNAHME_AGENT.md
- agents/STARTUP_AGENT.md

Pflichtabnahme:

    python tools/autonomous_acceptance.py --output artifacts/abnahme

Die erste Pflichtgröße ist 800 × 600. Danach folgen weitere Größen und 150/200-%-Prüfungen.
Der HTML-Rasterbericht ist Teil der Abnahme.

GUI und Konsole müssen dieselben Kern- und Sicherheitsregeln verwenden.

## 8. Ein-Schreibagent-Vertrag

Maschinenlesbar gilt `manifest/agents.manifest.json`.

- Analyse, Testplanung, Sicherheit, Regression, Fehlerlernen und Dokumentation sind **nur lesend**.
- Nur `operator` darf Dateien ändern.
- Vor einem Patch wird der aktuelle Zustand erfasst.
- Nach einem Patch werden gezielte Prüfungen ausgeführt.
- Vor Merge bleibt die vollständige Regression Pflicht.
- Jeder neue reproduzierbare Fehler erzeugt eine Lösung und einen Regressionstest-Vorschlag.


## Freeze – Bedienoberfläche / Prozesssteuerung

Seit v0.6.0 ist der Bereich **Bedienoberfläche / Prozesssteuerung = FROZEN**. Er wurde am 2026-10-06 auf ausdrücklichen Nutzerauftrag aus dem Stand v0.5.1 wieder geöffnet und nach gezielten Korrekturen sowie vollständiger 800×600-/100/150/200-%-Abnahme erneut eingefroren. Der konkrete Verlauf ist in `manifest/project.manifest.json` und `docs/FREEZE_BEDIENUNG_PROZESS.md` festgehalten.

Ohne ausdrückliche Wiederöffnung keine neuen Komfortfunktionen, kosmetischen Umbauten oder neuen Prozesssteuerungsvarianten beginnen.

Ohne Wiederöffnung zulässig bleiben nur gezielte Sicherheitskorrekturen, reproduzierbare Regressionskorrekturen und zwingende Plattform-Kompatibilitätskorrekturen.

Betroffen sind insbesondere `app/gui/**`, `app/process_control.py`, `app/progress_format.py`, `app/resource_monitor.py`, `app/cpu_limit.py` und `app/settings_store.py`.

Eine Wiederöffnung erfordert Vorvalidierung, gezielte Tests und anschließend die vollständige 800×600-/100/150/200-%-Abnahme.
