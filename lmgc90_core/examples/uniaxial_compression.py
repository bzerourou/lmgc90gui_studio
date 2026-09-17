"""Uniaxial compression of a concrete specimen — lab-style 2D test.

Same physics as the GUI example `ex_concrete_compression.py`, but this
file never touches a controller, Qt, or a live pylmgc90 object.

Run:
    PYTHONPATH=src python examples/uniaxial_compression.py
"""
from __future__ import annotations

from pathlib import Path

from lmgc90_core import DOFOperation, GranuloConfig, PostProCommand, Project, pre

OUT = Path(__file__).resolve().parent / "_out_compression"


def build() -> Project:
    p = Project(name="beton_C30_compression", dimension=2)

    p.add(pre.material(
        name="BETON", materialType="ELAS", density=2400.0,
        elas="standard", anisotropy="isotropic", young=30e9, nu=0.20,
    ))
    p.add(pre.material(name="ACIER", materialType="RIGID", density=7800.0))
    p.add(pre.model(
        name="femxx", physics="MECAx", element="T3xxx", dimension=2,
        anisotropy="iso__", kinematic="small", formulation="UpdtL",
        mass_storage="lump_", material="elas_", external_model="no___",
    ))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))

    lx, ly = 0.15, 0.30
    nx, ny = 6, 12
    y0 = 0.02
    specimen = pre.meshed_rectangle(
        lx=lx, ly=ly, nx=nx, ny=ny,
        center=[0.0, y0 + ly / 2.0],
        model="femxx", material="BETON", color="CYANx",
        mesh_type="2T3",
        contactors=[
            {"shape": "CLxxx", "color": "CYANx", "group": "down"},
            {"shape": "CLxxx", "color": "CYANx", "group": "up"},
        ],
    )
    p.add(specimen)
    p.group("eprouvette", [specimen.avatar_id])

    platen_w, platen_h = lx + 0.08, 0.025
    bottom = pre.smoothWall(
        l=platen_w, h=platen_h, center=[0.0, -platen_h / 2.0],
        model="rigid", material="ACIER", color="GRAYx", nb_polyg=24,
    )
    p.add(bottom)
    p.add(DOFOperation(
        "imposeDrivenDof", "avatar", bottom.avatar_id,
        {"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))

    top_y = y0 + ly + platen_h / 2.0 + 0.005
    top = pre.smoothWall(
        l=platen_w, h=platen_h, center=[0.0, top_y],
        model="rigid", material="ACIER", color="REEDx", nb_polyg=24,
    )
    p.add(top)
    p.add(DOFOperation(
        "imposeDrivenDof", "avatar", top.avatar_id,
        {"component": [1, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    p.add(DOFOperation(
        "imposeDrivenDof", "avatar", top.avatar_id,
        {"component": 2, "dofty": "vlocy", "ct": -0.002},
    ))
    p.group("plateaux", [bottom.avatar_id, top.avatar_id])

    p.add(pre.tact_behav(name="bt_ac", law="GAP_SGR_CLB", fric=0.25))
    p.add(pre.see_table(
        CorpsCandidat="MAILx", candidat="CLxxx", colorCandidat="CYANx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="GRAYx",
        behav="bt_ac", alert=0.02,
    ))
    p.add(pre.see_table(
        CorpsCandidat="MAILx", candidat="CLxxx", colorCandidat="CYANx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="REEDx",
        behav="bt_ac", alert=0.02,
    ))

    p.add(PostProCommand("Fint EVOLUTION", step=5))
    p.add(PostProCommand("KINETIC ENERGY", step=10))
    p.add(PostProCommand("SOLVER INFORMATIONS", step=20))
    return p


def main() -> None:
    p = build()
    OUT.mkdir(exist_ok=True)
    (OUT / "pre.py").write_text(p.to_pre_script(), encoding="utf-8")
    (OUT / "command.py").write_text(p.to_chipy_script(dt=1e-4, nb_steps=8000), encoding="utf-8")
    (OUT / "run.sbatch").write_text(p.sbatch(time="02:00:00", mem="4G"), encoding="utf-8")
    p.save(OUT / "beton_C30_compression.lmgc90")
    print(p.summary())
    print()
    print("--- equivalent pre.* for the specimen ---")
    print(p.equivalent(p.avatars[0]))
    print()
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
