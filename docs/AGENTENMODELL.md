# Agentenmodell

## Grundsatz

Nur der **Operator-Agent** darf schreiben. Alle anderen Agenten lesen, prüfen, planen und protokollieren.

| Agent | Schreibrecht | Aufgabe |
|---|---:|---|
| Analyse | nein | Zustand, Risiko, Änderungsumfang |
| Testplanung | nein | minimale und vollständige Prüfmenge |
| Sicherheit | nein | Schutzvertrag |
| Operator | **ja** | gezielter Patch |
| Regression | nein | Vorher/Nachher |
| Fehlerlernen | nein | Fehler → Lösung → Regression |
| Dokumentation | nein | Vertrags- und Hilfesynchronität |

Die Trigger stehen maschinenlesbar in `manifest/agents.manifest.json`.

Jeder Agentenbericht trägt Zeitstempel, Eingabezustand, Ergebnis und Status. Agenten dürfen keine versteckten Nebenaufgaben beginnen.
