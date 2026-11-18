from lmgc90_core import AvatarType, Project, scenes


def test_scene_star_import_exports_every_scene_builder():
    namespace = {}
    exec("from lmgc90_core.scenes import *", namespace)

    assert set(scenes.SCENE_BUILDERS).issubset(namespace)
    assert {
        "masonry_deformable_wall",
        "cell_adhesion_v3",
        "cell_adhesion_v4",
        "cell_adhesion_v5",
    }.issubset(namespace)


def test_hopper_visibility_rule_matches_polygon_walls():
    project = Project()
    scenes.hopper_discharge(project)

    walls = [
        avatar for avatar in project.avatars
        if avatar.avatar_id in project.avatar_groups["hopper_walls"]
    ]
    assert len(walls) == 2
    assert all(wall.wall_params["nb_vertex"] >= 3 for wall in walls)

    wall_rule = next(
        rule for rule in project.visibility
        if rule.candidate_contactor == "DISKx"
        and rule.antagonist_color == "GRAYx"
    )
    assert wall_rule.antagonist_contactor == "POLYG"


def test_avalanche_uses_rigid_jonc_for_disk_contacts():
    project = Project()
    scenes.avalanche_slope(project)

    slopes = [
        avatar for avatar in project.avatars
        if avatar.avatar_type == AvatarType.RIGID_JONC
        and avatar.color == "REEDx"
    ]
    assert len(slopes) == 1
    slope_rule = next(
        rule for rule in project.visibility
        if rule.candidate_color == "BLUEx"
        and rule.antagonist_color == "REEDx"
    )
    assert slope_rule.candidate_contactor == "DISKx"
    assert slope_rule.antagonist_contactor == "JONCx"


def test_biaxial_compression_drives_jonc_walls_and_matches_disks():
    project = Project()
    scenes.biaxial_compression(project)

    press_wall_ids = set(project.avatar_groups["press_walls"])
    press_walls = [
        avatar for avatar in project.avatars
        if avatar.avatar_id in press_wall_ids
    ]
    assert len(press_walls) == 2
    assert all(wall.avatar_type == AvatarType.RIGID_JONC for wall in press_walls)

    horizontal_velocities = {
        operation.target_value: operation.parameters["ct"]
        for operation in project.operations
        if operation.operation_type == "imposeDrivenDof"
        and operation.target_value in press_wall_ids
        and operation.parameters.get("component") == 1
    }
    assert set(horizontal_velocities.values()) == {-0.2, 0.2}

    wall_rule = next(
        rule for rule in project.visibility
        if rule.candidate_color == "BLUEx"
        and rule.antagonist_color == "GRAYx"
    )
    assert wall_rule.candidate_contactor == "DISKx"
    assert wall_rule.antagonist_contactor == "JONCx"

    project.deposit(project.granulo[0])
    script = project.to_pre_script()
    assert script.count("pre.rigidJonc(") == 3
    assert "antagoniste='JONCx'" in script
    assert "ct': 0.2" in script
    assert "ct': -0.2" in script


def test_ball_bearing_has_clearance_fixed_inner_race_and_ball_contacts():
    project = Project()
    scenes.ball_bearing(project)

    outer = next(avatar for avatar in project.avatars if avatar.color == "GRAYx")
    inner = next(avatar for avatar in project.avatars if avatar.color == "ORANx")
    balls = [
        avatar for avatar in project.avatars
        if avatar.avatar_id in project.avatar_groups["billes"]
    ]
    assert len(balls) == 7
    assert outer.is_hollow
    assert inner.is_hollow is False

    ball = balls[0]
    center_distance = (ball.center[0] ** 2 + ball.center[1] ** 2) ** 0.5
    inner_gap = center_distance - inner.radius - ball.radius
    outer_gap = outer.radius - center_distance - ball.radius
    assert inner_gap > 0.0
    assert outer_gap > 0.0
    inner_drives = [
        operation for operation in project.operations
        if operation.operation_type == "imposeDrivenDof"
        and operation.target_value == inner.avatar_id
    ]
    assert any(operation.parameters.get("component") == [1, 2]
               and operation.parameters.get("ct") == 0.0
               for operation in inner_drives)
    assert any(operation.parameters.get("component") == 3
               and operation.parameters.get("ct", 0.0) > 0.0
               for operation in inner_drives)

    assert {
        (rule.candidate_contactor, rule.antagonist_contactor,
         rule.candidate_color, rule.antagonist_color)
        for rule in project.visibility
    } == {
        ("DISKx", "DISKx", "BLUEx", "ORANx"),
        ("DISKx", "xKSID", "BLUEx", "GRAYx"),
        ("DISKx", "DISKx", "BLUEx", "BLUEx"),
    }

    script = project.to_pre_script()
    assert "is_Hollow=True" in script
    assert "antagoniste='xKSID'" in script
    assert "antagoniste='DISKx', colorAntagoniste='BLUEx'" in script
