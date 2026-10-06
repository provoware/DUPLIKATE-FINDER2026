# Portabler Linux-Release

## Ziel

Der Endnutzer soll keine Python-Pakete und keine Linux-Systempakete installieren müssen. Gleichzeitig soll das normale Paket keinen unnötigen Entwicklungs- oder Reparaturballast enthalten.

## Zwei Paketprofile

### Lite

Für normale Nutzung. Enthalten bleiben:

- vollständige geprüfte Python-Laufzeit,
- vollständige installierte PySide6/Qt-Laufzeit,
- Anwendungscode und Laufzeitressourcen,
- Laien-, Portable- und Sicherheitsdokumentation,
- Startskripte einschließlich USB-Start.

Bewusst entfernt werden nur eindeutig unnötige Distributionsbestandteile:

- `wheelhouse/` mit der zweiten Kopie der PySide6-Installationspakete,
- Agenten- und Entwicklungsstandards,
- JSON-Schemata und Vorlagen, die zur Laufzeit nicht benötigt werden,
- Prüf-/Build-Werkzeuge nach abgeschlossener Paketabnahme,
- Python-Zwischendateien.

Die eigentliche Python-/Qt-Laufzeit wird **nicht aggressiv beschnitten**.

### Recovery

Enthält dieselben Programmfunktionen wie Lite, zusätzlich aber den lokalen PySide6-Reparaturvorrat und die für die E2E-Abnahme notwendigen Unterlagen.

## Funktionsgleichheit

Lite und Recovery werden aus demselben Runtime-Stand erzeugt. Vor der endgültigen Lite-Bereinigung werden für beide Profile geprüft:

1. benötigte PySide6-Module sind importierbar,
2. keine direkte Python-Laufzeitbibliothek fehlt,
3. echter GUI-Start funktioniert,
4. Konsolen-Selbsttest funktioniert,
5. vollständige autonome Abnahme ist grün,
6. Zahl und Ergebnis der automatischen Funktionsprüfungen stimmen überein.

Nach der endgültigen Lite-Bereinigung werden GUI und Konsole erneut gestartet.

## USB-Stick

`STARTEN_VOM_STICK.sh` setzt den Arbeitsordner standardmäßig auf `PROVOWARE-DATEN` neben dem Programm.

- Ist die Laufzeit auf dem Stick ausführbar, startet das Programm direkt vom Stick.
- Ist das Dateisystem mit `noexec` eingehängt, wird die Programmlaufzeit einmalig in den lokalen Benutzer-Cache kopiert. Nutzerdaten können weiterhin auf dem Stick liegen.
- Das System-Python wird dabei nicht als Ersatz verwendet.

Damit kann der entpackte Ordner auf einen USB-Stick kopiert und auf einem kompatiblen Linux-x86_64-System gestartet werden.

## ZIP und tar.gz

Lite wird zusätzlich als ZIP erzeugt. Das ZIP ist für einfaches Kopieren und Entpacken gedacht. `tar.gz` bleibt die Linux-nahe Variante mit zuverlässig erhaltenen Dateirechten.

## Verkehr und Build-Effizienz

- portable Python-Archive und Python-Pakete werden in GitHub Actions gecacht,
- Versionsvorgaben werden aus `dependencies.env` gelesen,
- unnötige Mehrfachdownloads werden vermieden,
- Entwicklungs-Vollpakete laufen nur bei relevanten Dateiänderungen.

## Sicherheitsgrenze

Kein Paketprofil aktiviert physische Dateiänderungen. Löschen, Verschieben, Umbenennen und Quarantäne bleiben gesperrt.
