from __future__ import annotations

from typing import Any

from app.gui.scan_controller_support import (
    current_scan_options,
    fail_process,
    prepare_process_start,
    show_validation_error,
)
from app.gui.workers import SearchWorker
from app.models.entities import SearchJob
from app.validation import validate_search_request


class SearchController:
    """Kapselt Start, Abschluss und Fehlerbehandlung der Textsuche."""

    def __init__(self, window: Any) -> None:
        self.window = window

    def start(self) -> None:
        query = self.window.query_edit.text().strip()
        validation = validate_search_request(
            self.window.selected_root,
            query,
            self.window.names_box.isChecked(),
            self.window.contents_box.isChecked(),
        )
        if show_validation_error(self.window, validation):
            return

        job = SearchJob(
            root=self.window.selected_root,
            query=query,
            search_names=self.window.names_box.isChecked(),
            search_contents=self.window.contents_box.isChecked(),
        )
        self.window.search_button.setEnabled(False)
        prepare_process_start(self.window, "Hinweis · Textsuche läuft …")
        self.window.counter_label.setText("Dateien werden ermittelt …")

        options = current_scan_options(self.window)
        worker = SearchWorker(job, self.window.database, options)
        self.window.search_worker = worker
        self.window.process_controller.connect_worker_controls(worker)
        worker.completed.connect(self.finished)
        worker.failed.connect(self.failed)
        worker.start()

    def finished(
        self,
        job: SearchJob,
        job_id: int,
        hit_count: int,
        error_count: int,
    ) -> None:
        self.window.last_search_job_id = job_id
        self.window.results_model.set_job(job_id, hit_count)
        self.window.search_button.setEnabled(True)
        self.window._set_process_idle()

        if error_count:
            self.window.status_label.setText(
                f"Hinweis · Textsuche abgeschlossen · {error_count} Datei(en) übersprungen"
            )
        else:
            self.window.status_label.setText("OK · Textsuche abgeschlossen")

        self.window.activity_label.setText("Aktivität: Suche abgeschlossen")
        self.window.progress_bar.setRange(0, 100)
        self.window.progress_bar.setValue(100)
        self.window.counter_label.setText(
            f"{job.scanned_files} Textdateien geprüft · {hit_count} Treffer · "
            f"{error_count} übersprungen"
        )
        self.window.result_info.setText(
            f"{hit_count} Treffer · {error_count} Lesefehler · SQLite-Seiten · "
            f"max. {self.window.results_model.page_size * self.window.results_model.max_pages} "
            "Zeilen im GUI-Puffer"
        )
        self.window.dashboard_process_value.setText(
            f"Fertig · {job.scanned_files} Dateien · {hit_count} Treffer · "
            f"{error_count} übersprungen"
        )
        self.window.nav.setCurrentRow(self.window.PAGE_RESULTS)

    def failed(self, message: str) -> None:
        fail_process(
            self.window,
            area="textsuche",
            button=self.window.search_button,
            status_text="Fehler · Textsuche gestoppt",
            dialog_title="Suche gestoppt",
            lead_text="Die Suche wurde sicher beendet.",
            message=message,
        )
