from lmgc90_core import (
    DOFOperation, ForLoop, GranuloConfig, HistoryError, Loop, Project,
    ValidationError, pre,
)


def _empty() -> Project:
    p = Project(name="t", dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    return p


def test_add_and_undo_avatar():
    p = _empty()
    av = p.add(pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL"))
    assert p.n_bodies == 1
    p.undo()
    assert p.n_bodies == 0
    p.redo()
    assert p.avatar(av.avatar_id).radius == 0.1


def test_duplicate_material_rejected():
    p = _empty()
    try:
        p.add(pre.material(name="STEEL", materialType="RIGID", density=1))
        assert False
    except ValidationError:
        pass


def test_unknown_material_on_avatar():
    p = _empty()
    try:
        p.add(pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="XXXXX"))
        assert False
    except Exception:
        pass


def test_group_and_dof():
    p = _empty()
    a = p.add(pre.rigidDisk(r=0.05, center=[0, 0], model="rigid", material="STEEL", color="BLUEx"))
    p.group("grains", [a.avatar_id])
    p.add(DOFOperation("imposeDrivenDof", "group", "grains",
                       {"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0}))
    assert len(p.operations) == 1
    p.undo()
    assert len(p.operations) == 0


def test_loop_is_one_undo_step():
    p = _empty()
    proto = p.add(pre.rigidDisk(r=0.04, center=[0, 0], model="rigid", material="STEEL"))
    gen = p.apply_loop(Loop("circle", proto.avatar_id, count=12, radius=1.0, group_name="ring"))
    assert len(gen) == 12
    assert p.n_bodies == 13
    assert len(p.avatars_in("ring")) == 12
    p.undo()
    assert p.n_bodies == 1
    assert "ring" not in p.avatar_groups or p.avatars_in("ring") == []


def test_remove_loop_removes_generated_avatars_and_is_undoable():
    p = _empty()
    proto = p.add(pre.rigidDisk(r=0.04, center=[0, 0], model="rigid", material="STEEL"))
    p.group("ring", [proto.avatar_id])
    generated = p.apply_loop(
        Loop("circle", proto.avatar_id, count=4, radius=1.0, group_name="ring")
    )
    p.add(DOFOperation(
        "imposeDrivenDof", "avatar", generated[0].avatar_id,
        {"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    loop_id = p.loops[0].loop_id

    p.remove_loop(loop_id)
    assert p.loops == []
    assert [avatar.avatar_id for avatar in p.avatars] == [proto.avatar_id]
    assert p.avatars_in("ring") == [proto]
    assert p.operations == []

    p.undo()
    assert len(p.loops) == 1
    assert {avatar.avatar_id for avatar in p.avatars} == {
        proto.avatar_id, *(avatar.avatar_id for avatar in generated)
    }
    assert len(p.avatars_in("ring")) == 5
    assert len(p.operations) == 1

    p.redo()
    assert p.loops == []
    assert [avatar.avatar_id for avatar in p.avatars] == [proto.avatar_id]
    assert p.avatars_in("ring") == [proto]
    assert p.operations == []


def test_remove_for_loop_removes_generated_avatars_and_is_undoable():
    p = _empty()
    proto = p.add(pre.rigidDisk(r=0.04, center=[0, 0], model="rigid", material="STEEL"))
    loop = ForLoop(
        var_name="i",
        start=0,
        stop=4,
        step=1,
        target_kind="avatar",
        model_avatar_id=proto.avatar_id,
        expr_x="i * 0.2",
        group_name="forlp",
    )
    generated = p.apply_for_loop(loop)
    p.add(DOFOperation(
        "imposeDrivenDof", "avatar", generated[0].avatar_id,
        {"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))

    p.remove_for_loop(loop.loop_id)
    assert p.for_loops == []
    assert [avatar.avatar_id for avatar in p.avatars] == [proto.avatar_id]
    assert p.avatar_groups == {}
    assert p.operations == []

    p.undo()
    assert p.for_loops == [loop]
    assert {avatar.avatar_id for avatar in p.avatars} == {
        proto.avatar_id, *(avatar.avatar_id for avatar in generated)
    }
    assert len(p.operations) == 1

    p.redo()
    assert p.for_loops == []
    assert [avatar.avatar_id for avatar in p.avatars] == [proto.avatar_id]
    assert p.operations == []


def test_remove_for_loop_removes_generated_materials():
    p = _empty()
    loop = ForLoop(
        start=0,
        stop=3,
        target_kind="material",
        template_name="STEEL",
        expressions={"density": "1000 + i"},
    )
    generated = p.apply_for_loop(loop)
    assert len(generated) == 3
    assert len(p.materials) == 4

    p.remove_for_loop(loop.loop_id)
    assert p.for_loops == []
    assert [material.name for material in p.materials] == ["STEEL"]

    p.undo()
    assert len(p.materials) == 4
    assert p.for_loops == [loop]


def test_deposit_is_soa_and_one_undo():
    p = _empty()
    pop = p.deposit(GranuloConfig(
        nb_particles=80, radius_min=0.02, radius_max=0.03,
        container_type="Box2D", container_params={"lx": 1.0, "ly": 1.0},
        material_name="STEEL", model_name="rigid", seed=0, dimension=2,
    ))
    assert len(pop) > 0
    assert len(p.avatars) == 0
    assert p.n_bodies == len(pop)
    p.undo()
    assert p.n_bodies == 0


def test_undo_empty_raises():
    p = Project()
    try:
        p.undo()
        assert False
    except HistoryError:
        pass


def test_journal_records_ops():
    p = _empty()
    p.add(pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL"))
    ops = [j["op"] for j in p.journal()]
    assert ops == ["add_material", "add_model", "add_avatar"]
