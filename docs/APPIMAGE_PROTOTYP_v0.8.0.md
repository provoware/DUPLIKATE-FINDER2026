# AppImage-Prototyp v0.8.0

## Status

**PROTOTYP – nicht Bestandteil des stabilen v0.8.0-Releases.**

Der Prototyp wird vollständig auf dem separaten Zweig `prototype/appimage-v0.8.0` gebaut und verändert den stabilen Hauptzweig nicht.

## Messergebnis

- AppImage: `PROVOWARE-DUPLIKATE-FINDER-2026-v0.8.0-x86_64.AppImage`
- Größe: **239 MiB**
- SHA-256: `6900a60900d559508210fc9112645d0a4fb1b280fc305aa2c066e9bbd26d7d7e`
- Architektur: Linux x86_64
- Build-Basis: Ubuntu 22.04

Zum Vergleich mit den v0.8.0-Paketen:

| Variante | gemessene Größe |
| --- | ---: |
| AppImage-Prototyp | 239 MiB |
| Lite tar.gz | ca. 274 MB |
| Lite ZIP | ca. 310 MB |
| Recovery tar.gz | ca. 520 MB |

## Automatische Tests

Dasselbe erzeugte AppImage wurde erfolgreich geprüft auf:

- Ubuntu 22.04
- Ubuntu 24.04

Je Zielsystem wurden geprüft:

1. SHA-256-Prüfsumme,
2. Start aus einem simulierten USB-Pfad mit Leerzeichen,
3. direkter AppImage-Start, soweit FUSE im Runner verfügbar ist,
4. offizieller Extraktions-/Start-Fallback, falls direkter FUSE-Start nicht verfügbar ist,
5. portable Nutzerdaten neben dem AppImage über `PROVOWARE_PORTABLE_DATA=1`,
6. GUI-Rauchtest im Offscreen-Modus,
7. lokaler Nur-Lesen-Selbsttest aus dem extrahierten AppImage.

## Datenablage

Standardmäßig verwendet das AppImage den Benutzer-Datenordner.

Wird `PROVOWARE_PORTABLE_DATA=1` gesetzt, entsteht neben dem AppImage:

`PROVOWARE-DATEN/`

Damit lässt sich Programm + Arbeitsdaten gemeinsam auf einem USB-Datenträger testen, ohne in das schreibgeschützte AppImage schreiben zu müssen.

## Sicherheitsgrenze

Das AppImage ändert das bestehende Sicherheitsmodell nicht:

- Originaldateien bleiben Nur-Lesen,
- keine Löschfunktion,
- kein Verschieben,
- kein Umbenennen,
- kein Überschreiben,
- keine Quarantäne.

## Entscheidung

Der Prototyp ist technisch erfolgreich, wird aber vorerst **nicht automatisch zum stabilen Release hinzugefügt**.

Vor einer Promotion zum dritten offiziellen Paketprofil sollen zusätzlich geprüft werden:

- Kubuntu 22.04 auf realer Hardware,
- Start vom echten USB-Stick mit `exec` und `noexec`,
- Verhalten ohne FUSE,
- Dateidialoge und Dolphin-Integration,
- externe Datenträger,
- langfristig reproduzierbarer/pinnbarer appimagetool-Build,
- vollständige 800×600-/100/150/200-%-Abnahme direkt aus dem AppImage.
