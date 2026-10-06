# Analyse – Audio, Video und AppImage nach v0.8.0

## Ausgangslage

Der Datei-/Medienbrowser v0.8.0 ist vollständig abgenommen:

- Kern- und Sicherheitstests: grün
- 800×600: grün
- 100 %, 150 %, 200 %: grün
- autonome Gesamt-Abnahme: grün
- Portable Lite/Recovery: grün
- Funktionsgleichheit Lite/Recovery: grün

Gemessene Paketgrößen:

- Recovery entpackt: 985,7 MiB
- Lite entpackt: 733,0 MiB
- Einsparung Lite: 252,7 MiB bzw. 25,64 %
- Lite tar.gz: ca. 274 MB
- Lite ZIP: ca. 310 MB
- Recovery tar.gz: ca. 520 MB

Die Python-/Qt-Laufzeit wurde dabei bewusst nicht aggressiv beschnitten.

## Audio und Video

### Aktueller v0.8.0-Stand

Audio- und Videodateien werden:

- als eigene Dateigruppen erkannt,
- mit Dateigröße, Pfad und Änderungsdatum angezeigt,
- über das Standardprogramm des Linux-Systems geöffnet,
- nicht intern abgespielt.

### Bewertung einer internen Wiedergabe

PySide6 bringt bereits Qt-Multimedia-Bausteine mit. Eine robuste interne Wiedergabe auf unterschiedlichen Linux-Systemen ist trotzdem nicht automatisch garantiert, weil je nach Zielsystem Multimedia-Unterbau, Codecs und Systembibliotheken beteiligt sein können.

Eine interne Wiedergabe würde deshalb zusätzliche Risiken erzeugen:

- mehr plattformspezifische Abhängigkeiten,
- zusätzliche Codec-/Backend-Fehlerfälle,
- höhere E2E-Testlast,
- mögliches Wachstum des Portable-Pakets, falls Systembestandteile mitgebündelt werden müssten,
- deutlich mehr UI-Komplexität durch Playerzustände, Zeitleiste, Lautstärke, Fehlerzustände und Hintergrundressourcen.

### Entscheidung

Für v0.8.0 **keinen internen Audio-/Videoplayer ergänzen**.

Die aktuelle Lösung „Metadaten + extern öffnen“ bleibt die bevorzugte stabile Stufe.

Ein interner Player darf erst in einem eigenen Entwicklungsblock untersucht werden, wenn folgende Fragen vorher messbar beantwortet sind:

1. Welche Formate funktionieren auf den freigegebenen Linux-Zielsystemen tatsächlich?
2. Welche zusätzlichen Systembibliotheken oder Codecs werden benötigt?
3. Wie stark wachsen Lite und Recovery?
4. Funktioniert Wiedergabe auch vom USB-Stick bzw. AppImage?
5. Wie werden fehlende Codecs verständlich behandelt?
6. Wie hoch ist die zusätzliche RAM-/CPU-Last?

## AppImage

### Nutzen

AppImage ist für dieses Projekt interessant, weil es die Portable-Idee auf eine einzelne ausführbare Datei verdichten kann:

- eine Datei auf USB-Stick kopieren,
- auf kompatiblem Linux-System starten,
- kein Entpacken des eigentlichen Programmpakets nötig,
- klare zusätzliche Verteilform für Laien.

### Grenzen und Risiken

AppImage soll **nicht** Lite/Recovery ersetzen.

Vor einer Freigabe muss separat geprüft werden:

- Start auf mehreren unterstützten Linux-Systemen,
- Verhalten auf Datenträgern mit eingeschränkten Ausführungsrechten,
- FUSE-/Mount-Verhalten des Zielsystems,
- Zugriff auf externe Datenträger,
- Qt-Plugins und Plattformbibliotheken,
- Dateidialoge und Öffnen im System-Dateimanager,
- Update-/Versionsanzeige,
- Paketgröße,
- reproduzierbarer Build und SHA-256,
- 800×600-/100/150/200-%-Abnahme direkt aus dem AppImage.

### Empfohlene Architektur

AppImage als **drittes optionales Distributionsprofil**:

1. Portable Lite – kleinste normale Ordner-/Archivvariante
2. Portable Recovery – mit Offline-Reparaturvorrat
3. AppImage – einzelne ausführbare Datei für besonders einfachen Transport

Die AppImage-Erzeugung soll einen eigenen Workflow erhalten und aus demselben geprüften Quellstand gebaut werden. Erst nach erfolgreicher E2E-Abnahme darf ein AppImage an einen Release angehängt werden.

## Empfohlene Reihenfolge

1. v0.8.0 Datei-/Medienbrowser stabil veröffentlichen.
2. AppImage-Prototyp separat bauen und ausschließlich messen/testen.
3. Erst danach entscheiden, ob interne Audio-/Videowiedergabe überhaupt einen ausreichenden Nutzen gegenüber „Extern öffnen“ bietet.

## Fazit

Die beste aktuelle Balance aus Funktionsumfang, Stabilität und Paketgröße ist:

- Text/Bild/PDF intern vorschauen,
- Audio/Video sicher klassifizieren und extern öffnen,
- Portable Lite als Standard,
- Recovery als Reparaturvariante,
- AppImage später als zusätzliche Ein-Datei-Distribution testen.

Damit bleibt v0.8.0 schlank, verständlich und robust, ohne Multimedia- oder Paketkomplexität unnötig in den stabilen Funktionsblock zu ziehen.


## v0.9.0 – umgesetzter AppImage-Prototyp

Der Prototyp besitzt jetzt einen eigenen GitHub-Actions-Workflow und bleibt vollständig vom stabilen Lite-/Recovery-Veröffentlichungsweg getrennt.

Automatisch geprüft werden:

- Bau auf Ubuntu 22.04,
- SHA-256-Prüfsumme,
- Größenobergrenze 900 MiB,
- GUI-Start im Offscreen-Test,
- Start aus einem simulierten USB-Pfad mit Leerzeichen,
- Laufzeittest auf Ubuntu 22.04,
- Laufzeittest auf Ubuntu 24.04.

Das erzeugte AppImage wird ausschließlich als Workflow-Artefakt bereitgestellt. Eine automatische Veröffentlichung an GitHub Releases ist absichtlich nicht aktiviert.


### Messergebnis des v0.9.0-Prototyps

- AppImage-Größe: ca. **263 MB**
- Build-System: Ubuntu 22.04
- Starttest Ubuntu 22.04: **grün**
- Starttest Ubuntu 24.04: **grün**
- SHA-256-Prüfung: **grün**
- simulierter USB-Pfad mit Leerzeichen: **grün**
- stabile automatische Veröffentlichung: **weiterhin deaktiviert**

Damit ist die technische Machbarkeit bestätigt. Vor einer Aufnahme in einen offiziellen Release bleibt eine bewusste Produktentscheidung erforderlich.
