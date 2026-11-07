import ast

import pytest

from lmgc90_core import Avatar, AvatarType, ParticlePopulation, Project, pre
from lmgc90_core.compute_script import ComputeScriptGenerator


def _generate(set_entries):
    project = Project(name="set_actions", dimension=2)
    return ComputeScriptGenerator(project).generate_string({
        "use_mecaMAILx": False,
        "use_therMAILx": False,
        "use_poroMAILx": False,
        "set_entries": set_entries,
    })


def test_set_actions_are_generated_at_the_selected_times():
    script = _generate([
        {
            "func": "RBDY2_SetVisible",
            "args": "1",
            "step_mode": "before",
        },
        {
            "func": "SetThetaIntegrator",
            "args": "theta",
            "step_mode": "all",
        },
        {
            "func": "RBDY2_SetInvisible",
            "args": "2",
            "step_mode": "every_n",
            "step_val": 3,
        },
        {
            "func": "SetTimeStep",
            "args": "dt * 0.5",
            "step_mode": "at_k",
            "step_val": 0,
        },
        {
            "func": "RBDY2_SetInvisible",
            "args": "3",
            "step_mode": "after",
        },
    ])

    loop_start = script.index("for k in range(nb_steps):")
    assert script.index("chipy.RBDY2_SetVisible(1)") < loop_start
    assert "    chipy.SetThetaIntegrator(theta)\n" in script
    assert "if k % 3 == 0:\n        chipy.RBDY2_SetInvisible(2)" in script
    assert "if k == 0:\n        chipy.SetTimeStep(dt * 0.5)" in script
    assert "\nchipy.RBDY2_SetInvisible(3)\n" in script
    assert script.index("\nchipy.RBDY2_SetInvisible(3)\n") > loop_start
    ast.parse(script)


@pytest.mark.parametrize(
    "entry, message",
    [
        (
            {"func": "SetTimeStep", "args": "dt; chipy.SetTimeStep(0)"},
            "invalid Python arguments",
        ),
        (
            {"func": "SetTimeStep; chipy.SetTimeStep", "args": "dt"},
            "valid chipy function name",
        ),
        (
            {"func": "SetTimeStep", "args": "dt", "step_mode": "unknown"},
            "invalid step mode",
        ),
    ],
)
def test_invalid_set_actions_fail_with_a_clear_error(entry, message):
    with pytest.raises(ValueError, match=message):
        _generate([entry])


def _group_visibility_script(project, dimension=2):
    return ComputeScriptGenerator(project).generate_string({
        "use_RBDY2": dimension == 2,
        "use_RBDY3": dimension == 3,
        "use_mecaMAILx": True,
        "vis_entries": [{
            "action": "visible",
            "dim": f"{dimension}D",
            "group": "selected",
            "ids": "",
        }],
    })


def test_group_indices_follow_rigid_body_order_and_mesh_expansion():
    project = Project(name="group_indices", dimension=2)
    rigid_before = pre.rigidDisk(
        r=0.1, center=[0, 0], model="rigid", material="STEEL",
    )
    deformable = Avatar(
        avatar_type=AvatarType.MESH_DEFORMABLE,
        center=[0, 0],
        material_name="STEEL",
        model_name="mesh",
    )
    from_mesh = Avatar(
        avatar_type=AvatarType.EMPTY_AVATAR,
        center=[0, 0],
        material_name="STEEL",
        model_name="rigid",
        mesh_params={
            "source": "rigidsFromMesh2D",
            "filepath": "pkg://lmgc90_core/data/meshes/Carre.msh",
            "dim": 2,
        },
    )
    rigid_after = pre.rigidDisk(
        r=0.1, center=[1, 0], model="rigid", material="STEEL",
    )
    project.avatars.extend([rigid_before, deformable, from_mesh, rigid_after])
    project.group("selected", [deformable.avatar_id, from_mesh.avatar_id, rigid_after.avatar_id])

    script = _group_visibility_script(project)

    assert "\nchipy.RBDY2_SetVisible(1)\n" not in script
    for body_index in range(2, 7):
        assert f"chipy.RBDY2_SetVisible({body_index})" in script


def test_group_indices_recompute_after_remove_and_undo():
    project = Project(name="group_undo", dimension=2)
    avatars = [
        pre.rigidDisk(r=0.1, center=[index, 0], model="rigid", material="STEEL")
        for index in range(3)
    ]
    project.avatars.extend(avatars)
    project.group("selected", [avatars[2].avatar_id])

    assert "chipy.RBDY2_SetVisible(3)" in _group_visibility_script(project)
    project.remove_avatar(avatars[1].avatar_id)
    assert "chipy.RBDY2_SetVisible(2)" in _group_visibility_script(project)
    project.history.undo(project)
    assert "chipy.RBDY2_SetVisible(3)" in _group_visibility_script(project)


def test_group_indices_include_soa_after_aos_bodies():
    project = Project(name="group_soa_indices", dimension=2)
    rigid = pre.rigidDisk(
        r=0.1, center=[0, 0], model="rigid", material="STEEL",
    )
    project.avatars.append(rigid)
    population = ParticlePopulation.create(
        avatar_type=AvatarType.RIGID_DISK,
        material_name="STEEL",
        model_name="rigid",
        centers=[[0.0, 0.0], [1.0, 0.0]],
        radii=[0.1, 0.1],
    )
    project.populations.append(population)
    project.group("selected", [population.population_id])

    script = _group_visibility_script(project)

    assert "chipy.RBDY2_SetVisible(2)" in script
    assert "chipy.RBDY2_SetVisible(3)" in script


@pytest.mark.parametrize(
    ("dimension", "element", "visibility_function"),
    [
        (2, "Rxx2D", "RBDY2_SetVisible"),
        (3, "Rxx3D", "RBDY3_SetVisible"),
    ],
)
def test_group_indices_count_empty_rigid_avatars(
    dimension, element, visibility_function,
):
    project = Project(name="empty_avatar_indices", dimension=dimension)
    empty_avatars = [
        pre.emptyAvatar(
            center=[float(index)] * dimension,
            model="rigid",
            material="STEEL",
        )
        for index in range(2)
    ]
    if dimension == 2:
        empty_avatars[0].wall_params = {
            "brick_name": "rigid-brick", "l": 1.0, "h": 0.5,
        }
    rigid_after = (
        pre.rigidDisk(r=0.1, center=[2.0, 0.0], model="rigid", material="STEEL")
        if dimension == 2
        else pre.rigidSphere(
            r=0.1, center=[2.0, 0.0, 0.0], model="rigid", material="STEEL",
        )
    )
    project.avatars.extend([*empty_avatars, rigid_after])
    project.group("selected", [rigid_after.avatar_id])

    script = _group_visibility_script(project, dimension)

    assert f"chipy.{visibility_function}(3)" in script
