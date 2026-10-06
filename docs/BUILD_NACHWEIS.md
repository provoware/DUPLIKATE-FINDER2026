# Build-Nachweis und Software-Bestandsliste

Jeder Entwicklungs-Vollpaket-Bau erzeugt zusätzlich:

- `reports/BUILD-NACHWEIS.json`: Commit, Projektversion, Laufzeit, Abhängigkeiten, Archivgröße und SHA-256.
- `reports/SBOM.spdx.json`: schlanke Software-Bestandsliste im SPDX-2.3-JSON-Format.

Der Build-Nachweis orientiert sich am Provenienzgedanken von SLSA, beansprucht aber bewusst **keine formale SLSA-Level-Zertifizierung**.

Das Archiv wird mit sortierten Dateinamen, vereinheitlichten Zeitstempeln und ohne gzip-Zeitstempel erzeugt. Das verbessert die Reproduzierbarkeit identischer Builds.
