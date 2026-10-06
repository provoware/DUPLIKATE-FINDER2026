from __future__ import annotations

import argparse
import html
import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication, QWidget

from app.core.duplicates import scan_duplicate_groups
from app.core.search import TextSearcher
from app.gui.enhancements import UiEnhancements
from app.gui.main_window import MainWindow
from app.gui.theme import apply_accessible_theme
from app.models.entities import SearchJob
from app.startup.selftest import run_selftest
from app.storage.database import Database

PROFILES = (
    ("Basis 800x600", 800, 600, 100),
    ("Standard 1024x768", 1024, 768, 100),
    ("Grossschrift 150 Prozent", 1280, 800, 150),
    ("Grossschrift 200 Prozent", 1280, 800, 200),
)

CRITICAL_BY_PAGE = {
    0: ["safety_banner", "locked_write_features", "dashboard_go_search", "dashboard_go_duplicates", "dashboard_go_collections", "diagnostic_dashboard", "dashboard_process_metrics", "dashboard_resource_metrics", "cpu_limiter", "dashboard_tools", "autosave_info", "process_pause", "process_cancel"],
    1: ["search_root", "search_choose_root", "search_query", "search_names", "search_contents", "search_start", "exclude_python_dirs", "excluded_types_button", "search_info"],
    2: ["results_table", "result_mark", "result_note", "result_save_meta", "result_collection", "result_add_collection"],
    3: ["duplicate_start", "duplicate_root", "duplicate_filter_info", "duplicate_group_list", "duplicate_members", "duplicate_safety_note"],
    4: ["collection_name", "collection_note", "collection_create", "collection_list", "collection_items", "collection_remove", "collection_safety_note"],
    5: ["journal_info"], 6: ["help_safety"],
}


@dataclass
class Result:
    area: str
    check: str
    ok: bool
    detail: str


def create_fixture(root: Path) -> None:
    (root / "texte").mkdir(parents=True)
    (root / "duplikate").mkdir(parents=True)
    (root / "texte" / "bericht_alpha.txt").write_text("Start\nNadelwort im ersten Text.\nNoch eine Zeile mit Nadelwort.\n", encoding="utf-8")
    (root / "texte" / "notiz_beta.md").write_text("# Notiz\nHier steht ebenfalls Nadelwort.\n", encoding="utf-8")
    (root / "texte" / "kein_treffer.txt").write_text("vollkommen anderer Inhalt\n", encoding="utf-8")
    duplicate = b"PROVOWARE-DUPLIKAT-TEST-2026\n"
    (root / "duplikate" / "kopie_a.bin").write_bytes(duplicate)
    (root / "duplikate" / "kopie_b.bin").write_bytes(duplicate)
    (root / "duplikate" / "gleich_gross_anderer_inhalt.bin").write_bytes(b"X" * len(duplicate))


def core_checks() -> list[Result]:
    results = []
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "fixture"
        create_fixture(root)
        job = SearchJob(root=root, query="Nadelwort", search_names=True, search_contents=True)
        hits = TextSearcher().search(job)
        results.append(Result("Funktion", "Textsuche Testdateien", len(hits) == 3, f"{len(hits)} Treffer erwartet: 3"))
        scanned, groups = scan_duplicate_groups(root)
        exact = len(groups) == 1 and len(groups[0].paths) == 2
        results.append(Result("Funktion", "Duplikatprüfung Testdateien", exact, f"{scanned} Dateien · {len(groups)} Gruppen"))
        db = Database(Path(temp) / "state.sqlite3")
        db.initialize()
        target = root / "texte" / "bericht_alpha.txt"
        db.set_virtual_item(target, True, "Abnahme")
        state = db.virtual_item(target)
        results.append(Result("Daten", "Virtuelle Markierung", state.marked and state.note == "Abnahme", state.note))
        cid = db.create_collection("Abnahme")
        db.add_collection_item(cid, target, "nur virtuell")
        items = db.collection_items(cid)
        results.append(Result("Daten", "Virtuelle Sammlung", len(items) == 1 and items[0].path == target, f"{len(items)} Eintrag"))
    return results


def visible_inside(window: MainWindow, widget: QWidget) -> bool:
    if not widget.isVisible() or widget.width() <= 0 or widget.height() <= 0:
        return False
    top_left = widget.mapTo(window, widget.rect().topLeft())
    return window.rect().intersects(QRect(top_left, widget.size()))


def screenshot_is_plausible(path: Path) -> bool:
    from PySide6.QtGui import QImage
    image = QImage(str(path))
    if image.isNull():
        return False
    colors = set()
    sx, sy = max(1, image.width() // 30), max(1, image.height() // 20)
    for y in range(0, image.height(), sy):
        for x in range(0, image.width(), sx):
            colors.add(image.pixelColor(x, y).rgba())
            if len(colors) >= 12:
                return True
    return False


def ui_checks(output: Path) -> tuple[list[Result], list[dict]]:
    app = QApplication.instance() or QApplication([])
    results, shots = [], []
    for label, width, height, zoom in PROFILES:
        apply_accessible_theme(app, zoom)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for name in ("data", "logs", "recovery", "quarantine"):
                (base / name).mkdir(parents=True, exist_ok=True)
            db = Database(base / "data" / "ui.sqlite3")
            db.initialize()
            window = MainWindow(base, db)
            enhancement = UiEnhancements(window, base, db, install_global_filter=False)
            enhancement._apply_zoom(zoom)
            window.resize(width, height)
            window.show()
            app.processEvents()
            hint = window.minimumSizeHint()
            if zoom == 200 or (width == 800 and height == 600):
                largest = sorted(
                    (
                        (widget.minimumSizeHint().width(), widget.minimumSizeHint().height(),
                         widget.objectName() or "-", type(widget).__name__)
                        for widget in window.findChildren(QWidget)
                        if widget.isVisible()
                    ),
                    reverse=True,
                )[:12]
                print(f"UI-DIAG | {label} | Fensterbedarf {hint.width()}x{hint.height()}")
                for min_w, min_h, name, kind in largest:
                    print(f"UI-DIAG | {label} | {min_w}x{min_h} | {kind} | {name}")
                for page_index in range(window.pages.count()):
                    page_hint=window.pages.widget(page_index).minimumSizeHint()
                    print(f"UI-DIAG | {label} | Seite {page_index} | {page_hint.width()}x{page_hint.height()}")
            results.append(Result("Oberfläche", f"{label} Mindestlayout", hint.width() <= width and hint.height() <= height, f"Bedarf {hint.width()}x{hint.height()} bei Fenster {width}x{height}"))
            compact_navigation = width < 960
            window.compact_nav.setCurrentIndex(window.PAGE_HELP)
            app.processEvents()
            selection_sync = window.nav.currentRow() == window.PAGE_HELP
            window.nav.setCurrentRow(window.PAGE_SEARCH)
            app.processEvents()
            selection_sync = selection_sync and window.compact_nav.currentIndex() == window.PAGE_SEARCH
            navigation_visible = (
                window.compact_nav.isVisible() == compact_navigation
                and window.nav.isVisible() != compact_navigation
            )
            results.append(Result(
                "Bedienung", f"{label} Bereichsnavigation",
                navigation_visible and selection_sync,
                "passende Navigation sichtbar; Auswahl bleibt in beiden Ansichten synchron"
                if navigation_visible and selection_sync
                else "Navigation fehlt, ist doppelt sichtbar oder Auswahl wurde nicht synchronisiert",
            ))
            for page_index in range(window.pages.count()):
                window.nav.setCurrentRow(page_index)
                app.processEvents()
                missing = []
                for name in CRITICAL_BY_PAGE[page_index]:
                    widget = window.findChild(QWidget, name)
                    if widget is None or not visible_inside(window, widget):
                        missing.append(name)
                ok = not missing
                results.append(Result("Oberfläche", f"{label} · Seite {page_index}", ok, "alle Kernelemente sichtbar" if ok else "nicht sichtbar: " + ", ".join(missing)))
                file_name = f"ui_{width}x{height}_{zoom}_seite_{page_index}.png"
                image_path = output / file_name
                window.grab().save(str(image_path))
                plausible = screenshot_is_plausible(image_path)
                results.append(Result("Bild", file_name, plausible, "Bildinhalt plausibel" if plausible else "Bild wirkt leer/einfarbig"))
                shots.append({"profile": label, "page": page_index, "file": file_name, "ok": ok and plausible})
            enhancement.dispose()
            window.close()
            app.processEvents()
            del enhancement
    return results, shots


def write_html(output: Path, results: list[Result], shots: list[dict]) -> None:
    passed, total = sum(1 for r in results if r.ok), len(results)
    cards = []
    for shot in shots:
        state = "OK" if shot["ok"] else "FEHLER"
        css = "ok" if shot["ok"] else "bad"
        cards.append(f'<article class="shot"><h3>{html.escape(shot["profile"])} · Seite {shot["page"]}</h3><div class="badge {css}">{state}</div><a href="{html.escape(shot["file"])}"><img src="{html.escape(shot["file"])}" alt="Prüfbild"></a></article>')
    rows = "".join(f"<tr><td>{'✅' if r.ok else '❌'}</td><td>{html.escape(r.area)}</td><td>{html.escape(r.check)}</td><td>{html.escape(r.detail)}</td></tr>" for r in results)
    document = f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PROVOWARE Autonome Abnahme</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;background:#eef3f8;color:#17202a}}header{{background:#102a43;color:white;padding:24px}}main{{max-width:1500px;margin:auto;padding:20px}}.summary{{font-size:1.25rem;font-weight:800}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:16px}}.shot{{background:white;border:1px solid #a8b4c0;border-radius:10px;padding:12px;box-shadow:0 2px 7px #0002}}.shot img{{width:100%;height:auto;border:1px solid #66788a}}.badge{{display:inline-block;padding:4px 9px;border-radius:999px;font-weight:800;margin-bottom:8px}}.ok{{background:#d8f5df;color:#075b2a}}.bad{{background:#ffe1e1;color:#8f0000}}table{{width:100%;border-collapse:collapse;background:white;margin:20px 0}}th,td{{border:1px solid #b5c0ca;padding:8px;text-align:left;vertical-align:top}}th{{background:#dce8f3}}</style></head>
<body><header><h1>PROVOWARE DUPLIKATE-FINDER 2026 · Autonome Abnahme</h1><div class="summary">{passed}/{total} Prüfungen grün</div></header><main><h2>Maschinenprüfung</h2><table><tr><th>Status</th><th>Bereich</th><th>Prüfung</th><th>Detail</th></tr>{rows}</table><h2>Visuelles Prüfraster</h2><div class="grid">{''.join(cards)}</div></main></body></html>"""
    (output / "index.html").write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/abnahme"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = core_checks()
    with tempfile.TemporaryDirectory() as temp:
        checks = run_selftest(Path(temp), require_gui=True)
        results.extend(Result("Start", c.name, c.ok, c.detail) for c in checks)
    ui_results, shots = ui_checks(args.output)
    results.extend(ui_results)
    write_html(args.output, results, shots)
    (args.output / "report.json").write_text(json.dumps({"results": [asdict(r) for r in results], "screenshots": shots}, ensure_ascii=False, indent=2), encoding="utf-8")
    bad = [r for r in results if not r.ok]
    print(f"ABNAHME: {len(results)-len(bad)}/{len(results)} grün")
    for item in bad:
        print(f"FEHLER | {item.area} | {item.check} | {item.detail}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
