"""Vague 2 — journal, preferences, prepare_run_directory (headless)."""
from __future__ import annotations

from pathlib import Path

from lmgc90_core import pre
from lmgc90_gui import ProjectController
from lmgc90_gui.utils.app_journal import AppJournal, get_journal
from lmgc90_gui.utils.preferences import Preferences, load_preferences, save_preferences


def test_journal_ring():
    j = AppJournal(maxlen=5)
    for i in range(10):
        j.info(f"msg{i}")
    entries = j.entries()
    assert len(entries) == 5
    assert entries[-1].message == "msg9"
    assert "msg9" in j.text()


def test_preferences_roundtrip(tmp_path: Path):
    prefs = Preferences(dt=2e-3, nb_steps=50, python_executable="python3")
    path = tmp_path / "prefs.json"
    save_preferences(prefs, path)
    loaded = load_preferences(path)
    assert loaded.dt == 2e-3
    assert loaded.nb_steps == 50
    assert loaded.python_executable == "python3"
    assert "dt" in loaded.chipy_params()


def test_prepare_run_directory(tmp_path: Path):
    ctrl = ProjectController()
    ctrl.new_project("w2", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    ctrl.add(pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL"))
    ctrl.prefs.nb_steps = 100
    ctrl.prefs.dt = 1e-4
    ctrl.prefs.auto_write_datbox = False  # no pylmgc in CI

    out = tmp_path / "run"
    paths = ctrl.prepare_run_directory(out)
    assert paths["pre"].is_file()
    assert paths["command"].is_file()
    text = paths["command"].read_text(encoding="utf-8")
    assert "chipy.Initialize" in text
    assert "100" in text or "1e-4" in text or "0.0001" in text
    assert ctrl.work_dir == out
    assert any("Preparing" in e.message or "DATBOX" in e.message for e in ctrl.journal.entries())
