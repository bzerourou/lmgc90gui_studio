"""50k-class granular deposit in a box — SoA by default, not a checkbox.

Run:
    PYTHONPATH=src python examples/granular_box.py
"""
from __future__ import annotations

from pathlib import Path

from lmgc90_core import DOFOperation, GranuloConfig, Loop, Project, pre

OUT = Path(__file__).resolve().parent / "_out_granular"


def build(n: int = 400, seed: int = 1) -> Project:
    p = Project(name="granular_box", dimension=2)
    p.add(pre.material(name="TDURx", materialType="RIGID", density=2500.0))
    p.add(pre.material(name="WALLx", materialType="RIGID", density=7800.0))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))

    floor = pre.smoothWall(
        l=1.0, h=0.04, center=[0.0, -0.02],
        model="rigid", material="WALLx", color="GRAYx",
    )
    p.add(floor)
    p.add(DOFOperation(
        "imposeDrivenDof", "avatar", floor.avatar_id,
        {"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))

    pop = p.deposit(GranuloConfig(
        nb_particles=n,
        radius_min=0.008,
        radius_max=0.016,
        container_type="Box2D",
        container_params={"lx": 0.90, "ly": 0.70},
        material_name="TDURx",
        model_name="rigid",
        avatar_type="rigidDisk",
        color="BLUEx",
        group_name="grains",
        seed=seed,
        dimension=2,
    ))

    p.add(pre.tact_behav(name="IQS01", law="IQS_CLB", fric=0.3))
    p.add(pre.see_table(
        CorpsCandidat="RBDY2", candidat="DISKx", colorCandidat="BLUEx",
        CorpsAntagoniste="RBDY2", antagoniste="DISKx", colorAntagoniste="BLUEx",
        behav="IQS01", alert=0.02,
    ))
    p.add(pre.see_table(
        CorpsCandidat="RBDY2", candidat="DISKx", colorCandidat="BLUEx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="GRAYx",
        behav="IQS01", alert=0.02,
    ))
    assert pop.group_name == "grains"
    return p


def demo_undo_and_loop() -> None:
    p = Project(name="loop_demo", dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    proto = p.add(pre.rigidDisk(r=0.05, center=[0, 0], model="rigid", material="STEEL"))
    p.apply_loop(Loop(loop_type="circle", model_avatar_id=proto.avatar_id,
                      count=8, radius=0.4, group_name="ring"))
    assert p.n_bodies == 9
    p.undo()
    assert p.n_bodies == 1
    p.redo()
    assert p.n_bodies == 9


def main() -> None:
    demo_undo_and_loop()
    p = build(n=400)
    OUT.mkdir(exist_ok=True)
    p.save(OUT / "granular_box.lmgc90")
    (OUT / "pre.py").write_text(p.to_pre_script(), encoding="utf-8")
    (OUT / "command.py").write_text(p.to_chipy_script(dt=5e-4, nb_steps=4000), encoding="utf-8")
    print(p.summary())
    print("radius stats:", p.populations[0].radius_stats())
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
