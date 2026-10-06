# AGENTS.md – verbindlicher Entwicklungsvertrag

Dieses Dokument gilt für alle KI- und Automationsagenten, die an diesem Repository arbeiten.

## 1. Oberstes Ziel

Robustes, laienfreundliches Linux-Werkzeug für Textsuche, Duplikatprüfung und virtuelle Organisation – mit maximalem Schutz der Originaldateien.

## 2. Unverhandelbare Regeln

1. **Kein Tkinter.** GUI ausschließlich PySide6/Qt.
2. **Keine physischen Dateiänderungen in v0.1.x.**
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
