from __future__ import annotations

from typing import Any

from app.formatting import format_bytes
from app.gui.scan_controller_support import (
    current_scan_options,
    fail_process,
    prepare_process_start,
    show_validation_error,
)
from app.gui.workers import DuplicateWorker
from app.validation import validate_scan_root


class DuplicateController:
    """Kapselt Duplikatprüfung und Darstellung der Duplikatgruppen."""

    def __init__(self, window: Any) -> None:
        self.window = window

    def start(self) -> None:
        validation = validate_scan_root(self.window.selected_root)
        if show_validation_error(self.window, validation):
            return

        self.window.duplicate_start.setEnabled(False)
        prepare_process_start(self.window, "Hinweis · Duplikatprüfung läuft …")
        self.window.duplicate_summary.setText(
            "Dateigrößen werden gruppiert; nur Kandidaten werden vollständig gehasht."
        )

        options = current_scan_options(self.window)
        worker = DuplicateWorker(
            self.window.selected_root,
            self.window.database,
            options,
        )
        self.window.duplicate_worker = worker
        self.window.process_controller.connect_worker_controls(worker)
        worker.completed.connect(self.finished)
        worker.failed.connect(self.failed)
        worker.start()

    def finished(
        self,
        scanned: int,
        group_count: int,
        error_count: int,
    ) -> None:
        self.refresh_view_from_database()
        self.window.duplicate_start.setEnabled(True)
        self.window._set_process_idle()
        duplicates = sum(item[3] for item in self.window.duplicate_groups_cache)

        if error_count:
            self.window.status_label.setText(
                f"Hinweis · Duplikatprüfung abgeschlossen · {error_count} Datei(en) übersprungen"
            )
        else:
            self.window.status_label.setText("OK · Duplikatprüfung abgeschlossen")

        self.window.activity_label.setText(
            "Aktivität: Duplikatprüfung abgeschlossen"
        )
        self.window.step_label.setText("Schritt: abgeschlossen")
        self.window.eta_label.setText("Restzeit: 0 s")
        self.window.progress_bar.setRange(0, 100)
        self.window.progress_bar.setValue(100)
        self.window.counter_label.setText(
            f"{scanned} Dateien inventarisiert · {group_count} Gruppen · "
            f"{duplicates} Duplikatdateien · {error_count} übersprungen"
        )
        self.window.duplicate_summary.setText(
            f"{group_count} sichere Duplikatgruppen gefunden. "
            "Die Schnellprüfung dient nur als Vorfilter; jede angezeigte Gruppe "
            "wurde vollständig mit SHA-256 bestätigt."
        )
        self.window.dashboard_process_value.setText(
            f"Fertig · {scanned} Dateien · {group_count} Gruppen · "
            f"{error_count} übersprungen"
        )

    def failed(self, message: str) -> None:
        fail_process(
            self.window,
            area="duplikatpruefung",
            button=self.window.duplicate_start,
            status_text="Fehler · Duplikatprüfung gestoppt",
            dialog_title="Duplikatprüfung gestoppt",
            lead_text="Die Prüfung wurde sicher beendet.",
            message=message,
        )

    def refresh_view_from_database(self) -> None:
        self.window.duplicate_groups_cache = (
            self.window.database.duplicate_group_summaries()
        )
        self.fill_groups()

    def fill_groups(self) -> None:
        self.window.duplicate_group_list.clear()
        for index, (_group_id, _digest, size, members) in enumerate(
            self.window.duplicate_groups_cache,
            start=1,
        ):
            wasted = size * (members - 1)
            self.window.duplicate_group_list.addItem(
                f"Gruppe {index} · {members} Dateien · "
                f"{format_bytes(wasted)} mehrfach"
            )

        if self.window.duplicate_groups_cache:
            self.window.duplicate_group_list.setCurrentRow(0)
        else:
            self.window.duplicate_members_model.set_group_id(None)

    def show_group(self, row: int) -> None:
        if row < 0 or row >= len(self.window.duplicate_groups_cache):
            self.window.duplicate_members_model.set_group_id(None)
            return

        group_id, digest, size, members = self.window.duplicate_groups_cache[row]
        self.window.duplicate_members_model.set_group_id(
            group_id,
            size=size,
            count=members,
        )
        self.window.duplicate_summary.setText(
            f"Gruppe {row + 1}: {members} vollständig identische Dateien · "
            f"je {format_bytes(size)} · SHA-256 {digest[:16]}…"
        )
