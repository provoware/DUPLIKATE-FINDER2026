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

Auf Feature-Zweigen läuft zuerst die **gezielte Entwicklungsprüfung**. Sie leitet aus den geänderten Dateien die betroffenen Bereiche ab und vermeidet unnötige UI-/Gesamtprüfungen.

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

Downloads nur, wenn lokaler Bestand fehlt oder sein Fingerabdruck nicht mehr zum Vertrag passt. GitHub-Abhängigkeiten werden gecacht. Veraltete Workflow-Läufe werden abgebrochen.

## Oberfläche

Zentrale Maße stehen in `app/gui/design_tokens.py` und `standards/global-standard.json`.

Pflichtgrößen: 800×600 sowie 100/150/200-%-Prüfungen.

## Fehler

Jeder neue Fehler braucht eine konkrete Lösung. Reproduzierbare Fehler sollen einen Test erhalten.

## Sicherheit

Tk/Tkinter ist verboten. Originaldateien bleiben read-only. System-Python und Linux-Paketbestand werden zur Laufzeit nicht verändert.


## Prozesssteuerung 0.4

`app/core/control.py` enthält die gemeinsame kooperative Prozesssteuerung.

Regel:
- Pause nur an sicheren Prüfpunkten,
- Abbruch über ein Abbruchsignal,
- kein `terminate()` und kein gewaltsames Beenden eines QThread,
- Hashing prüft den Zustand blockweise,
- Textsuche prüft den Zustand datei-/zeilenweise,
- Restzeit ist eine Durchsatzschätzung.

`app/core/scanner.ScanOptions` ist die einzige Quelle für Scanfilter.

Die CPU-Begrenzung beeinflusst ausschließlich parallele SHA-256-Prüfungen.

## Persistenz 0.4

`app/settings.py` verwaltet versionierte Bedien-/Filtereinstellungen.

Alle fünf Minuten wird zusätzlich ein vollständiger PROVOWARE-Wiederherstellungsstand nach:

`recovery/autosave-state.json`

geschrieben.

Export/Import darf nur PROVOWARE-Zustände verändern. Originaldateien sind ausdrücklich außerhalb dieses Vertrags.

## Oberfläche 0.4

Der zentrale Stil liegt in `app/gui/theme.py`; globale Zielwerte zusätzlich in `standards/global-standard.json`.

Neue Aktionstasten verwenden denselben Neon-Rahmen. Warn- und Abbruchtasten besitzen eigene Eigenschaften statt lokale Einzel-Styles.
