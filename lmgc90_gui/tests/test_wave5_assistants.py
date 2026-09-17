"""Vague 5 — masonry + deformable (headless)."""
from __future__ import annotations

from lmgc90_core import MasonryConfig, Material, MaterialType, Model, expand_masonry, pre
from lmgc90_gui import ProjectController


def test_expand_patterns():
    assert len(expand_masonry(MasonryConfig(n_courses=3, n_columns=4, bond="stack"))) == 12
    # standard without fill_ends: same as legacy masonery_wizard
    assert len(expand_masonry(MasonryConfig(
        n_courses=2, n_columns=3, bond="standard", fill_ends=False,
    ))) == 6
    assert len(expand_masonry(MasonryConfig(
        n_courses=2, n_columns=3, bond="running",
    ))) == 6
    # flemish: still n_courses * n_columns placements (variable width)
    assert len(expand_masonry(MasonryConfig(
        n_courses=2, n_columns=4, bond="flemish",
    ))) == 8


def test_apply_masonry_on_project():
    ctrl = ProjectController()
    ctrl.new_project("wall", 2)
    ctrl.add(pre.material(name="brick", materialType="RIGID", density=1800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    bricks = ctrl.apply_masonry(MasonryConfig(
        n_courses=2, n_columns=2, bond="stack", group_name="mur",
    ))
    assert len(bricks) == 4
    assert "mur" in ctrl.project.avatar_groups
    text = ctrl.emit_pre_script()
    assert "rigidPolygon" in text or "vertices" in text


def test_deformable_mesh_with_contactor_and_gap():
    ctrl = ProjectController()
    ctrl.new_project("def", 2)
    ctrl.add_material(Material(
        name="ELAS1", material_type=MaterialType.ELAS, density=2500,
        properties={"young": 7e10, "nu": 0.3},
    ))
    ctrl.add_model(Model(name="femxx", physics="MECAx", element="T3xxx", dimension=2))
    ctrl.add_model(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    mesh = pre.meshed_rectangle(
        lx=1.0, ly=0.4, nx=6, ny=3, center=[0.0, 0.5],
        model="femxx", material="ELAS1", color="CYANx",
        contactors=[{"shape": "CLxxx", "color": "CYANx"}],
    )
    ctrl.add_avatar(mesh)
    floor = pre.smoothWall(l=2.0, h=0.08, center=[0.0, -0.1], model="rigid", material="STEEL", color="GRAYx")
    ctrl.add_avatar(floor)
    ctrl.add_law(pre.tact_behav(name="gap", law="GAP_SGR_CLB", fric=0.3))
    ctrl.add_visibility(pre.see_table(
        CorpsCandidat="MAILx", candidat="CLxxx", colorCandidat="CYANx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="GRAYx",
        behav="gap", alert=0.05,
    ))
    assert ctrl.project.avatars[0].avatar_type.value == "mesh"
