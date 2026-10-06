from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QMessageBox

from app.formatting import format_bytes
from app.process_control import ProgressInfo
from app.progress_format import format_eta


class ProcessUiController:
    """Kapselt die sichtbare Steuerung laufender Hintergrundvorgänge."""

    def __init__(self, window: Any) -> None:
        self.window = window
        self._paused = False

    def connect_worker_controls(self, worker: Any) -> None:
        self._paused = False
        self.window.pause_button.setText("Pause")
        self.window.pause_button.setEnabled(True)
        self.window.cancel_button.setEnabled(True)
        worker.progress.connect(self.on_progress)
        worker.paused_changed.connect(self.on_pause_changed)
        worker.cancelled.connect(self.process_cancelled)

    def active_worker(self) -> Any | None:
        for worker in (self.window.search_worker, self.window.duplicate_worker):
            if worker is not None and worker.isRunning():
                return worker
        return None

    def toggle_pause(self) -> None:
        worker = self.active_worker()
        if worker is None:
            return
        if self._paused:
            worker.resume()
        else:
            worker.pause()

    def on_pause_changed(self, paused: bool) -> None:
        self._paused = paused
        if paused:
            self.window.pause_button.setText("Fortsetzen")
            self.window.status_label.setText("Hinweis · Pausiert")
            self.window.activity_label.setText(
                "Aktivität: pausiert – sicherer Zwischenstand"
            )
            self.window.eta_label.setText("Restzeit: angehalten")
            return

        self.window.pause_button.setText("Pause")
        self.window.status_label.setText("Hinweis · Vorgang läuft …")
        self.window.activity_label.setText("Aktivität: Verarbeitung fortgesetzt")
        self.window.eta_label.setText("Restzeit: wird neu berechnet")

    def cancel_active_process(self) -> None:
        worker = self.active_worker()
        if worker is None:
            return

        answer = QMessageBox.question(
            self.window,
            "Vorgang abbrechen?",
            "Der laufende Vorgang wird sauber beendet. Bereits gelesene "
            "Originaldateien bleiben unverändert.\n\nWirklich abbrechen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.window.cancel_button.setEnabled(False)
        self.window.pause_button.setEnabled(False)
        self.window.status_label.setText(
            "Hinweis · Abbruch wird sicher abgeschlossen …"
        )
        self.window.activity_label.setText(
            "Aktivität: aktueller Dateischritt wird beendet"
        )
        worker.cancel()

    def process_cancelled(self, message: str) -> None:
        self.window.search_button.setEnabled(True)
        self.window.duplicate_start.setEnabled(True)
        self.set_idle()
        self.window.status_label.setText("Hinweis · Vorgang abgebrochen")
        self.window.activity_label.setText("Aktivität: sauber beendet")
        self.window.step_label.setText("Schritt: abgebrochen")
        self.window.eta_label.setText("Restzeit: –")
        self.window.progress_bar.setRange(0, 100)
        self.window.progress_bar.setValue(0)
        self.window.counter_label.setText(message)
        self.window.dashboard_process_value.setText("Abgebrochen")

    def on_progress(self, info: ProgressInfo) -> None:
        self.window.step_label.setText(f"Schritt: {info.step}")
        if info.total <= 0:
            self.window.progress_bar.setRange(0, 0)
            self.window.progress_bar.setFormat("Dateien werden erfasst …")
            self.window.eta_label.setText(
                "Restzeit: wird nach der Erfassung berechnet"
            )
            if info.current > 0:
                self.window.counter_label.setText(
                    f"{info.current} Dateien bisher erfasst"
                )
                self.window.dashboard_process_value.setText(
                    f"Erfassen · {info.current} Dateien"
                )
            return

        self.window.progress_bar.setRange(0, 100)
        self.window.progress_bar.setFormat("%p %")
        self.window.progress_bar.setValue(info.percent)
        self.window.eta_label.setText(
            "Restzeit: " + format_eta(info.eta_seconds)
        )
        rate = (
            f"{info.items_per_second:.1f} Dateien/s"
            if info.items_per_second > 0
            else "Geschwindigkeit wird ermittelt"
        )
        amount = (
            format_bytes(info.processed_bytes)
            if info.processed_bytes > 0
            else "nur Metadaten"
        )
        self.window.counter_label.setText(
            f"{info.current}/{info.total} · {rate} · {amount}"
        )
        self.window.dashboard_process_value.setText(
            f"{rate} · {amount} · Rest {format_eta(info.eta_seconds)}"
        )

    def set_idle(self) -> None:
        self.window.pause_button.setEnabled(False)
        self.window.cancel_button.setEnabled(False)
        self.window.pause_button.setText("Pause")
        self._paused = False
