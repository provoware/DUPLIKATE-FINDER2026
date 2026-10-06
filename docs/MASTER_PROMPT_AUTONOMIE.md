# PROVOWARE Master-Prompt – Autonome, laiengerechte Entwicklung

Version: 1.0.0

## Ziel

Entwickle PROVOWARE DUPLIKATE-FINDER 2026 so, dass Installation, Start, Prüfung, Fehlerbehandlung, Wartung und Weiterentwicklung für Laien weitgehend automatisch funktionieren, ohne das Hauptsystem unnötig zu verändern.

## Unverhandelbare Regeln

1. GUI ausschließlich PySide6/Qt. Kein Tk/Tkinter.
2. Klick-&-Start führt ohne technische Zwischenentscheidungen bis ins Werkzeug.
3. Der Standard-Projektordner wird automatisch geprüft und bei Bedarf sicher angelegt.
4. Originaldateien bleiben im aktuellen Sicherheitsstand unverändert.
5. Vor jeder Änderung: Ziel, betroffene Dateien, Risiken und minimale Prüfmenge bestimmen.
6. Nach jeder Änderung: gezielte Prüfung; vor Merge vollständige Regression.
7. Nur ein Operator darf schreiben. Analyse-, Planungs-, Sicherheits- und Regressionsagenten arbeiten lesend und protokollierend.
8. Jeder Fehler erhält Fehlerkennung, Ursache, Lösung, Wiederholungsprüfung und – wenn sinnvoll – einen neuen Regressionstest.
9. Änderungen bevorzugen kleine, gezielte Patches statt großflächiger Umbauten.
10. Netzwerkverkehr minimieren: lokale Bestände, Hashes und Caches wiederverwenden; unveränderte Zustände nicht erneut erzeugen.
11. Projektzustände, Abhängigkeiten, Manifeste, Checkpoints und Agentenläufe werden versioniert und mit Zeitstempel protokolliert.
12. Alle Nutzertexte sind einfaches, eindeutiges Deutsch. Kritische Informationen niemals nur über Farbe vermitteln.
13. Oberfläche nicht überladen: wenige Hauptaktionen, klare Bereiche, konsistente Abstände, gleiche Bedienelemente für gleiche Aufgaben.
14. Drei Hilfestufen: kurze Erklärung im Bereich, Tooltip am Element, ausführliche Hilfe mit Lösungsschritten.
15. Vor- und Nachvalidierung ist für zustandsändernde interne Vorgänge Pflicht.
16. Abbruch muss sicher sein. Temporäre Vorgänge dürfen keinen unklaren Zwischenzustand hinterlassen.

## Entwicklungsstrategie

- Zuerst Zustand erfassen und Hashvergleich durchführen.
- Nur betroffene Bereiche planen.
- Lesender Analyse-Agent erstellt Befund.
- Lesender Testplaner bestimmt Minimaltests und Pflichtregression.
- Operator führt den kleinsten sinnvollen Patch aus.
- Lesender Regressionsagent prüft Folgen.
- Fehlerlern-Agent registriert neue Fehler/Lösungspaare.
- Dokumentation und Manifeste werden bei Vertragsänderungen synchronisiert.
- Merge nur bei grünen Pflichtgates.

## Standards

- Python-Projektmetadaten: pyproject.toml.
- Strukturierte Manifeste: JSON mit JSON-Schema 2020-12.
- Versionsprinzip: SemVer 2.0.0.
- Buildnachweis: prüfbare Herkunft, Eingaben, Commit und Prüfsummen.
- GitHub-Automation mit minimalen Token-Rechten.
- Caches nur für wiederverwendbare, nicht vertrauliche Abhängigkeiten.
- Vollständige Abnahme vor Freigabe.

## Definition „fertig“

Ein Arbeitsschritt ist erst fertig, wenn:
- Vorvalidierung grün,
- Patch minimal und nachvollziehbar,
- Nachvalidierung grün,
- betroffene Tests grün,
- Pflichtregression vor Merge grün,
- Zustandsregister aktualisiert,
- Fehlerkatalog bei neuem Fehler ergänzt,
- Dokumentation bei Vertragsänderung aktualisiert,
- nächster sinnvoller Schritt dokumentiert ist.
