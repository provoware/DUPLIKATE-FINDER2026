# Vollautomatische Startroutine

## Grundsatz

Der normale Start verlangt keine technische Entscheidung vom Nutzer.

STARTEN.sh:

1. verwendet ausschließlich die mitgelieferte Python-Laufzeit,
2. führt die lokale Bootstrap-Prüfung aus,
3. legt fehlende interne Arbeitsordner an,
4. versucht bei fehlendem PySide6 eine Reparatur ausschließlich aus dem mitgelieferten wheelhouse/,
5. führt den Selbsttest aus,
6. startet nur bei einem sicheren Zustand die Oberfläche.

Es gibt kein sudo, keine Paketinstallation ins Linux-System und keinen stillen Internet-Download beim Start.

## Nicht automatisch reparierbare Fälle

Fehlt die komplette portable Laufzeit oder das lokale Reparaturpaket, wird der Start sicher gestoppt. Details stehen im Protokollordner. Das Hauptsystem bleibt unverändert.
