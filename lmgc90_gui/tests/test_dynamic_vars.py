"""Dynamic variables — SafeEvaluator + project context."""
from __future__ import annotations

from lmgc90_core import pre
from lmgc90_gui import ProjectController
from lmgc90_gui.utils.eval_context import build_eval_context, resolve_dynamic_vars
from lmgc90_gui.utils.safe_eval import safe_eval


def test_resolve_chain_and_avatar_access():
    ctrl = ProjectController()
    ctrl.new_project("dv", 2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    ctrl.add(pre.rigidDisk(r=0.1, center=[1.5, 2.0], model="rigid", material="STEEL", color="BLUEx"))
    ctrl.set_dynamic_var("thickness", "0.05")
    ctrl.set_dynamic_var("radius", "thickness * 3")
    ctrl.set_dynamic_var("x0", "avatar[0].x")
    resolved = resolve_dynamic_vars(ctrl.project)
    assert resolved["thickness"] == 0.05
    assert abs(resolved["radius"] - 0.15) < 1e-12
    assert abs(resolved["x0"] - 1.5) < 1e-12
    ctx = build_eval_context(ctrl.project)
    assert abs(safe_eval("avatar[0].y + thickness", ctx) - 2.05) < 1e-12
    assert abs(safe_eval("material['STEEL'].density", ctx) - 7800) < 1e-9
    assert safe_eval("len(avatar)", ctx) == 1
    assert safe_eval("avatars_by_color('BLUEx')[0].radius", ctx) == 0.1


def test_persistence_roundtrip(tmp_path):
    ctrl = ProjectController()
    ctrl.new_project("dv2", 2)
    ctrl.set_dynamic_var("a", "1.0")
    ctrl.set_dynamic_var("b", "a * 2")
    path = tmp_path / "p.lmgc90"
    ctrl.save_project(path)
    ctrl2 = ProjectController()
    ctrl2.load_project(path)
    assert "a" in ctrl2.project.dynamic_vars
    r = resolve_dynamic_vars(ctrl2.project)
    assert r["b"] == 2.0
