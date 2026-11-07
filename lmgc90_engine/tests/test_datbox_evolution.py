from __future__ import annotations

from lmgc90_core import DOFOperation, Project
from lmgc90_engine.datbox import _maybe_write_evolution_files


def test_evolution_file_is_not_overwritten(tmp_path):
    project = Project(name="evolution", dimension=2)
    project.dynamic_vars["vx_evolution"] = {
        "file": "vx.dat",
        "v_max": 0.02,
        "t_rest": 0.005,
        "t_ramp": 0.01,
    }
    evolution_file = tmp_path / "vx.dat"
    original = "0.0 0.0\n0.5 0.7\n"
    evolution_file.write_text(original, encoding="utf-8")

    _maybe_write_evolution_files(project, tmp_path)

    assert evolution_file.read_text(encoding="utf-8") == original


def test_evolution_file_is_not_invented_from_dof_filename_alone(tmp_path):
    project = Project(name="evolution", dimension=2)
    project.operations.append(DOFOperation(
        "imposeDrivenDof",
        "avatar",
        "avatar-id",
        {
            "description": "evolution",
            "evolutionFile": "user_velocity.dat",
        },
    ))

    _maybe_write_evolution_files(project, tmp_path)

    assert not (tmp_path / "user_velocity.dat").exists()


def test_configured_evolution_is_created_when_missing(tmp_path):
    project = Project(name="evolution", dimension=2)
    project.dynamic_vars["vx_evolution"] = (
        "{'file':'vx.dat','v_max':0.02,'t_rest':0.005,'t_ramp':0.01}"
    )

    _maybe_write_evolution_files(project, tmp_path)

    assert (tmp_path / "vx.dat").read_text(encoding="utf-8") == (
        "0  0\n0.005  0\n0.01  0.02\n10  0.02\n"
    )
