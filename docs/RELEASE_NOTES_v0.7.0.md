# PROVOWARE DUPLIKATE-FINDER 2026 – v0.7.0

## Freigabestatus

v0.7.0 ist der geprüfte Nur-Lesen-Release für robuste große Such- und Duplikatbestände. Originaldateien werden weiterhin nicht gelöscht, verschoben, umbenannt oder überschrieben.

## Wesentliche Verbesserungen

- versionierte und transaktionale SQLite-Migrationen
- Erkennung von Dateiänderungen während Inhalts- und SHA-256-Prüfungen
- sichtbare Anzahl übersprungener oder nicht lesbarer Dateien
- atomare Einstellungen und Zustandsexporte
- transaktionaler Zustandimport mit Vor- und Nachprüfung
- begrenzte technische Such- und Scan-Historie
- geprüfter SHA-256-Zwischenspeicher für unveränderte Dateien
- mehrstufige Duplikatprüfung: Größe → kurze Inhaltsprobe → vollständiges SHA-256
- SQLite-Inventare statt vollständiger Python-Dateilisten
- SQLite-seitenweise Suchtreffer, Sammlungen und Duplikatmitglieder
- identische skalierbare Pipeline in grafischer Oberfläche und Konsolenmodus

## Abnahme

Vor der Freigabe wurden erfolgreich geprüft:

- Kern- und Sicherheitstests
- Oberfläche bei 100 %, 150 % und 200 %
- autonome Gesamt-Abnahme
- Entwicklungs-Vollpaket
- Offline-Prüfung des Vollpakets
- reproduzierbares Archiv und SHA-256-Prüfsumme
- Build-Nachweis und SPDX-Komponentenliste

## Eingefrorene Bereiche

- Bedienoberfläche / Prozesssteuerung: FROZEN 🟢
- Robustheit / Skalierung: FROZEN 🟢

Änderungen in diesen Bereichen erfordern eine ausdrückliche Wiederöffnung oder eine klar begrenzte Sicherheits-, Regressions- oder Plattformkorrektur.

## Sicherheitsgrenze

Physische Dateiaktionen bleiben gesperrt. Verschieben, Umbenennen, Quarantäne und Löschen sind nicht Bestandteil dieses Releases.
