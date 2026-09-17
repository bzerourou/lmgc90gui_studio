"""Vague 1 scene — materials, loop, granulo SoA, contact, DOF, export.

  PYTHONPATH=lmgc90_core/src:lmgc90_engine/src:lmgc90_gui/src \\
    python lmgc90_gui/examples/wave1_scene.py
"""
from __future__ import annotations

from pathlib import Path

from lmgc90_core import DOFOperation, GranuloConfig, Loop, PostProCommand, pre
from lmgc90_gui import ProjectController

OUT = Path(__file__).resolve().parent / "_out_wave1"


def main() -> None:
    ctrl = ProjectController()
    ctrl.new_project("wave1_box", dimension=2)

    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.material(name="SAND", materialType="RIGID", density=2500))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))

    floor = pre.smoothWall(
        l=2.0, h=0.08, center=[0.0, -0.04],
        model="rigid", material="STEEL", color="GRAYx", nb_polyg=16,
    )
    ctrl.add(floor)
    ctrl.add_dof(DOFOperation(
        "imposeDrivenDof", "avatar", floor.avatar_id,
        {"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))

    seed = pre.rigidDisk(
        r=0.06, center=[0.0, 0.3], model="rigid", material="SAND", color="BLUEx",
    )
    ctrl.add(seed)
    ctrl.apply_loop(Loop(
        loop_type="grid", model_avatar_id=seed.avatar_id,
        count=9, step=0.15, offset_x=-0.15, offset_y=0.3, group_name="grid",
    ))

    ctrl.deposit(GranuloConfig(
        nb_particles=40, radius_min=0.015, radius_max=0.025,
        container_type="Box2D", container_params={"lx": 1.0, "ly": 0.6},
        material_name="SAND", model_name="rigid", avatar_type="rigidDisk",
        color="CYANx", group_name="depot", seed=1, dimension=2,
    ))

    ctrl.add_law(pre.tact_behav(name="st_sd", law="IQS_CLB", fric=0.35))
    ctrl.add_visibility(pre.see_table(
        CorpsCandidat="RBDY2", candidat="DISKx", colorCandidat="BLUEx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="GRAYx",
        behav="st_sd", alert=0.05,
    ))
    ctrl.add_visibility(pre.see_table(
        CorpsCandidat="RBDY2", candidat="DISKx", colorCandidat="CYANx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="GRAYx",
        behav="st_sd", alert=0.05,
    ))
    ctrl.add_postpro(PostProCommand("SOLVER INFORMATIONS", step=20))

    print(ctrl.summary())
    OUT.mkdir(parents=True, exist_ok=True)
    paths = ctrl.export_all(OUT, dt=1e-3, nb_steps=1000)
    for k, p in paths.items():
        print(f"  {k}: {p}")
    ctrl.save_project(OUT / "wave1_box.lmgc90")
    print(f"project: {OUT / 'wave1_box.lmgc90'}")


if __name__ == "__main__":
    main()
