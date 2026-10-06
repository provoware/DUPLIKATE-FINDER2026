# PROVOWARE Entwicklungsstandard

## Effizienz

1. Datei- und Projektzustand per SHA-256 erfassen.
2. Unveränderte Zustände wiederverwenden.
3. Zuerst gezielte Prüfungen für betroffene Bereiche.
4. Vollständige Regression erst vor Freigabe – niemals weglassen.
5. Kleine Patches bevorzugen; keine kosmetischen Sammelumbauten neben Funktionsänderungen.
6. Downloads nur bei fehlendem oder geänderten Bestand.
7. GitHub-Caches nur für nicht vertrauliche Abhängigkeiten.

## Nachvollziehbarkeit

- Projektmanifest: `manifest/project.manifest.json`
- Agentenmanifest: `manifest/agents.manifest.json`
- globale Regeln: `standards/global-standard.json`
- lokaler Zustandsstand: `.provoware-state/development-state.json`
- Fehlerkatalog: `.provoware-state/error-catalog.jsonl`
- Checkpoints: `.provoware-state/checkpoints.jsonl`

## Konfiguration

JSON-Konfigurationen orientieren sich an JSON Schema Draft 2020-12. Vorlagen liegen in `templates/`.

## Sprache

Nutzertexte: kurze Sätze, klares Deutsch, keine unerklärten Abkürzungen. Status nie nur farblich darstellen.
