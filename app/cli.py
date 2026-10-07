from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from app.core.duplicates import scan_duplicate_groups_to_database
from app.models.entities import SearchJob
from app.startup.selftest import run_selftest
from app.storage.database import Database
from app.core.search_pipeline import run_search_to_database
from app.validation import validate_scan_root, validate_search_request
from app.testing.cli import (
    configure_testlab_arguments,
    run_requested_testlab,
)
from app.workspace import ensure_workspace


class ConsoleUI:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.database = Database(base_dir / "data" / "duplicate_finder.sqlite3")
        self.database.initialize()
        self.last_hits = []
        self.color = sys.stdout.isatty()

    def c(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.color else text

    def line(self, char: str = "─") -> str:
        return char * min(88, shutil.get_terminal_size((88, 24)).columns)

    def title(self, text: str) -> None:
        print("\n" + self.c("1;36", self.line("═")))
        print(self.c("1;36", f"  {text}"))
        print(self.c("1;36", self.line("═")))

    def pause(self) -> None:
        input("\nEnter drücken für das Hauptmenü … ")

    def choice(self, prompt: str, valid: set[str]) -> str:
        while True:
            value = input(prompt).strip()
            if value in valid:
                return value
            print(self.c("1;33", "⚠ Bitte nur eine der angezeigten Nummern eingeben."))

    def choose_root(self) -> Path | None:
        home = Path.home()
        options = [("1", Path.cwd(), "Aktueller Ordner"), ("2", home, "Persönlicher Ordner"), ("3", home / "Dokumente", "Dokumente"), ("4", home / "Downloads", "Downloads")]
        print("\nOrdner auswählen:")
        for key, path, label in options:
            marker = "" if path.exists() else " (nicht vorhanden)"
            print(f"  {key}) {label}: {path}{marker}")
        print("  5) Anderen Ordnerpfad eingeben")
        print("  0) Zurück")
        selected = self.choice("Auswahl: ", {"0", "1", "2", "3", "4", "5"})
        if selected == "0":
            return None
        path = Path(input("Ordnerpfad: ").strip()).expanduser() if selected == "5" else next(path for key, path, _ in options if key == selected)
        result = validate_scan_root(path)
        if not result.ok:
            print(self.c("1;31", f"✖ {result.title}: {result.message}"))
            return None
        return path.resolve()

    def show_status(self) -> None:
        self.title("SYSTEMSTATUS")
        checks = run_selftest(self.base_dir, require_gui=False)
        for check in checks:
            mark = self.c("1;32", "✔") if check.ok else self.c("1;31", "✖")
            print(f"{mark} {check.name:<20} {check.detail}")
        print("\n🔒 Originaldateien: NUR LESEN")
        print(f"🧾 Protokolle: {self.base_dir / 'logs'}")

    def text_search(self) -> None:
        self.title("TEXTSUCHE")
        root = self.choose_root()
        if root is None:
            return
        query = input("Suchbegriff: ").strip()
        print("\nSuchbereich:\n  1) Dateinamen\n  2) Dateiinhalte\n  3) Beides")
        mode = self.choice("Auswahl: ", {"1", "2", "3"})
        names, contents = mode in {"1", "3"}, mode in {"2", "3"}
        validation = validate_search_request(root, query, names, contents)
        if not validation.ok:
            print(self.c("1;31", f"✖ {validation.title}: {validation.message}"))
            return

        job = SearchJob(
            root=root,
            query=query,
            search_names=names,
            search_contents=contents,
        )
        try:
            result = run_search_to_database(
                job,
                self.database,
                run_kind="search-console",
            )
        except Exception as exc:
            print(self.c("1;31", f"✖ Suche sicher gestoppt: {exc}"))
            return

        page = self.database.search_hits_page(
            result.job_id,
            offset=0,
            limit=100,
            sort_column=2,
        )
        self.last_hits = [hit for hit, _marked in page]
        print(
            self.c(
                "1;32",
                f"\n✔ {job.scanned_files} Textdateien geprüft · "
                f"{result.hit_count} Treffer · {result.error_count} übersprungen",
            )
        )
        for index, hit in enumerate(self.last_hits, 1):
            line = f"Zeile {hit.line_number}" if hit.line_number else "Dateiname"
            print(f"{index:>3}) {hit.path} · {line} · {hit.excerpt[:100]}")
        if result.hit_count > len(self.last_hits):
            print(
                f"… weitere {result.hit_count - len(self.last_hits)} "
                "Treffer nicht aufgelistet."
            )
        if self.last_hits:
            self._organize_hit()

    def _organize_hit(self) -> None:
        print("\nTreffer virtuell organisieren?\n  1) Markieren / Notiz\n  2) Sammlung zuordnen\n  0) Nein")
        action = self.choice("Auswahl: ", {"0", "1", "2"})
        if action == "0":
            return
        raw = input(f"Treffernummer 1–{len(self.last_hits)}: ").strip()
        if not raw.isdigit() or not 1 <= int(raw) <= len(self.last_hits):
            print(self.c("1;33", "⚠ Ungültige Treffernummer. Es wurde nichts verändert."))
            return
        hit = self.last_hits[int(raw) - 1]
        if action == "1":
            note = input("Optionale Notiz (Enter = leer): ").strip()
            self.database.set_virtual_item(hit.path, True, note)
            print(self.c("1;32", "✔ Virtuelle Markierung gespeichert. Originaldatei unverändert."))
            return
        collections = self.database.collections()
        if not collections:
            print("Noch keine Sammlung vorhanden.")
            name = input("Name für neue Sammlung: ").strip()
            try:
                cid = self.database.create_collection(name)
            except Exception as exc:
                print(self.c("1;31", f"✖ Sammlung nicht angelegt: {exc}"))
                return
        else:
            for i, col in enumerate(collections, 1):
                print(f"  {i}) {col.name}")
            raw_col = input("Sammlungsnummer: ").strip()
            if not raw_col.isdigit() or not 1 <= int(raw_col) <= len(collections):
                print(self.c("1;33", "⚠ Ungültige Auswahl."))
                return
            cid = collections[int(raw_col) - 1].id
        self.database.add_collection_item(cid, hit.path)
        print(self.c("1;32", "✔ Virtuell einsortiert. Originaldatei unverändert."))

    def duplicates(self) -> None:
        self.title("DUPLIKATPRÜFUNG")
        root = self.choose_root()
        if root is None:
            return
        try:
            scanned, group_count, errors = scan_duplicate_groups_to_database(
                root,
                self.database,
            )
        except Exception as exc:
            print(self.c("1;31", f"✖ Prüfung sicher gestoppt: {exc}"))
            return
        summaries = self.database.duplicate_group_summaries()
        print(
            self.c(
                "1;32",
                f"\n✔ {scanned} Dateien inventarisiert · {group_count} sichere Gruppen · "
                f"{errors} übersprungen",
            )
        )
        for i, (group_id, _digest, size, members) in enumerate(summaries[:100], 1):
            waste = size * (members - 1)
            print(f"\n{i}) {members} Dateien · {size} Byte · mehrfach: {waste} Byte")
            page = self.database.duplicate_members_page(
                group_id,
                offset=0,
                limit=50,
            )
            for path, _member_size, _mtime_ns in page:
                print(f"     {path}")
            if members > len(page):
                print(f"     … {members - len(page)} weitere")
        if len(summaries) > 100:
            print(f"… {len(summaries) - 100} weitere Gruppen nicht aufgelistet.")
        if not summaries:
            print("Keine vollständig identischen Dateien gefunden.")

    def collections(self) -> None:
        self.title("VIRTUELLE SAMMLUNGEN")
        collections = self.database.collections()
        if not collections:
            print("Noch keine Sammlungen vorhanden.")
        for i, col in enumerate(collections, 1):
            count = self.database.collection_item_count(col.id)
            items = self.database.collection_items_page(
                col.id,
                offset=0,
                limit=20,
            )
            print(f"{i}) {col.name} · {count} Einträge")
            for entry in items:
                print(f"     {entry.path}")
            if count > len(items):
                print(f"     … {count - len(items)} weitere")
        print("\n  1) Neue Sammlung anlegen\n  0) Zurück")
        if self.choice("Auswahl: ", {"0", "1"}) == "1":
            name = input("Sammlungsname: ").strip()
            note = input("Optionale Beschreibung: ").strip()
            try:
                self.database.create_collection(name, note)
                print(self.c("1;32", "✔ Sammlung angelegt."))
            except Exception as exc:
                print(self.c("1;31", f"✖ {exc}"))

    def menu(self) -> int:
        while True:
            self.title("PROVOWARE DUPLIKATE-FINDER 2026 · KONSOLE")
            print(self.c("1;32", "  🟢 Bereit · 🔒 Originaldateien geschützt"))
            print("\n  1) Systemstatus / Selbsttest\n  2) Textdateien durchsuchen\n  3) Duplikate prüfen\n  4) Virtuelle Sammlungen\n  0) Beenden")
            action = self.choice("\nAuswahl: ", {"0", "1", "2", "3", "4"})
            if action == "0":
                print("Programm beendet. Es wurden keine Originaldateien verändert.")
                return 0
            {"1": self.show_status, "2": self.text_search, "3": self.duplicates, "4": self.collections}[action]()
            self.pause()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    configure_testlab_arguments(parser)
    args = parser.parse_args()
    base = ensure_workspace()
    ui = ConsoleUI(base)
    testlab_exit = run_requested_testlab(args, base)
    if testlab_exit is not None:
        return testlab_exit
    if args.selftest:
        checks = run_selftest(base, require_gui=False)
        for check in checks:
            print(("OK" if check.ok else "FEHLER"), check.name, check.detail)
        return 1 if any(not c.ok for c in checks) else 0
    return ui.menu()


if __name__ == "__main__":
    raise SystemExit(main())
