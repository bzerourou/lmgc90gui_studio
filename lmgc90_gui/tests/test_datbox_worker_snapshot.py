from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtCore")

from lmgc90_core import Project
from lmgc90_gui.utils.preferences import Preferences
from lmgc90_gui.workers.datbox_worker import create_datbox_worker


def test_datbox_worker_generates_from_project_and_preferences_snapshot(tmp_path):
    project = Project(name="snapshot-before", dimension=2)

    class UncopyableHistoryEntry:
        def __deepcopy__(self, memo):
            memo[id(self)] = self
            raise AssertionError("project history must not be deep-copied")

    project.history._undo.append(UncopyableHistoryEntry())
    preferences = Preferences(nb_steps=17)
    controller = SimpleNamespace(
        project=project,
        prefs=preferences,
        pylmgc_available=lambda: False,
    )
    runner = create_datbox_worker(
        controller,
        tmp_path,
        try_live_datbox=False,
        chipy_params=preferences.chipy_params(),
        use_loop=False,
    )

    assert runner.worker.session.project.history._undo == []
    assert runner.worker.session.project.history._redo == []

    project.name = "project-after"
    preferences.nb_steps = 23

    runner.worker.run()

    pre_text = (tmp_path / "pre.py").read_text(encoding="utf-8")
    command_text = (tmp_path / "command.py").read_text(encoding="utf-8")
    assert "project 'snapshot-before'" in pre_text
    assert "project-after" not in pre_text
    assert "nb_steps    = 17" in command_text
