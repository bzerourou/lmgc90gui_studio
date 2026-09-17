from pathlib import Path

from lmgc90_core import DOFOperation, GranuloConfig, PostProCommand, Project, pre


def _compression(tmp: Path) -> Project:
    p = Project(name="beton", dimension=2)
    p.add(pre.material(name="BETON", materialType="ELAS", density=2400.0, young=30e9, nu=0.2))
    p.add(pre.material(name="ACIER", materialType="RIGID", density=7800.0))
    p.add(pre.model(name="femxx", physics="MECAx", element="T3xxx", dimension=2,
                    anisotropy="iso__", kinematic="small"))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    spec = pre.meshed_rectangle(
        lx=0.15, ly=0.30, nx=6, ny=12, center=[0.0, 0.17],
        model="femxx", material="BETON",
        contactors=[{"shape": "CLxxx", "color": "CYANx", "group": "down"}],
    )
    p.add(spec)
    wall = pre.smoothWall(l=0.23, h=0.025, center=[0.0, -0.0125],
                          model="rigid", material="ACIER", color="GRAYx")
    p.add(wall)
    p.add(DOFOperation("imposeDrivenDof", "avatar", wall.avatar_id,
                       {"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0}))
    p.add(pre.tact_behav(name="bt_ac", law="GAP_SGR_CLB", fric=0.25))
    p.add(pre.see_table(
        CorpsCandidat="MAILx", candidat="CLxxx", colorCandidat="CYANx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="GRAYx",
        behav="bt_ac", alert=0.02,
    ))
    p.add(PostProCommand("SOLVER INFORMATIONS", step=20))
    return p


def test_roundtrip(tmp_path: Path):
    p = _compression(tmp_path)
    path = tmp_path / "case.lmgc90"
    p.save(path)
    q = Project.load(path)
    assert q.name == "beton"
    assert [m.name for m in q.materials] == ["BETON", "ACIER"]
    assert q.avatars[0].avatar_id == p.avatars[0].avatar_id
    assert q.avatars[1].avatar_type.value == "smoothWall"
    assert q.laws[0].law_type.value == "GAP_SGR_CLB"


def test_population_sidecar(tmp_path: Path):
    p = Project(name="g", dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    p.deposit(GranuloConfig(
        nb_particles=30, radius_min=0.02, radius_max=0.03,
        container_type="Box2D", container_params={"lx": 0.8, "ly": 0.8},
        material_name="STEEL", model_name="rigid", seed=1,
    ))
    path = tmp_path / "g.lmgc90"
    p.save(path)
    sidecar = tmp_path / "g.populations.npz"
    assert sidecar.exists()
    q = Project.load(path)
    assert len(q.populations) == 1
    assert len(q.populations[0]) == len(p.populations[0])
    assert (q.populations[0].centers == p.populations[0].centers).all()


def test_pre_script_contains_pylmgc90_calls(tmp_path: Path):
    p = _compression(tmp_path)
    src = p.to_pre_script()
    assert "from pylmgc90 import pre" in src
    assert "pre.material(name='BETON'" in src
    assert "pre.buildMesh2D" in src
    assert "pre.smoothWall" in src
    assert "pre.tact_behav(name='bt_ac', law='GAP_SGR_CLB'" in src
    assert "pre.see_table(" in src
    assert "imposeDrivenDof" in src
    assert "pre.writeDatbox(" in src


def test_equivalent_matches_factory():
    p = Project(dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    av = p.add(pre.rigidDisk(r=0.1, center=[0.2, 0.3], model="rigid", material="STEEL"))
    eq = p.equivalent(av)
    assert "pre.rigidDisk(r=0.1, center=[0.2, 0.3]" in eq


def test_chipy_and_sbatch():
    p = Project(name="job", dimension=2)
    chipy = p.to_chipy_script(dt=1e-4, nb_steps=10)
    assert "chipy.SetDimension(2)" in chipy
    assert "chipy.RBDY2_LoadTactors()" in chipy
    bat = p.sbatch(partition="cpu", time="01:00:00")
    assert bat.startswith("#!/bin/bash")
    assert "#SBATCH --partition=cpu" in bat
    assert "python pre.py" in bat
    assert "python command.py" in bat
