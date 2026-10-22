# Vorrelease-Pflichtmatrix – 2026-10-23

Repository: provoware/DUPLIKATE-FINDER2026
Ausgangsstand main: e0f58a84e9f64a7d61a43757e21ca59c174b7da3
Branch: agent/20261023-search-terminal-state

## Maßnahme
Unerwartete Fehler bei der Textsuche dürfen den Auftrag nicht im Zustand RUNNING zurücklassen. Fehlerzustand FAILED wird gesetzt und Ausnahme weitergereicht. Zwei Regressionstests ergänzt. Originaldateien bleiben unangetastet.

## Pflichtmatrix (Soll / Ist / Nachweis / Status)
| Bereich | Soll | Ist / Nachweis | Status |
|---|---|---|---|
| Fachfunktionen | Suche, Duplikate, Sammlungen | README und Pflichtenheft vorhanden | OFFEN: Vollregression |
| Schnittstellen | GUI/Konsole konsistent | AGENTS.md verlangt gemeinsamen Sicherheitsvertrag | OFFEN |
| Datenverlustschutz | Originale nur lesen | Sicherheitsvertrag dokumentiert | OFFEN: Regression |
| Sicherheit | keine destruktiven APIs | Architekturregel vorhanden | OFFEN: Prüfung |
| Fehlerfälle | korrekte Terminalzustände | Codekorrektur + Regressionstests im Branch | OFFEN: Ausführung |
| Performance | große Datenmengen | Testlabor laut Commit-Historie vorhanden | OFFEN |
| Wartbarkeit | getrennte Kernlogik | app/core ohne Qt | TEILWEISE |
| Design/UX | verständlich | README, UI-Freeze | OFFEN: Abnahme |
| 800×600 / Skalierung | 100/150/200 % | automatisierte UI-Prüfung vorgesehen | OFFEN |
| Tastatur/Barrierefreiheit | Fokus, Beschriftung | Pflichtenheft | OFFEN |
| Import/Export | virtuelle Daten | README | OFFEN |
| Sicherung/Restore | Datenintegrität | noch kein Laufnachweis | OFFEN |
| Installation/Start | portabel, offline | README | OFFEN |
| Einheiten/Integration | pytest grün | Tests ergänzt | BLOCKED: hier keine Laufumgebung des Repos |
| End-to-End/GUI | automatisierte Abnahme | tools/autonomous_acceptance.py dokumentiert | OFFEN |
| Regression | Fehlerfälle abgesichert | tests/test_search_terminal_state.py | OFFEN: Ausführung |
| CI | alle Pflichtprüfungen grün | nach Commit noch nicht bestätigt | OFFEN |
| Dokumentation | Stand und Grenzen dokumentiert | dieses Protokoll | PASS: geschrieben |
| Paketierung | Lite/Recovery/AppImage | README v0.9.0 | OFFEN: Kandidatenprüfung |
| Branch-Schutz | main geschützt | Issue #2 offen | OFFEN |

## Ergebnis
PASS: GitHub-Branch und Quellcode-/Test-Commits gespeichert.
BLOCKED: Vollständige lokale pytest-, Qt- und Paketprüfungen nicht ausgeführt.
Keine Freigabe, kein Merge, kein Release.

## Nächste Pflichtarbeit
1. Quellcode syntaktisch und mit pytest vollständig prüfen; Fehler korrigieren.
2. GUI 800×600 bei 100/150/200 Prozent und autonome Abnahme ausführen.
3. CI auswerten, PR nur mit offenem Prüfstatus belassen und Branch-Schutz nach Issue #2 prüfen.
