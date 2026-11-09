"""Controller tests — no PyQt6, no pylmgc90 required."""
from __future__ import annotations

from pathlib import Path

import pytest

from lmgc90_core import (
    ForLoop, GranuloConfig, Loop, MaterialType, ValidationError, pre,
)
from lmgc90_gui import ProjectController
from lmgc90_gui.controller.signals import _NoopSignal


def test_noop_controller_signals_are_isolated_per_instance():
    class HeadlessProjectController(ProjectController):
        state_changed = _NoopSignal()

    first = HeadlessProjectController()
    second = HeadlessProjectController()
    first_events = []
    second_events = []
    first.state_changed.connect(lambda: first_events.append("first"))
    second.state_changed.connect(lambda: second_events.append("second"))

    first.state_changed.emit()
    assert first_events == ["first"]
    assert second_events == []

    second.state_changed.emit()
    assert first_events == ["first"]
    assert second_events == ["second"]


def test_apply_scene_deposits_only_new_distribution_configs(monkeypatch):
    ctrl = ProjectController()
    ctrl.new_project("scene-granulo", dimension=2)

    def distribution_config(seed):
        return GranuloConfig(
            nb_particles=4,
            radius_min=0.01,
            radius_max=0.02,
            container_type="Box2D",
            container_params={"lx": 1.0, "ly": 1.0},
            material_name="STEEL",
            model_name="rigid",
            create_avatars=False,
            seed=seed,
        )

    existing = distribution_config(1)
    added_by_scene = distribution_config(2)
    ctrl.deposit(existing)

    deposit_calls = []
    deposit = ctrl.deposit

    def track_deposit(config):
        deposit_calls.append(config.generation_id)
        return deposit(config)

    monkeypatch.setattr(ctrl, "deposit", track_deposit)
    ctrl.apply_scene(
        lambda project: project.granulo.append(added_by_scene),
        on_conflict="merge",
    )

    assert deposit_calls == [added_by_scene.generation_id]
    assert [cfg.generation_id for cfg in ctrl.project.granulo] == [
        existing.generation_id,
        added_by_scene.generation_id,
    ]
    assert len(added_by_scene.radii) == added_by_scene.nb_particles

    ctrl.project.undo()
    assert [cfg.generation_id for cfg in ctrl.project.granulo] == [
        existing.generation_id,
    ]


def test_new_project_and_summary():
    ctrl = ProjectController()
    ctrl.new_project("box", dimension=2)
    assert ctrl.project.name == "box"
    assert ctrl.project.dimension == 2
    assert "box" in ctrl.summary()


def test_add_material_model_avatar_via_controller():
    ctrl = ProjectController()
    ctrl.new_project("t", dimension=2)
    events = []
    ctrl.state_changed.connect(lambda: events.append(1))

    ctrl.add_material(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add_model(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    av = pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL")
    ctrl.add_avatar(av)

    assert len(ctrl.project.materials) == 1
    assert len(ctrl.project.models) == 1
    assert len(ctrl.project.avatars) == 1
    assert ctrl.project.avatars[0].avatar_id == av.avatar_id
    assert len(events) >= 3
    assert ctrl.session.dirty is True


def test_batch_single_signal():
    ctrl = ProjectController()
    ctrl.new_project("b", dimension=2)
    ctrl.add_material(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add_model(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    events = []
    ctrl.state_changed.connect(lambda: events.append(1))

    with ctrl.batch():
        for i in range(5):
            ctrl.add_avatar(
                pre.rigidDisk(r=0.05, center=[i * 0.2, 0], model="rigid", material="STEEL")
            )
    assert len(ctrl.project.avatars) == 5
    assert len(events) == 1  # single emit on batch exit


def test_remove_avatar_by_id():
    ctrl = ProjectController()
    ctrl.new_project("r", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    a = pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL")
    ctrl.add_avatar(a)
    ctrl.remove_avatar(a.avatar_id)
    assert ctrl.project.avatars == []


def test_remove_loop_via_controller():
    ctrl = ProjectController()
    ctrl.new_project("loop", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    prototype = pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL")
    ctrl.add_avatar(prototype)
    ctrl.apply_loop(Loop("circle", prototype.avatar_id, count=3, radius=1.0))
    loop_id = ctrl.project.loops[0].loop_id

    ctrl.remove_loop(loop_id)
    assert ctrl.project.loops == []
    assert [avatar.avatar_id for avatar in ctrl.project.avatars] == [prototype.avatar_id]


def test_remove_for_loop_via_controller():
    ctrl = ProjectController()
    ctrl.new_project("for-loop", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    prototype = pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL")
    ctrl.add_avatar(prototype)
    loop = ForLoop(
        start=0,
        stop=3,
        target_kind="avatar",
        model_avatar_id=prototype.avatar_id,
        group_name="generated",
    )
    ctrl.apply_for_loop(loop)

    ctrl.remove_for_loop(loop.loop_id)
    assert ctrl.project.for_loops == []
    assert [avatar.avatar_id for avatar in ctrl.project.avatars] == [prototype.avatar_id]


def test_deposit_numpy():
    ctrl = ProjectController()
    ctrl.new_project("g", dimension=2)
    ctrl.add(pre.material(name="SAND", materialType="RIGID", density=2500))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    from lmgc90_core import GranuloConfig
    cfg = GranuloConfig(
        nb_particles=20,
        radius_min=0.01,
        radius_max=0.02,
        container_type="Box2D",
        container_params={"lx": 1.0, "ly": 1.0},
        material_name="SAND",
        model_name="rigid",
        seed=42,
    )
    pop = ctrl.deposit(cfg)
    assert len(pop) == 20
    assert len(ctrl.project.populations) == 1


def test_export_scripts(tmp_path: Path):
    ctrl = ProjectController()
    ctrl.new_project("ex", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    ctrl.add(pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL"))
    pre_path = tmp_path / "pre.py"
    cmd_path = tmp_path / "command.py"
    text = ctrl.emit_pre_script(pre_path)
    assert pre_path.is_file()
    assert "from pylmgc90 import pre" in text
    ctrl.emit_chipy_script(cmd_path, dt=1e-3, nb_steps=100)
    assert cmd_path.is_file()


def test_emit_pre_script_uses_performance_preference():
    ctrl = ProjectController()
    ctrl.new_project("compact", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    ctrl.add(pre.rigidDisk(r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL"))
    ctrl.add(pre.rigidDisk(r=0.1, center=[1.0, 0.0], model="rigid", material="STEEL"))
    ctrl.add(pre.rigidDisk(r=0.1, center=[2.0, 0.0], model="rigid", material="STEEL"))

    ctrl.prefs.script_use_loop = False
    expanded = ctrl.emit_pre_script()
    ctrl.prefs.script_use_loop = True
    compact = ctrl.emit_pre_script()

    assert expanded.count("pre.rigidDisk(") == 3
    assert compact.count("pre.rigidDisk(") == 1


def test_save_load_roundtrip(tmp_path: Path):
    ctrl = ProjectController()
    ctrl.new_project("round", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    ctrl.add(pre.rigidDisk(r=0.1, center=[0.5, 0.5], model="rigid", material="STEEL"))
    path = tmp_path / "round.lmgc90"
    ctrl.save_project(path)
    assert path.is_file()

    ctrl2 = ProjectController()
    ctrl2.load_project(path)
    assert ctrl2.project.name == "round"
    assert len(ctrl2.project.avatars) == 1
    assert ctrl2.project.avatars[0].radius == pytest.approx(0.1)


def test_undo_redo():
    ctrl = ProjectController()
    ctrl.new_project("u", dimension=2)
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    assert len(ctrl.project.materials) == 1
    ctrl.undo()
    # undo may leave empty depending on history for first command
    # at least should not crash
    ctrl.redo()


def test_duplicate_material_name_emits_error():
    ctrl = ProjectController()
    ctrl.new_project("d", dimension=2)
    errors = []
    ctrl.error_occurred.connect(lambda m: errors.append(m))
    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    with pytest.raises(ValidationError):
        ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=1000))
    assert errors
