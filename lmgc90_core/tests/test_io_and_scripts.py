from pathlib import Path
import ast

import pytest

from lmgc90_core import (
    DOFOperation, GranuloConfig, ParticlePopulation, PostProCommand, Project, pre,
    render_sbatch,
)
from lmgc90_core.scenes.demos import falling_disks, sphere_stack


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


def test_removed_population_history_roundtrip_keeps_arrays(tmp_path: Path):
    p = Project(name="g", dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    population = p.deposit(GranuloConfig(
        nb_particles=4, radius_min=0.02, radius_max=0.03,
        container_type="Box2D", container_params={"lx": 0.4, "ly": 0.4},
        material_name="STEEL", model_name="rigid", seed=1,
    ))
    population_id = population.population_id

    p.remove_population(population_id)
    path = tmp_path / "removed.lmgc90"
    p.save(path)
    loaded = Project.load(path)
    assert loaded.populations == []

    loaded.undo()
    restored = loaded.population(population_id)
    assert len(restored) == len(population)
    assert (restored.centers == population.centers).all()


def test_v1_migration_restores_loop_avatars_and_resolves_dof_indices(tmp_path: Path):
    import json

    template = pre.rigidDisk(
        r=0.1, center=[0, 0], model="rigid", material="STEEL",
    )
    data = {
        "schema_version": 1,
        "project_name": "legacy-loop",
        "dimension": 2,
        "materials": [
            pre.material(name="STEEL", materialType="RIGID", density=7800).to_dict()
        ],
        "models": [
            pre.model(
                name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
            ).to_dict()
        ],
        "avatars": [template.to_dict()],
        "loops": [{
            "type": "line",
            "model_avatar_index": 0,
            "count": 2,
            "step": 0.2,
            "generated_indices": [1, 2],
        }],
        "operations": [{
            "type": "imposeDrivenDof",
            "body_index": 2,
            "params": {"ct": 0.0},
        }],
        "avatar_groups": {"legacy": [1, 2]},
    }
    path = tmp_path / "legacy-loop.lmgc90"
    path.write_text(json.dumps(data), encoding="utf-8")

    project = Project.load(path)

    assert len(project.avatars) == 3
    loop = project.loops[0]
    assert loop.model_avatar_id == project.avatars[0].avatar_id
    assert loop.generated_ids == [
        project.avatars[1].avatar_id, project.avatars[2].avatar_id,
    ]
    assert project.operations[0].target_value == project.avatars[2].avatar_id
    assert project.avatar_groups["legacy"] == loop.generated_ids
    assert not project.load_warnings


def test_v1_migration_regenerates_missing_population_from_granulo_config(tmp_path: Path):
    import json

    config = GranuloConfig(
        nb_particles=3,
        radius_min=0.02,
        radius_max=0.03,
        container_type="Box2D",
        container_params={"lx": 1.0, "ly": 1.0},
        material_name="STEEL",
        model_name="rigid",
        seed=7,
        population_id="pop_legacy",
    ).to_dict()
    config["generated_indices"] = [1, 2, 3]
    data = {
        "schema_version": 1,
        "project_name": "legacy-granulo",
        "dimension": 2,
        "materials": [
            pre.material(name="STEEL", materialType="RIGID", density=7800).to_dict()
        ],
        "models": [
            pre.model(
                name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
            ).to_dict()
        ],
        "avatars": [],
        "granulo_generations": [config],
        "operations": [{
            "type": "imposeDrivenDof",
            "body_index": 2,
            "params": {"ct": 0.0},
        }],
        "avatar_groups": {"legacy": [1, 2, 3]},
    }
    path = tmp_path / "legacy-granulo.lmgc90"
    path.write_text(json.dumps(data), encoding="utf-8")

    project = Project.load(path)

    assert len(project.populations) == 1
    population = project.populations[0]
    assert population.population_id == "pop_legacy"
    assert len(population) == 3
    assert project.granulo[0].population_id == population.population_id
    assert project.operations[0].target_value == f"{population.population_id}:1"
    assert project.avatar_groups["legacy"] == [
        f"{population.population_id}:{index}" for index in range(3)
    ]
    from lmgc90_core.pre_script import emit_pre
    script = emit_pre(project)
    assert f"_population_bodies_pop_legacy[1].imposeDrivenDof" in script
    assert len(project.load_warnings) == 1
    assert any("regenerated from stored granulo configuration" in warning
               for warning in project.load_warnings)


def test_pre_script_contains_pylmgc90_calls(tmp_path: Path):
    p = _compression(tmp_path)
    src = p.to_pre_script()
    assert "from pylmgc90 import pre" in src
    assert "pre.material(name='BETON'" in src
    assert "pre.buildMesh2D" in src
    assert "pre.smoothWall" in src
    assert "pre.tact_behav(name='bt_ac', law='GAP_SGR_CLB'" in src
    assert "pre.see_table(" in src
    assert "behav=law_bt_ac" in src
    assert "behav='bt_ac'" not in src
    assert "imposeDrivenDof" in src
    assert "pre.writeDatbox(" in src
    assert ".addContactors(shape='CLxxx', color='CYANx', group='down')" in src


def test_pre_script_emits_custom_polygon_vertices_in_local_frame():
    p = Project(name="polygon", dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    p.add(pre.rigidPolygon(
        center=[0.5, 0.25], model="rigid", material="STEEL",
        generation_type="full",
        vertices=[[0.0, 0.0], [1.0, 0.0], [1.0, 0.5], [0.0, 0.5]],
    ))

    src = p.to_pre_script()

    assert "generation_type='full'" in src
    assert "vertices=np.array([[-0.5, -0.25], [0.5, -0.25], [0.5, 0.25], [-0.5, 0.25]])" in src
    ast.parse(src)


def test_empty_avatar_contactors_are_emitted_before_rigid_properties():
    p = Project(name="empty_contactors", dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    avatar = p.add(pre.emptyAvatar(
        center=[0.0, 0.0], model="rigid", material="STEEL",
    ))
    avatar.contactors.append({
        "shape": "DISKx",
        "color": "BLUEx",
        "params": {"byrd": 0.15},
    })

    script = p.to_pre_script()
    call = (
        f"av_{avatar.avatar_id}.addContactors("
        "shape='DISKx', color='BLUEx', byrd=0.15)"
    )
    properties = f"av_{avatar.avatar_id}.computeRigidProperties()"
    add_avatar = f"bodies.addAvatar(av_{avatar.avatar_id})"

    assert "pre.avatar(2)" in script
    assert call in script
    assert properties in script
    assert script.index(call) < script.index(properties) < script.index(add_avatar)
    ast.parse(script)


def test_pre_script_emits_rigid_brick_geometry_for_empty_avatar():
    project = Project(name="rigid_brick", dimension=2)
    project.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    project.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    avatar = project.add(pre.emptyAvatar(
        center=[0.5, 0.25], model="rigid", material="STEEL",
    ))
    avatar.wall_params = {"brick_name": "std", "l": 0.2, "h": 0.1}

    script = project.to_pre_script()

    assert "pre.brick2D('std', 0.2, 0.1)" in script
    assert ".rigidBrick(center=[0.5, 0.25]" in script
    assert "pre.avatar(2)" not in script
    ast.parse(script)


def test_pre_script_expands_rigids_from_mesh2d_to_bodies():
    project = Project(name="mesh_rigids", dimension=2)
    project.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    project.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    avatar = project.add(pre.emptyAvatar(
        center=[0.05, 0.05], model="rigid", material="STEEL", color="BLEUx",
    ))
    avatar.mesh_params = {
        "geom": "rigidsFromMesh2D",
        "source": "rigidsFromMesh2D",
        "filepath": "pkg://lmgc90_core/data/meshes/Carre.msh",
        "dim": 2,
    }

    script = project.to_pre_script()
    bodies_ref = f"_mesh_rigids_{avatar.avatar_id}"

    assert "pre.readMesh(str(_mesh_file_" in script
    assert "pre.rigidsFromMesh2D(" in script
    assert f"for _body in {bodies_ref}:" in script
    assert "bodies.addAvatar(_body)" in script
    assert "pre.avatar(2)" not in script
    ast.parse(script)


def test_pre_script_compacts_repeated_avatars_when_requested():
    p = Project(name="compact", dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    p.add(pre.rigidDisk(
        r=0.2, center=[-1.0, 0.0], model="rigid", material="STEEL", color="REDxx"
    ))
    first = p.add(pre.rigidDisk(r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL"))
    second = p.add(pre.rigidDisk(r=0.15, center=[1.0, 0.0], model="rigid", material="STEEL"))
    third = p.add(pre.rigidDisk(r=0.12, center=[2.0, 0.0], model="rigid", material="STEEL"))
    p.avatar_groups["pair"] = [first.avatar_id, second.avatar_id, third.avatar_id]
    p.add(DOFOperation("translate", "group", "pair", {"dx": 0.25}))

    expanded = p.to_pre_script()
    compact = p.to_pre_script(use_loop=True)

    assert expanded.count("pre.rigidDisk(") == 4
    assert compact.count("pre.rigidDisk(") == 2
    assert "for _center, _radius in (" in compact
    assert "([1.0, 0.0], 0.15)" in compact
    assert "_avatar_batch_0.append(_body)" in compact
    assert "_avatar_batch_0[0].translate(dx=0.25)" in compact
    assert "_avatar_batch_0[1].translate(dx=0.25)" in compact
    assert "_avatar_batch_0[2].translate(dx=0.25)" in compact
    assert len(compact) < len(expanded)
    ast.parse(compact)


def test_pre_script_dof_fields_and_color_target():
    p = Project(name="dof_options", dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    red = p.add(pre.rigidDisk(
        r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL", color="REDxx"
    ))
    blue = p.add(pre.rigidDisk(
        r=0.1, center=[1.0, 0.0], model="rigid", material="STEEL", color="BLUEx"
    ))
    p.add(DOFOperation(
        "imposeInitValue", "color", "REDxx",
        {"group": "all", "component": 1, "value": 0.25},
    ))
    p.add(DOFOperation(
        "rotate", "avatar", blue.avatar_id,
        {"description": "Euler", "phi": 0.1, "theta": 0.2, "psi": 0.3},
    ))

    script = p.to_pre_script()
    red_target = f"av_{red.avatar_id}"
    blue_target = f"av_{blue.avatar_id}"
    assert f"{red_target}.imposeInitValue(group='all', component=1, value=0.25)" in script
    assert f"{blue_target}.imposeInitValue(" not in script
    assert (
        f"{blue_target}.rotate(description='Euler', phi=0.1, theta=0.2, psi=0.3)"
        in script
    )
    ast.parse(script)


def test_pre_script_applies_group_dof_to_population_particles():
    project = Project(name="population_dof", dimension=2)
    project.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    project.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    population = project.add(ParticlePopulation.create(
        avatar_type="rigidDisk",
        material_name="STEEL",
        model_name="rigid",
        centers=[[0.0, 0.0], [1.0, 0.0]],
        radii=[0.1, 0.2],
        group_name="particles",
    ))
    project.add(DOFOperation(
        "imposeDrivenDof", "group", "particles",
        {"component": 1, "dofty": "vlocy", "ct": 0.0},
    ))

    script = project.to_pre_script()
    bodies_ref = f"_population_bodies_{population.population_id[:12]}"

    assert f"{bodies_ref} = []" in script
    assert f"{bodies_ref}.append(_body)" in script
    assert f"{bodies_ref}[0].imposeDrivenDof(" in script
    assert f"{bodies_ref}[1].imposeDrivenDof(" in script
    assert "av_pop_" not in script
    ast.parse(script)


def test_pre_script_resolves_postpro_avatar_and_group_targets():
    project = Project(name="postpro_targets", dimension=2)
    project.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    project.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    avatar = project.add(pre.rigidDisk(
        r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL",
    ))
    population = project.add(ParticlePopulation.create(
        avatar_type="rigidDisk",
        material_name="STEEL",
        model_name="rigid",
        centers=[[1.0, 0.0], [2.0, 0.0]],
        radii=[0.1, 0.2],
        group_name="particles",
    ))
    project.add(PostProCommand(
        name="BODY TRACKING", target_type="avatar", target_value=avatar.avatar_id,
    ))
    project.add(PostProCommand(
        name="TORQUE EVOLUTION", target_type="group", target_value="particles",
    ))
    project.add(PostProCommand(
        name="NEW RIGID SETS", target_type="groups",
        target_value=["particles"],
    ))

    script = project.to_pre_script()
    avatar_ref = f"av_{avatar.avatar_id}"
    population_ref = f"_population_bodies_{population.population_id[:12]}"

    assert f"rigid_set=[{avatar_ref}]" in script
    assert f"rigid_set=[{population_ref}[0], {population_ref}[1]]" in script
    assert f"rigid_sets=[[{population_ref}[0], {population_ref}[1]]]" in script
    assert "avatar=" not in script
    assert "group=" not in script
    ast.parse(script)


def test_pre_script_avatar_variable_names_use_full_ids():
    project = Project(name="full_avatar_ids", dimension=2)
    project.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    project.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    first = pre.rigidDisk(
        r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL",
    )
    second = pre.rigidDisk(
        r=0.1, center=[1.0, 0.0], model="rigid", material="STEEL",
    )
    first.avatar_id = "deadbeef" + "1" * 24
    second.avatar_id = "deadbeef" + "2" * 24
    project.add(first)
    project.add(second)
    project.add(DOFOperation(
        "imposeDrivenDof", "avatar", second.avatar_id,
        {"component": 1, "dofty": "vlocy", "ct": 0.0},
    ))

    script = project.to_pre_script()

    first_ref = f"av_{first.avatar_id}"
    second_ref = f"av_{second.avatar_id}"
    assert f"{first_ref} = pre.rigidDisk(" in script
    assert f"{second_ref} = pre.rigidDisk(" in script
    assert f"{second_ref}.imposeDrivenDof(" in script
    assert f"{first_ref}.imposeDrivenDof(" not in script
    ast.parse(script)


def test_chipy_script_enables_detectors_required_by_demo_visibility():
    project_2d = Project(name="falling_disks", dimension=2)
    falling_disks(project_2d)
    script_2d = project_2d.to_chipy_script()
    assert "chipy.ComputeFreeVelocity()" in script_2d
    assert "chipy.DKDKx_SelectProxTactors()" in script_2d
    assert "chipy.DKJCx_SelectProxTactors()" in script_2d
    assert len({tuple(a.center) for a in project_2d.avatars if a.avatar_type.value == "rigidDisk"}) == 10

    project_3d = Project(name="sphere_stack", dimension=3)
    sphere_stack(project_3d)
    script_3d = project_3d.to_chipy_script()
    assert "mhyp   = 3" in script_3d
    assert "chipy.RBDY3_NewStep()" in script_3d
    assert "chipy.SPSPx_SelectProxTactors()" in script_3d
    assert "chipy.SPPLx_SelectProxTactors()" in script_3d
    assert "chipy.DKDKx_SelectProxTactors()" not in script_3d

    overridden = project_3d.to_chipy_script(use_SPPLx=False)
    assert "chipy.SPPLx_SelectProxTactors()" not in overridden


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


def test_render_sbatch_quotes_shell_values_and_exports_openmp_threads():
    project = Project(name="safe job", dimension=2)
    script = render_sbatch(
        project,
        job_name="safe-job",
        partition="cpu",
        cpus_per_task=4,
        workdir="/scratch/my runs",
        module_load=("python/3.11; touch bad",),
        python="/opt/Python Env/python",
    )

    assert "export OMP_NUM_THREADS=4" in script
    assert "cd -- '/scratch/my runs'" in script
    assert "module load 'python/3.11; touch bad'" in script
    assert "'/opt/Python Env/python' pre.py" in script
    assert "'/opt/Python Env/python' command.py" in script


def test_render_sbatch_rejects_newlines_in_directives():
    with pytest.raises(ValueError, match="job_name"):
        render_sbatch(Project(), job_name="job\n#SBATCH --account=other")


def test_render_sbatch_preserves_submit_directory_expansion():
    script = render_sbatch(Project())

    assert 'cd -- "${SLURM_SUBMIT_DIR}"' in script


def test_render_sbatch_requires_positive_integer_cpu_counts():
    with pytest.raises(ValueError, match="positive integers"):
        render_sbatch(Project(), cpus_per_task=0)
