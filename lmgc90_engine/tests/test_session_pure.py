"""Tests that never import pylmgc90 — script emission and session façade."""
from __future__ import annotations

from pathlib import Path

import pytest

from lmgc90_core import Project, pre
from lmgc90_engine import EngineSession, PylmgcNotAvailable


def _tiny_project() -> Project:
    p = Project(name="tiny", dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800.0))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    p.add(pre.rigidDisk(r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL"))
    return p


def test_session_repr_and_dirty():
    p = _tiny_project()
    s = EngineSession(p)
    assert s.dirty is True
    assert s.is_materialized is False
    assert "tiny" in repr(s)
    assert s.body_map == {}
    assert s.population_map == {}


def test_emit_pre_script_always_works(tmp_path: Path):
    p = _tiny_project()
    s = EngineSession(p)
    text = s.emit_pre_script()
    assert "from pylmgc90 import pre" in text
    assert "rigidDisk" in text
    assert "STEEL" in text

    out = tmp_path / "pre.py"
    s.emit_pre_script(out)
    assert out.is_file()
    assert "writeDatbox" in out.read_text(encoding="utf-8")


def test_emit_chipy_script(tmp_path: Path):
    p = _tiny_project()
    s = EngineSession(p)
    text = s.emit_chipy_script(dt=1e-4, nb_steps=100)
    assert "chipy.Initialize" in text
    assert "1e-4" in text or "0.0001" in text

    out = tmp_path / "command.py"
    s.emit_chipy_script(out, dt=1e-3, nb_steps=50)
    assert out.is_file()


def test_export_all_without_pylmgc(tmp_path: Path):
    p = _tiny_project()
    s = EngineSession(p)
    paths = s.export_all(tmp_path, try_datbox=True)
    assert "pre" in paths
    assert "command" in paths
    assert paths["pre"].is_file()
    assert paths["command"].is_file()
    # datbox may be absent if pylmgc not installed
    if not s.available():
        assert "datbox" not in paths


def test_materialize_raises_without_pylmgc():
    p = _tiny_project()
    s = EngineSession(p)
    if s.available():
        pytest.skip("pylmgc90 is installed in this environment")
    with pytest.raises(PylmgcNotAvailable):
        s.materialize()


def test_available_bool():
    s = EngineSession(_tiny_project())
    assert isinstance(s.available(), bool)
