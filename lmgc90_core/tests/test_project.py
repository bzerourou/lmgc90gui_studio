from lmgc90_core import (
    ContactLaw, DOFOperation, ForLoop, GranuloConfig, HistoryError, Loop,
    PostProCommand, Project, ValidationError, VisibilityRule, pre,
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


<<<<<<< HEAD
=======
def test_runtime_material_type_survives_serialization():
    material = pre.material(
        name="JOINT", materialType="JOINT_ELAS", density=0,
        stiffnesses=(1.0, 2.0),
    )

    restored = type(material).from_dict(material.to_dict())

    assert restored.material_type == "JOINT_ELAS"
    assert restored.to_dict() == material.to_dict()


>>>>>>> 634bb2a (new version 0.7.6)
def test_add_normalizes_lmgc_names_and_references_once():
    p = Project()
    material = p.add(pre.material(name="iron", materialType="RIGID", density=1))
    model = p.add(pre.model(
        name="mod", physics="MECAx", element="Rxx2D", dimension=2,
    ))
    law = p.add(ContactLaw(name="law", law_type="IQS_CLB", friction=0.3))
    avatar = p.add(pre.rigidDisk(
        r=0.1, center=[0, 0], model="mod", material="iron", color="RED",
    ))
    rule = p.add(VisibilityRule(
        candidate_body="RBDY2", candidate_contactor="DISKx",
        candidate_color="RED", antagonist_body="RBDY2",
        antagonist_contactor="DISKx", antagonist_color="BLUEx",
        behavior_name="law",
    ))

    assert material.name == "ironx"
    assert model.name == "modxx"
    assert law.name == "lawxx"
    assert avatar.material_name == material.name
    assert avatar.model_name == model.name
    assert avatar.color == "REDxx"
    assert rule.behavior_name == law.name
    assert rule.candidate_color == avatar.color
    assert p.material("iron") is material
    assert p.model("mod") is model


def test_add_conflicts_are_checked_after_name_normalization():
    p = Project()
    existing = p.add(pre.material(name="iron", materialType="RIGID", density=1))

    assert p.add(
        pre.material(name="ironx-extra", materialType="RIGID", density=1),
        on_conflict="skip",
    ) is existing


def test_postpro_removal_and_addition_remain_undoable_in_order():
    p = _empty()
    first = PostProCommand("SOLVER INFORMATIONS", step=10)
    second = PostProCommand("BODY TRACKING", step=20)
    p.add(first)
    p.add(second)

    p.remove_postpro(0)
    assert p.postpro == [second]
    p.undo()
    assert p.postpro == [first, second]
    p.undo()
    assert p.postpro == [first]
    p.redo()
    assert p.postpro == [first, second]


def test_add_see_dof_and_postpro_undo_redo_after_reload(tmp_path):
    p = _empty()
    p.add(ContactLaw(name="law", law_type="IQS_CLB", friction=0.3))
    avatar = p.add(pre.rigidDisk(
        r=0.1, center=[0, 0], model="rigid", material="STEEL",
    ))
    rule = p.add(VisibilityRule(
        candidate_body="RBDY2", candidate_contactor="DISKx",
        candidate_color="BLUEx", antagonist_body="RBDY2",
        antagonist_contactor="JONCx", antagonist_color="WALLx",
        behavior_name="law",
    ))
    operation = p.add(DOFOperation(
        "translate", "avatar", avatar.avatar_id, {"dx": 0.1},
    ))
    postpro = p.add(PostProCommand("BODY TRACKING", step=10))

    path = tmp_path / "command-history.lmgc90"
    p.save(path)
    loaded = Project.load(path)

    loaded.undo()
    assert loaded.postpro == []
    loaded.undo()
    assert loaded.operations == []
    loaded.undo()
    assert loaded.visibility == []

    loaded.redo()
    assert [item.visibility_id for item in loaded.visibility] == [
        rule.visibility_id,
    ]
    loaded.redo()
    assert [item.operation_id for item in loaded.operations] == [
        operation.operation_id,
    ]
    loaded.redo()
    assert loaded.postpro == [postpro]


def test_dynamic_variable_set_and_remove_are_undoable():
    p = _empty()
    p.set_dynamic_var("speed", "1.0")
    p.set_dynamic_var("speed", "2.0")
    p.undo()
    assert p.dynamic_vars == {"speed": "1.0"}
    p.remove_dynamic_var("speed")
    assert p.dynamic_vars == {}
    p.undo()
    assert p.dynamic_vars == {"speed": "1.0"}


def test_remove_avatar_restores_dofs_and_avatar_position_after_reload(tmp_path):
    p = _empty()
    avatars = [
        p.add(pre.rigidDisk(
            r=0.1, center=[float(index), 0], model="rigid", material="STEEL",
        ))
        for index in range(3)
    ]
    operations = [
        DOFOperation("imposeDrivenDof", "avatar", avatar.avatar_id, {"ct": value})
        for avatar, value in (
            (avatars[0], 0.0),
            (avatars[1], 1.0),
            (avatars[2], 2.0),
            (avatars[1], 3.0),
        )
    ]
    for operation in operations:
        p.add(operation)

    p.remove_avatar(avatars[1].avatar_id)
    assert [avatar.avatar_id for avatar in p.avatars] == [
        avatars[0].avatar_id, avatars[2].avatar_id,
    ]
    assert p.operations == [operations[0], operations[2]]

    path = tmp_path / "removed-avatar.lmgc90"
    p.save(path)
    loaded = Project.load(path)
    loaded.undo()
    assert [avatar.avatar_id for avatar in loaded.avatars] == [
        avatar.avatar_id for avatar in avatars
    ]
    assert [operation.operation_id for operation in loaded.operations] == [
        operation.operation_id for operation in operations
    ]

    loaded.redo()
    assert [avatar.avatar_id for avatar in loaded.avatars] == [
        avatars[0].avatar_id, avatars[2].avatar_id,
    ]
    assert loaded.operations == [operations[0], operations[2]]


def test_cannot_remove_avatar_used_as_geometric_loop_template():
    p = _empty()
    template = p.add(pre.rigidDisk(
        r=0.1, center=[0, 0], model="rigid", material="STEEL",
    ))
    p.apply_loop(Loop("line", template.avatar_id, count=2, step=0.2))
    avatar_ids = [avatar.avatar_id for avatar in p.avatars]
    history_size = len(p.history._undo)

    try:
        p.remove_avatar(template.avatar_id)
        assert False, "removing a loop template should fail"
    except ValidationError as exc:
        assert "loop" in str(exc)

    assert [avatar.avatar_id for avatar in p.avatars] == avatar_ids
    assert len(p.history._undo) == history_size


def test_cannot_remove_avatar_used_as_avatar_forloop_template():
    p = _empty()
    template = p.add(pre.rigidDisk(
        r=0.1, center=[0, 0], model="rigid", material="STEEL",
    ))
    p.apply_for_loop(ForLoop(
        target_kind="avatar", model_avatar_id=template.avatar_id,
        start=0, stop=2, expr_x="i",
    ))

    try:
        p.remove_avatar(template.avatar_id)
        assert False, "removing a ForLoop template should fail"
    except ValidationError as exc:
        assert "ForLoop" in str(exc)


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


def test_remove_for_loop_uses_dof_operation_ids_not_local_counters():
    p = _empty()
    wall = p.add(pre.rigidDisk(
        r=0.1, center=[0, 0], model="rigid", material="STEEL",
    ))
    p.group("wall", [wall.avatar_id])
    template = p.add(DOFOperation(
        "imposeDrivenDof", "group", "wall",
        {"component": 1, "dofty": "vlocy", "ct": 0.0},
    ))
    loop = ForLoop(
        start=0, stop=2, target_kind="dof", template_index=0,
    )

    generated = p.apply_for_loop(loop)

    assert len(generated) == 2
    assert loop.generated_ids == [op.operation_id for op in generated]
    assert all(not generated_id.isdigit() for generated_id in loop.generated_ids)
    assert len(set(loop.generated_ids)) == 2

    p.remove_for_loop(loop.loop_id)

    assert p.operations == [template]


def test_remove_for_loop_does_not_treat_legacy_dof_counters_as_indices():
    p = _empty()
    wall = p.add(pre.rigidDisk(
        r=0.1, center=[0, 0], model="rigid", material="STEEL",
    ))
    p.group("wall", [wall.avatar_id])
    template = p.add(DOFOperation(
        "imposeDrivenDof", "group", "wall",
        {"component": 1, "dofty": "vlocy", "ct": 0.0},
    ))
    loop = ForLoop(
        start=0, stop=2, target_kind="dof", template_index=0,
    )
    generated = p.apply_for_loop(loop)
    loop.generated_ids = ["0", "1"]

    p.remove_for_loop(loop.loop_id)

    assert p.operations == [template, *generated]


def test_remove_for_loop_uses_visibility_rule_ids_not_local_counters():
    from lmgc90_core import VisibilityRule

    p = _empty()
    p.add(pre.tact_behav(name="law01", law="GAP_SGR_CLB", fric=0.3))
    template = p.add(VisibilityRule(
        candidate_body="RBDY2", candidate_contactor="DISKx",
        candidate_color="BLUEx", antagonist_body="RBDY2",
        antagonist_contactor="JONCx", antagonist_color="WALLx",
        behavior_name="law01",
    ))
    loop = ForLoop(
        start=0, stop=2, target_kind="visibility", template_index=0,
    )

    generated = p.apply_for_loop(loop)

    assert len(generated) == 2
    assert loop.generated_ids == [rule.visibility_id for rule in generated]
    assert all(not generated_id.isdigit() for generated_id in loop.generated_ids)
    assert len(set(loop.generated_ids)) == 2

    p.remove_for_loop(loop.loop_id)

    assert p.visibility == [template]


def test_remove_for_loop_does_not_treat_legacy_visibility_counters_as_indices():
    from lmgc90_core import VisibilityRule

    p = _empty()
    p.add(pre.tact_behav(name="law01", law="GAP_SGR_CLB", fric=0.3))
    template = p.add(VisibilityRule(
        candidate_body="RBDY2", candidate_contactor="DISKx",
        candidate_color="BLUEx", antagonist_body="RBDY2",
        antagonist_contactor="JONCx", antagonist_color="WALLx",
        behavior_name="law01",
    ))
    loop = ForLoop(
        start=0, stop=2, target_kind="visibility", template_index=0,
    )
    generated = p.apply_for_loop(loop)
    loop.generated_ids = ["0", "1"]

    p.remove_for_loop(loop.loop_id)

    assert p.visibility == [template, *generated]


def test_granulo_distribution_for_loop_uses_persistent_generation_ids():
    p = _empty()
    loop = ForLoop(
        start=0, stop=2, target_kind="granulo_dist",
        expressions={"nb_particles": "10 + i"},
    )

    generated = p.apply_for_loop(loop)

    assert len(generated) == 2
    assert loop.generated_ids == [config.generation_id for config in generated]
    assert all(generated_id.startswith("gen_") for generated_id in loop.generated_ids)
    assert len(set(loop.generated_ids)) == 2

    p.remove_for_loop(loop.loop_id)

    assert p.granulo == []


def test_generated_entity_ids_survive_serialization():
    from lmgc90_core import VisibilityRule

    operation = DOFOperation("translate", "group", "walls", {"dx": 0.1})
    restored_operation = DOFOperation.from_dict(operation.to_dict())
    assert restored_operation.operation_id == operation.operation_id

    rule = VisibilityRule(
        candidate_body="RBDY2", candidate_contactor="DISKx",
        candidate_color="BLUEx", antagonist_body="RBDY2",
        antagonist_contactor="JONCx", antagonist_color="WALLx",
        behavior_name="law01",
    )
    restored_rule = VisibilityRule.from_dict(rule.to_dict())
    assert restored_rule.visibility_id == rule.visibility_id

    config = GranuloConfig(
        nb_particles=10, radius_min=0.01, radius_max=0.02,
        container_type="Box2D", container_params={"lx": 1.0, "ly": 1.0},
        material_name="STEEL", model_name="rigid", create_avatars=False,
    )
    restored_config = GranuloConfig.from_dict(config.to_dict())
    assert restored_config.generation_id == config.generation_id


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


def test_deposit_reuses_scene_granulo_config_and_remove_undo_tracks_one_config():
    p = _empty()
    config = GranuloConfig(
        nb_particles=12,
        radius_min=0.02,
        radius_max=0.03,
        container_type="Box2D",
        container_params={"lx": 1.0, "ly": 1.0},
        material_name="STEEL",
        model_name="rigid",
        seed=3,
        dimension=2,
    )
    p.granulo.append(config)

    population = p.deposit(config)

    assert population is not None
    assert len(p.granulo) == 1
    assert p.granulo[0].generation_id == config.generation_id
    assert p.granulo[0].population_id == population.population_id

    p.remove_population(population.population_id)
    assert p.granulo == []
    p.undo()
    assert len(p.granulo) == 1
    assert p.granulo[0].generation_id == config.generation_id
    p.redo()
    assert p.granulo == []


def test_remove_distribution_only_config_is_undoable():
    p = _empty()
    config = GranuloConfig(
        nb_particles=4,
        radius_min=0.01,
        radius_max=0.02,
        container_type="Box2D",
        container_params={"lx": 1.0, "ly": 1.0},
        material_name="STEEL",
        model_name="rigid",
        create_avatars=False,
        radii=[0.01, 0.012, 0.015, 0.02],
    )
    p.granulo.append(config)

    removed = p.remove_granulo_config(config.generation_id)

    assert removed is config
    assert p.granulo == []
    p.undo()
    assert p.granulo == [config]
    p.redo()
    assert p.granulo == []


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
