"""Vague 3 — scene geometry + history stack (headless, no Qt required for geometry)."""
from __future__ import annotations

from lmgc90_core import pre
from lmgc90_gui import ProjectController
from lmgc90_gui.utils.scene_geometry import build_scene_geometry, color_rgb


def test_color_rgb():
    assert color_rgb("BLUEx")[2] > 200
    assert color_rgb("unknown")  # default


def test_scene_geometry_avatars_and_pop():
    ctrl = ProjectController()
    ctrl.new_project("v3", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    ctrl.add(pre.rigidDisk(r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL", color="BLUEx"))
    ctrl.add(pre.smoothWall(l=2.0, h=0.1, center=[0.0, -0.5], model="rigid", material="STEEL", color="GRAYx"))
    from lmgc90_core import GranuloConfig
    ctrl.deposit(GranuloConfig(
        nb_particles=12, radius_min=0.02, radius_max=0.03,
        container_type="Box2D", container_params={"lx": 0.5, "ly": 0.5},
        material_name="STEEL", model_name="rigid", avatar_type="rigidDisk",
        color="CYANx", seed=1, dimension=2,
    ))
    geom = build_scene_geometry(ctrl.project)
    assert geom.n_avatars == 2
    assert geom.n_population_particles == 12
    assert geom.n_items >= 2 + 12
    assert geom.bounds is not None
    assert any(d.source == "population" for d in geom.discs)
    assert any(s.label == "smoothWall" for s in geom.segments)


def test_history_describe_stack():
    ctrl = ProjectController()
    ctrl.new_project("h", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    stack = ctrl.project.history.describe_stack()
    assert len(stack) >= 2
    assert any("material" in s.lower() or "STEEL" in s or "add" in s.lower() for s in stack)
    ctrl.undo()
    assert len(ctrl.project.history.describe_stack()) == len(stack) - 1
