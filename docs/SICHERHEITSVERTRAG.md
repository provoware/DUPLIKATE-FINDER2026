# Sicherheitsvertrag

Dieser Vertrag ist für Anwendungscode und Entwicklungsagenten bindend.

## Schutzstufe v1

Originaldateien sind **read-only**: nur lesen.

## Gesperrte Linux-Bereiche

Die Suchwurzel `/` sowie kritische Systempfade wie `/etc`, `/usr`, `/var`, `/sys`, `/proc`, `/boot`, `/dev`, `/root` werden blockiert.

## Symbolische Verknüpfungen

Werden standardmäßig nicht verfolgt. Dadurch kann ein scheinbar harmloser Nutzerordner nicht unbemerkt in andere Bereiche springen.

## Duplikatdefinition

Gleiche Größe allein genügt nicht. Nur vollständig identische SHA-256-Prüfsummen erzeugen eine Duplikatgruppe.

## Zerstörerische APIs

Im Anwendungscode sind direkte Aufrufe zum Löschen, Verschieben, Umbenennen oder Ersetzen von Dateien verboten. Ein Architekturtest überwacht dies.

## Spätere Schreibfreigabe

Vor einer späteren Freigabe müssen mindestens existieren:

1. Änderungsplan ohne Ausführung.
2. klare Vorschau.
3. Vorprüfung von Quelle und Ziel.
4. Transaktionsjournal.
5. Nachprüfung.
6. Rückgängig-Mechanismus.
7. Absturz-Wiederaufnahme.
8. gesonderte Freigabetests.

Bis dahin bleiben Dashboard-Schalter sichtbar, aber gesperrt.
