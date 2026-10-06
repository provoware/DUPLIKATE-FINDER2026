# Entwicklerhandbuch – PROVOWARE DUPLIKATE-FINDER 2026

## Einstieg

```bash
./ENTWICKLUNG_STARTEN.sh --schnelltest
```

führt zustandsbasierte Minimalprüfungen aus.

Vor Merge:

```bash
./ENTWICKLUNG_STARTEN.sh --tests
./ENTWICKLUNG_STARTEN.sh --abnahme
```

## Quellen der Wahrheit

- `manifest/project.manifest.json`
- `manifest/agents.manifest.json`
- `standards/global-standard.json`
- `dependencies.env`
- `pyproject.toml`
- `resources/texts/manifest.json`

## Zweistufige Prüfstrategie

Auf Arbeitszweigen läuft zuerst die **gezielte Entwicklungsprüfung**. Bei einem vorhandenen Git-Vergleich werden nur die geänderten Dateipfade ausgewertet; ein unnötiges erneutes Hashen des gesamten Projektbaums entfällt. Der einmal erzeugte Prüfplan wird anschließend direkt wiederverwendet.

Auf jedem Pull Request und auf `main` bleiben die vollständigen Kern-, 100/150/200-%- und autonomen Prüfungen Pflicht. Damit wird Geschwindigkeit nur während der Iteration optimiert, nicht bei der Freigabe.

## Arbeitsfolge

1. Zustandsregister erzeugen.
2. Analyse-Agent liest.
3. Testplaner bestimmt betroffene Prüfungen.
4. Operator patcht ausschließlich den geplanten Bereich.
5. Regressions-Agent vergleicht.
6. Fehlerlern-Agent registriert neue Fehler/Lösungen.
7. Vor Merge vollständige Regression.

## Zustandswerkzeuge

```bash
python tools/state_registry.py
python tools/agent_router.py --plan artifacts/pruefplan.json
python tools/targeted_checks.py
python tools/targeted_checks.py --full
```

## Patchregel

Keine Nebenrefaktorisierung. Gleiche Stelle bevorzugt einmal gezielt ändern. Unveränderte Dateien nicht neu schreiben.

## Netzwerkregel

Downloads nur, wenn lokaler Bestand fehlt oder sein Fingerabdruck nicht mehr zum Vertrag passt. Python-Laufzeit und Paketdateien werden in GitHub Actions gecacht. Versionen kommen zentral aus `dependencies.env`. Veraltete Workflow-Läufe werden abgebrochen und große Entwicklungs-Vollpakete nur bei relevanten Änderungen gebaut.

## Oberfläche

Zentrale Maße stehen in `app/gui/design_tokens.py` und `standards/global-standard.json`.

Pflichtgrößen: 800×600 sowie 100/150/200-%-Prüfungen.

## Fehler

Jeder neue Fehler braucht eine konkrete Lösung. Reproduzierbare Fehler sollen einen Test erhalten.

## Sicherheit

Tk/Tkinter ist verboten. Originaldateien bleiben read-only. System-Python und Linux-Paketbestand werden zur Laufzeit nicht verändert.


## Prozesssteuerung 0.3.1

Hintergrundarbeiten verwenden `ProcessControl` mit kooperativen Checkpoints. Gewaltsames Thread-Beenden ist verboten.

Scanner-Ausschlüsse werden zentral über `ScanOptions` definiert und dadurch von Textsuche und Duplikatprüfung gemeinsam verwendet.

Benutzereinstellungen liegen unter `config/benutzer-einstellungen.json`. Virtuelle Organisation bleibt in SQLite. Import/Export transportiert ausschließlich virtuelle Zustände und Einstellungen.

CPU-Affinität wird nur auf den laufenden PROVOWARE-Prozess bzw. dessen Threads angewendet.


## Leistungs-/Monitoring-Vertrag 0.5.0

Große Tabellen verwenden `QTableView` plus `QAbstractTableModel`. Das Erzeugen eines `QTableWidgetItem` pro Treffer ist für große Ergebnislisten verboten.

Suchtreffer, Sammlungsinhalte und Duplikatmitglieder werden SQLite-seitenweise geladen. Die Oberfläche hält nur einen begrenzten Seitenpuffer und nicht mehr den vollständigen Datenbestand im Arbeitsspeicher.

Der Ressourcenmonitor liest unter Linux `/proc` direkt und benötigt keine zusätzliche Laufzeitbibliothek. Angezeigt werden CPU-Verbrauch des PROVOWARE-Prozesses, RAM des Prozesses und SWAP-Nutzung.

Fortschrittsdaten umfassen Dateien pro Sekunde und verarbeitete Datenmenge. Wenn eine bekannte Gesamtdatenmenge vorhanden ist, wird die Restzeit bevorzugt nach Bytes statt nur nach Dateianzahl geschätzt.

Diese Regeln gehören zum Bedien-/Prozessbereich und dürfen nach dessen Freeze nur mit eigener Regression und ausdrücklicher Entsperrung verändert werden.
