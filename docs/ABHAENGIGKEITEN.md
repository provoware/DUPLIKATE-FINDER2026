# Vollständige Abhängigkeiten

## Grundsatz

Das **PROVOWARE-Vollpaket** bringt alles mit, was sicher und sinnvoll mitgeliefert werden kann:

- Python 3.12.15
- PySide6 6.11.2 einschließlich Qt
- shiboken6, PySide6 Essentials und PySide6 Addons
- pytest 8.x
- setuptools und wheel
- lokalen Python-Paketvorrat
- Anwendung, Tests, Dokumentation und Abnahmewerkzeuge

**Tk und Tkinter werden nicht verwendet.** Die grafische Oberfläche ist ausschließlich PySide6/Qt.

## GitHub-Quellcode gegenüber Vollpaket

GitHubs automatisch erzeugtes „Source code ZIP“ enthält nur Dateien aus Git. Große Laufzeiten gehören absichtlich nicht in die Git-Historie.

Darum gelten zwei sichere Wege:

1. **PROVOWARE-Vollpaket:** Laufzeit und Pakete sind bereits enthalten → entpacken → starten.
2. **GitHub-Quellcode:** `ENTWICKLUNG_STARTEN.sh` erkennt Fehlendes und lädt es automatisch ausschließlich in `.provoware-dev/`.

## Fest definierte Komponenten

| Komponente | Version / Bereich | Zweck |
|---|---|---|
| CPython | **3.12.15** | eigene Projektlaufzeit |
| PySide6 | **6.11.2** | Oberfläche / Qt |
| PySide6_Addons | 6.11.2 | Qt-Zusatzmodule |
| PySide6_Essentials | 6.11.2 | Qt-Kernmodule |
| shiboken6 | 6.11.2 | Python-/Qt-Bindung |
| pytest | >=8,<9 | Tests |
| setuptools | >=68 | Paketbau |
| wheel | >=0.45 | Paketformat |

Python-Archiv-SHA-256:

`731af898886c5f821890dc901eca3c651cca8e51fa7308c159d12a1194aeac91`

## Was Linux selbst bereitstellen muss

Nicht sinnvoll mitgeliefert oder ersetzt werden können der bereits laufende Linux-Kernel, der echte Grafiktreiber und der aktive X11-/Wayland-Anzeigeserver. Diese Teile werden erkannt und geprüft.

Das Systemprofil erfasst außerdem wichtige Linux-Bibliotheken wie EGL, OpenGL, XKB, Fontconfig, DBus, X11 und XCB samt tatsächlich installierter Paketversion.

## Automatisches Systemprofil

Vor dem Start werden unter anderem geprüft und gespeichert:

- Betriebssystem und Version
- Kernel und Architektur
- CPU-Kernzahl
- RAM und SWAP
- freier Speicher
- X11/Wayland
- Schreibrechte
- Python-Version
- alle relevanten Python-Paketversionen
- Qt-Startfähigkeit
- Hilfsprogramme wie curl, wget, tar, sha256sum, dpkg und apt
- erkennbare Linux-Bibliotheken

Ausgaben:

- `.provoware-dev/systemprofil.json`
- `logs/ABHAENGIGKEITEN_AKTUELL.txt`
- `logs/ABHAENGIGKEITEN_AKTUELL.json`

Das vorherige Profil wird beim nächsten Lauf eingelesen und im neuen Profil referenziert. Dynamische Werte wie freier Speicher, Schreibrechte und Qt-Startfähigkeit werden trotzdem frisch geprüft.

## Automatisch verwalteter Bereich

```text
.provoware-dev/
├── runtime/
├── cache/
├── wheelhouse/
└── systemprofil.json
```

Der gesamte Ordner wird von Git ignoriert.

## Nutzerbefehl

```bash
./ENTWICKLUNG_STARTEN.sh
```

Keine manuelle virtuelle Umgebung und kein manuelles `pip install`.


## Optionale Medienanalyse ab v0.9.0

Für die normalen Programmfunktionen ist **FFmpeg/ffprobe nicht erforderlich**.

Ist das Programm `ffprobe` auf dem Linux-System bereits vorhanden, kann PROVOWARE zusätzliche technische Angaben zu Audio- und Videodateien auslesen, zum Beispiel:

- Laufzeit,
- Containerformat,
- Audio-/Video-Codec,
- Bildauflösung,
- Bildrate,
- Tonkanäle,
- Abtastrate,
- Bitrate.

Fehlt `ffprobe`, startet das Werkzeug trotzdem normal. Die Vorschau zeigt dann die verfügbaren Basisdaten und einen verständlichen Hinweis.

**Wichtig:** v0.9.0 fügt FFmpeg/ffprobe nicht als Pflichtabhängigkeit zum Lite-, Recovery- oder AppImage-Paket hinzu.
