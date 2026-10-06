# Pflichtenheft v1.0

## 1. Ziel

Ein lokales, portables Linux-Werkzeug für Laien, das Dateien sicher findet, Textinhalte durchsucht, echte Duplikate erkennt und Ergebnisse virtuell organisiert.

## 2. Muss-Funktionen

1. Ordner grafisch auswählen.
2. Textdateien nach Dateinamen durchsuchen.
3. unterstützte Textdateien nach Inhalt durchsuchen.
4. reguläre Dateien auf echte Duplikate prüfen.
5. Duplikate verständlich gruppiert anzeigen.
6. Treffer markieren und kommentieren.
7. virtuelle Sammlungen anlegen und Treffer zuordnen.
8. alle virtuellen Daten lokal in SQLite speichern.
9. automatische Start- und Sicherheitsprüfung ausführen.
10. 100/150/200-%-Sichtbarkeitsprüfung ermöglichen.
11. ohne Internet nutzbar sein.
12. portable Laufzeit im Release mitliefern.

## 3. Darf Version 1 ausdrücklich nicht

Version 1 darf Originaldateien nicht:

- löschen,
- verschieben,
- umbenennen,
- überschreiben,
- in eine Quarantäne bewegen,
- inhaltlich ändern,
- Berechtigungen ändern.

Version 1 darf ebenfalls nicht:

- Systempakete installieren,
- `sudo` verlangen,
- kritische Linux-Systembereiche durchsuchen,
- symbolischen Verknüpfungen folgen,
- ungefragt Internetzugriffe ausführen,
- auf ein fehlendes portables Python durch System-Python ausweichen.

## 4. Sicherheitsinvarianten

Eine Sicherheitsinvariante ist eine Regel, die durch neue Funktionen niemals verletzt werden darf.

- `SafetyPolicy.read_only == True` bleibt Standard.
- vier Schreibfunktionen bleiben `enabled=0` und `locked=1`.
- Kern und Oberfläche enthalten keine direkten zerstörerischen Datei-APIs.
- ein Duplikat benötigt vollständige SHA-256-Gleichheit.
- virtuelle Organisation verändert nur SQLite.

## 5. Bedienung

Der Nutzer soll im Normalfall nur:

1. Ordner wählen,
2. Suche oder Duplikatprüfung starten,
3. Ergebnisse ansehen und virtuell organisieren.

Technische Begriffe werden in der Oberfläche auf ein notwendiges Minimum reduziert.

## 6. Barrierefreiheit

- vollständig lesbare Beschriftungen,
- keine Information nur durch Farbe,
- Tastaturfokus über Standard-Qt-Verhalten,
- große Bedienelemente,
- Wortumbruch bei längeren Hinweisen,
- automatisierte Sichtbarkeitsprüfung bei 100, 150 und 200 Prozent.

## 7. Abnahmekriterien

Version 1 gilt erst als abnahmefähig, wenn:

- alle automatischen Tests grün sind,
- 100/150/200-%-Prüfung grün ist,
- der portable Selbsttest grün ist,
- keine zerstörerische Datei-API im Anwendungscode gefunden wird,
- die Release-Prüfsumme erzeugt wurde.
