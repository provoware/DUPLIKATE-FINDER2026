from __future__ import annotations

import errno
import sqlite3
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtGui",
    reason="GUI-Fehlergrenzen benötigen die Qt-Systembibliotheken.",
)
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.gui.enhancements import UiEnhancements
from app.gui.result_controller import ResultController


class _Index:
    def isValid(self) -> bool:
        return True

    def row(self) -> int:
        return 0


def test_settings_write_enospc_is_caught_at_gui_boundary(tmp_path: Path):
    fake = SimpleNamespace(
        store=MagicMock(),
        _collect_settings=lambda: {"zoom_percent": 100},
        window=SimpleNamespace(base_dir=tmp_path),
        autosave_info=MagicMock(),
    )
    fake.store.save.side_effect = OSError(errno.ENOSPC, "Datenträger voll")

    with patch("app.gui.enhancements.report_ui_error") as report:
        ok = UiEnhancements._save_settings(fake, show_dialog=False)

    assert ok is False
    report.assert_called_once()
    assert report.call_args.kwargs["area"] == "einstellungen"
    assert report.call_args.kwargs["show_dialog"] is False
    fake.autosave_info.setText.assert_called_once_with(
        "Autosicherung fehlgeschlagen"
    )


def test_settings_permission_error_is_caught_at_gui_boundary(tmp_path: Path):
    fake = SimpleNamespace(
        store=MagicMock(),
        _collect_settings=lambda: {"zoom_percent": 100},
        window=SimpleNamespace(base_dir=tmp_path),
        autosave_info=MagicMock(),
    )
    fake.store.save.side_effect = PermissionError(
        errno.EACCES,
        "Schreibrechte fehlen",
    )

    with patch("app.gui.enhancements.report_ui_error") as report:
        ok = UiEnhancements._save_settings(fake, show_dialog=True)

    assert ok is False
    report.assert_called_once()
    assert report.call_args.kwargs["show_dialog"] is True


def test_sqlite_write_error_does_not_update_result_model(tmp_path: Path):
    path = tmp_path / "treffer.txt"
    database = MagicMock()
    database.set_virtual_item.side_effect = sqlite3.OperationalError(
        "simulierter SQLite-Fehler"
    )
    results_model = MagicMock()
    results_model.path_at.return_value = path
    window = SimpleNamespace(
        base_dir=tmp_path,
        results=SimpleNamespace(currentIndex=lambda: _Index()),
        results_model=results_model,
        database=database,
        result_mark=SimpleNamespace(isChecked=lambda: True),
        result_note=SimpleNamespace(text=lambda: "Notiz"),
        status_label=MagicMock(),
    )

    with patch("app.gui.result_controller.report_ui_error") as report:
        ResultController(window).save_selected_state()

    report.assert_called_once()
    assert report.call_args.kwargs["area"] == "ergebnisstatus"
    results_model.set_marked.assert_not_called()
