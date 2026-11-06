from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtWidgets")

from PyQt6.QtWidgets import QApplication, QMessageBox

from lmgc90_gui import ProjectController
from lmgc90_gui.views.tabs.compute_tab import create_compute_tab


def test_run_refuses_to_start_without_datbox(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    controller = ProjectController()
    controller.prefs.confirm_run = False
    work = tmp_path / "run"
    work.mkdir()
    (work / "command.py").write_text("pass\n", encoding="utf-8")
    tab = create_compute_tab()
    tab.bind_controller(controller)
    tab.work_edit.setText(str(work))

    warnings = []
    journal_warnings = []
    workers = []
    monkeypatch.setattr(
        QMessageBox, "warning",
        lambda *args: warnings.append(args),
    )
    monkeypatch.setattr(
        controller.journal, "warning",
        lambda message: journal_warnings.append(message),
    )
    monkeypatch.setattr(
        "lmgc90_gui.workers.compute_worker.create_compute_worker",
        lambda *args, **kwargs: workers.append((args, kwargs)),
    )

    tab._run()

    assert not workers
    assert len(warnings) == 1
    assert "No DATBOX directory found" in warnings[0][2]
    assert "DATBOX missing" in tab.status_lbl.text()
    assert "DATBOX" in journal_warnings[0]
    assert "WARNING" in tab.log_view.toPlainText()

    tab.deleteLater()
    app.processEvents()


def test_run_accepts_existing_datbox_and_starts_worker(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    controller = ProjectController()
    controller.prefs.confirm_run = False
    work = tmp_path / "run"
    work.mkdir()
    (work / "command.py").write_text("pass\n", encoding="utf-8")
    (work / "DATBOX").mkdir()
    tab = create_compute_tab()
    tab.bind_controller(controller)
    tab.work_edit.setText(str(work))

    class Signal:
        def connect(self, callback):
            pass

    class Worker:
        line_out = Signal()
        finished = Signal()
        failed = Signal()

    class Runner:
        worker = Worker()

        def start(self):
            pass

    started = []
    monkeypatch.setattr(
        "lmgc90_gui.workers.compute_worker.create_compute_worker",
        lambda *args, **kwargs: started.append((args, kwargs)) or Runner(),
    )

    tab._run()

    assert len(started) == 1
    assert started[0][0][0] == work
    assert tab.status_lbl.text() == "Calculating…"

    tab.deleteLater()
    app.processEvents()
