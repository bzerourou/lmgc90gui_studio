"""Vague 2 — journal, preferences, prepare_run_directory (headless)."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

from lmgc90_core import pre
from lmgc90_gui import ProjectController
from lmgc90_gui.utils.app_journal import AppJournal, get_journal
from lmgc90_gui.utils.preferences import Preferences, load_preferences, save_preferences
from lmgc90_gui.workers.compute_worker import create_compute_worker


def test_python_executable_defaults_to_current_interpreter():
    assert Preferences().python_executable == sys.executable
    assert (
        inspect.signature(create_compute_worker).parameters["python_executable"].default
        == sys.executable
    )


def test_journal_ring():
    j = AppJournal(maxlen=5)
    for i in range(10):
        j.info(f"msg{i}")
    entries = j.entries()
    assert len(entries) == 5
    assert entries[-1].message == "msg9"
    assert "msg9" in j.text()


def test_preferences_roundtrip(tmp_path: Path):
    prefs = Preferences(
        dt=2e-3,
        nb_steps=50,
        python_executable="python3",
        auto_detect_contactors=True,
        chipy_options={"advanced_write_out_dof": False, "use_RBDY3": True},
    )
    path = tmp_path / "prefs.json"
    save_preferences(prefs, path)
    loaded = load_preferences(path)
    assert loaded.dt == 2e-3
    assert loaded.nb_steps == 50
    assert loaded.python_executable == "python3"
    assert loaded.auto_detect_contactors is True
    assert loaded.chipy_params()["use_SelectProx_macro"] is False
    assert "dt" in loaded.chipy_params()
    assert loaded.chipy_params()["advanced_write_out_dof"] is False
    assert loaded.chipy_params()["use_RBDY3"] is True


def test_contactors_default_to_select_prox_macro():
    prefs = Preferences(chipy_options={"use_SelectProx_macro": False})

    assert prefs.auto_detect_contactors is False
    assert prefs.chipy_params()["use_SelectProx_macro"] is True


def test_contactors_preference_selects_macro_or_inferred_detector():
    ctrl = ProjectController()
    ctrl.new_project("contactor-preference", dimension=3)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx3D", dimension=3))
    ctrl.add(pre.rigidSphere(
        r=0.1, center=[0, 0, 0], model="rigid", material="STEEL",
    ))

    default_script = ctrl.emit_chipy_script()
    assert default_script.count("chipy.SelectProxTactors()") == 1
    assert "chipy.SPSPx_SelectProxTactors()" not in default_script

    ctrl.prefs.auto_detect_contactors = True
    automatic_script = ctrl.emit_chipy_script()
    assert "chipy.SelectProxTactors()" not in automatic_script
    assert automatic_script.count("chipy.SPSPx_SelectProxTactors()") == 1


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


def test_export_all_uses_saved_chipy_preferences(tmp_path: Path):
    ctrl = ProjectController()
    ctrl.new_project("export-prefs", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    ctrl.add(pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL"))
    ctrl.prefs.dt = 2e-4
    ctrl.prefs.nb_steps = 37
    ctrl.prefs.chipy_options = {"use_SelectProx_macro": True}

    direct_script = ctrl.emit_chipy_script()
    paths = ctrl.export_all(tmp_path / "export", try_datbox=False)
    command = paths["command"].read_text(encoding="utf-8")

    assert "dt          = 0.0002" in command
    assert "nb_steps    = 37" in command
    assert "chipy.SelectProxTactors()" in command
    assert command == direct_script


def test_project_modified_state_tracks_edits_saves_and_replacements(tmp_path: Path):
    ctrl = ProjectController()
    ctrl.new_project("modified-state", dimension=2)
    assert not ctrl.modified

    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    assert ctrl.modified
    ctrl.set_dimension(3)
    assert ctrl.modified

    path = tmp_path / "saved.lmgc90"
    ctrl.save_project(path)
    assert not ctrl.modified

    ctrl.set_dimension(2)
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    assert ctrl.modified
    ctrl.load_project(path)
    assert not ctrl.modified
