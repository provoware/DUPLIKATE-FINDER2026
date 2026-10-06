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
