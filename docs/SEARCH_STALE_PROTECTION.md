# Schutz der Textsuche vor veränderten Quelldateien

## Zweck
Der Scan liest Originaldateien weiterhin **ausschließlich lesend**.
Ein Treffer darf nicht aus einer Datei gemeldet werden, die zwischen Dateibestandsaufnahme und Leseende unbemerkt verändert wurde.

## Neue Sicherheitsgrenzen
- Vor und nach dem Lesen werden Dateigröße, Änderungszeit und vorhandene Geräte-/Inode-Informationen mit dem erfassten Dateieintrag verglichen.
- Pro Datei werden Inhaltsfunde erst **nach** erfolgreicher Nachprüfung an Anzeige und Rückruf übergeben.
- Lesezugriffe sind auf Teilstücke von 256 Ki-Zeichen begrenzt. Suchwörter können trotzdem über die Teilstückgrenze gefunden werden.
- Veränderte oder verschwundene Dateien werden als Diagnosefehler behandelt; deren Treffer werden verworfen.
- Die Suche verändert, verschiebt, benennt oder löscht niemals Originaldateien.

## Testpflicht
`tests/test_search.py` enthält positive Suche, Teilstückgrenze, Dateiänderung **vor** sowie **während** des Lesevorgangs (inklusive ausbleibender Treffer-Rückrufe).

## Bekannte Grenze
Identitätsprüfung vor/nach dem Lesen ist keine kryptografische Vollinhaltsprüfung und kann einen gleichzeitigen Austausch mit identischen Metadaten nicht beweisen. Für Lösch-/Duplikatentscheidungen gilt weiterhin der separate vollständige SHA-256-Vertrag; dieser PR erlaubt ausdrücklich keine Dateimutationen.

## Bezug
Issue #35, geschlossener Alt-PR #31. GUI/Kontrast und isolierte Test-Sandbox werden getrennt behandelt und bleiben bis zur erneuten Prüfung offen.
