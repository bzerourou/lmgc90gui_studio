"""Vague 1 — full scene path without Qt: materials → bodies → loop/granulo → laws → DOF → export."""
from __future__ import annotations

from pathlib import Path

from lmgc90_core import DOFOperation, GranuloConfig, Loop, PostProCommand, pre
from lmgc90_gui import ProjectController


def _base(ctrl: ProjectController) -> None:
    ctrl.new_project("wave1", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.material(name="SAND", materialType="RIGID", density=2500))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))


def test_wave1_complete_scene(tmp_path: Path):
    ctrl = ProjectController()
    _base(ctrl)

    # wall + template disk
    wall = pre.smoothWall(
        l=2.0, h=0.1, center=[0.0, -0.05],
        model="rigid", material="STEEL", color="GRAYx", nb_polyg=12,
    )
    ctrl.add(wall)
    seed = pre.rigidDisk(
        r=0.05, center=[0.0, 0.2], model="rigid", material="SAND", color="BLUEx",
    )
    ctrl.add(seed)

    # loop
    loop = Loop(
        loop_type="circle",
        model_avatar_id=seed.avatar_id,
        count=6,
        radius=0.4,
        group_name="ring",
    )
    generated = ctrl.apply_loop(loop)
    assert len(generated) == 6
    assert "ring" in ctrl.project.avatar_groups

    # granulo SoA
    cfg = GranuloConfig(
        nb_particles=30,
        radius_min=0.01,
        radius_max=0.02,
        container_type="Box2D",
        container_params={"lx": 0.8, "ly": 0.5},
        material_name="SAND",
        model_name="rigid",
        avatar_type="rigidDisk",
        color="CYANx",
        group_name="depot",
        seed=7,
        dimension=2,
    )
    pop = ctrl.deposit(cfg)
    assert len(pop) == 30
    assert len(ctrl.project.populations) == 1

    # contact + visibility
    law = pre.tact_behav(name="st_sd", law="IQS_CLB", fric=0.3)
    ctrl.add_law(law)
    rule = pre.see_table(
        CorpsCandidat="RBDY2", candidat="DISKx", colorCandidat="BLUEx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="GRAYx",
        behav="st_sd", alert=0.05,
    )
    ctrl.add_visibility(rule)
    assert len(ctrl.project.laws) == 1
    assert len(ctrl.project.visibility) == 1

    # DOF on wall
    ctrl.add_dof(DOFOperation(
        "imposeDrivenDof", "avatar", wall.avatar_id,
        {"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    assert len(ctrl.project.operations) == 1

    # postpro
    ctrl.add_postpro(PostProCommand(name="SOLVER INFORMATIONS", step=10))
    assert len(ctrl.project.postpro) == 1

    # export
    out = tmp_path / "wave1_out"
    paths = ctrl.export_all(out, dt=1e-3, nb_steps=200)
    assert paths["pre"].is_file()
    assert paths["command"].is_file()
    text = paths["pre"].read_text(encoding="utf-8")
    assert "st_sd" in text
    assert "writeDatbox" in text

    # save / reload (loop expansion policy may differ on reload)
    proj = tmp_path / "wave1.lmgc90"
    ctrl.save_project(proj)
    ctrl2 = ProjectController()
    ctrl2.load_project(proj)
    assert ctrl2.project.name == "wave1"
    assert len(ctrl2.project.materials) == 2
    assert len(ctrl2.project.laws) == 1
    assert len(ctrl2.project.populations) == 1
    assert len(ctrl2.project.populations[0]) == 30
    assert ctrl2.project.n_bodies >= 30


def test_remove_law_visibility_dof():
    ctrl = ProjectController()
    _base(ctrl)
    ctrl.add_law(pre.tact_behav(name="law1", law="IQS_CLB", fric=0.2))
    ctrl.add_visibility(pre.see_table(
        CorpsCandidat="RBDY2", candidat="DISKx", colorCandidat="BLUEx",
        CorpsAntagoniste="RBDY2", antagoniste="DISKx", colorAntagoniste="REEDx",
        behav="law1", alert=0.1,
    ))
    a = pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL")
    ctrl.add(a)
    ctrl.add_dof(DOFOperation("imposeDrivenDof", "avatar", a.avatar_id, {"component": 1, "dofty": "vlocy", "ct": 0}))
    ctrl.add_postpro(PostProCommand("KINETIC ENERGY", step=5))

    ctrl.remove_postpro(0)
    ctrl.remove_dof(0)
    ctrl.remove_visibility(0)
    ctrl.remove_law("law1")
    assert ctrl.project.laws == []
    assert ctrl.project.visibility == []
    assert ctrl.project.operations == []
    assert ctrl.project.postpro == []
