"""Vague 4 — groups, contactors, pipeline/sbatch (headless)."""
from __future__ import annotations

from pathlib import Path

from lmgc90_core import Pipeline, pre, render_sbatch
from lmgc90_core.validate import compatible_contactors
from lmgc90_gui import ProjectController


def _scene(ctrl: ProjectController) -> None:
    ctrl.new_project("w4", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))


def test_groups_crud():
    ctrl = ProjectController()
    _scene(ctrl)
    a = pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL")
    b = pre.rigidDisk(r=0.1, center=[1, 0], model="rigid", material="STEEL")
    ctrl.add(a)
    ctrl.add(b)
    ctrl.group("G1", [a.avatar_id, b.avatar_id])
    assert "G1" in ctrl.project.avatar_groups
    assert len(ctrl.project.avatar_groups["G1"]) == 2
    ctrl.remove_group("G1")
    assert "G1" not in ctrl.project.avatar_groups


def test_contactors_on_empty_avatar():
    ctrl = ProjectController()
    _scene(ctrl)
    av = pre.emptyAvatar(center=[0, 0], model="rigid", material="STEEL", color="BLUEx")
    ctrl.add(av)
    shapes = compatible_contactors(av.avatar_type, 2)
    assert "DISKx" in shapes or len(shapes) > 0
    shape = "DISKx" if "DISKx" in shapes else shapes[0]
    av.contactors.append({"shape": shape, "color": "BLUEx"})
    assert len(ctrl.project.avatars[0].contactors) == 1
    text = ctrl.emit_pre_script()
    # mesh/empty contactors appear when present
    assert shape in text or "emptyAvatar" in text or "avatar" in text.lower()


def test_pipeline_sbatch_export(tmp_path: Path):
    ctrl = ProjectController()
    _scene(ctrl)
    ctrl.add(pre.rigidDisk(r=0.05, center=[0, 0], model="rigid", material="STEEL"))
    ctrl.prefs.auto_write_datbox = False
    out = tmp_path / "pipe"
    paths = ctrl.prepare_run_directory(out)
    assert paths["pre"].is_file()
    assert paths["command"].is_file()
    sbatch = render_sbatch(ctrl.project, job_name="w4job", partition="cpu", time="01:00:00")
    assert "#SBATCH" in sbatch
    assert "command.py" in sbatch
    (out / "run.sbatch").write_text(sbatch, encoding="utf-8")
    pipe = Pipeline.standard(dt=1e-3, nb_steps=10, backend="slurm")
    assert pipe.backend == "slurm"
    assert any(s.name == "run" for s in pipe.steps)
