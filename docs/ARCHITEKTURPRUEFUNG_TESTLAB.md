# Architekturprüfung Testlabor und Fehlerpfade

Stand: 2026-10-07

## Ergebnis

Die Architektur ist für den aktuellen Projektumfang sinnvoll und ausreichend streng getrennt. Eine weitere kosmetische Klassenzerlegung würde derzeit mehr Kopplung und Verwaltungsaufwand erzeugen als Nutzen.

## Abhängigkeitsrichtung

Die gewünschte Richtung ist:

```text
GUI
  -> Controller
      -> Kern / Speicher

Konsole
  -> Produktfunktionen
  -> Testlabor-Adapter

Testlabor
  -> Kern / Speicher

Kern / Speicher
  -X-> GUI
  -X-> Testlabor
```

Kern- und Speicherschicht dürfen weder GUI noch Testlabor importieren. Das Testlabor darf die Produktlogik als Prüfling verwenden, aber nicht umgekehrt.

## Gezielte Verbesserung dieser Runde

Die Testlabor-spezifischen Konsolenparameter und Ausführungsdetails wurden aus `app/cli.py` nach `app/testing/cli.py` verschoben.

Damit kennt die Hauptkonsole nur noch zwei Testlabor-Schnittstellen:

- `configure_testlab_arguments(...)`
- `run_requested_testlab(...)`

Die Einzelheiten zu Profilen, Fehler-Injektion, Leistungsbericht und Vergleichsbasis bleiben im Testlabor.

## Bewusst nicht weiter zerlegt

Nicht weiter aufgeteilt werden:

- `MainWindow` und die bestehenden Controller
- Scan-/Hash-/Duplikatkern
- Datenbankklasse allein wegen Dateigröße
- Dateibrowser allein wegen Dateigröße

Neue Abstraktionen sind nur gerechtfertigt, wenn sie nachweisbar Doppelcode, Kopplung oder Testbarkeit verbessern.

## Neue Prüfschranken

Automatische Architekturtests verhindern:

- Abhängigkeiten von `app/core` auf `app/gui`
- Abhängigkeiten von `app/core` auf `app/testing`
- Abhängigkeiten von `app/storage` auf `app/gui`
- Abhängigkeiten von `app/storage` auf `app/testing`
- Abhängigkeiten des Testlabors auf die GUI

## Visueller Stand

Der visuelle Stand bleibt FROZEN. Diese Runde verändert keine Theme-, Layout- oder MainWindow-Struktur.
