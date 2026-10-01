from types import SimpleNamespace

from lmgc90_gui.views.tabs.visibility_tab import (
    _body_options,
    _project_contact_options,
    _project_shapes,
)


def _avatar(avatar_type, center, color, contactors=()):
    return SimpleNamespace(
        avatar_type=avatar_type,
        center=center,
        color=color,
        contactors=list(contactors),
    )


def test_contact_options_keep_contactor_color_associated_with_its_shape():
    project = SimpleNamespace(
        dimension=2,
        avatars=[_avatar(
            "rigidDisk",
            [0.0, 0.0],
            "BLUEx",
            (
                {"shape": "DISKx", "color": "REDxx"},
                {"shape": "xKSID", "color": "GREEx"},
            ),
        )],
        populations=[],
    )

    options = _project_contact_options(project)

    assert ("RBDY2", "DISKx", "REDxx", "candidate") in options
    assert ("RBDY2", "xKSID", "GREEx", "candidate") in options
    assert ("RBDY2", "DISKx", "GREEx", "candidate") not in options


def test_mesh_contactors_use_mail_body_and_their_own_color():
    project = SimpleNamespace(
        dimension=2,
        avatars=[_avatar(
            "mesh",
            [0.0, 0.0],
            "CYANx",
            ({"shape": "CLxxx", "color": "ORANx"},),
        )],
        populations=[],
    )

    assert ("MAILx", "CLxxx", "ORANx", "both") in _project_contact_options(project)


def test_body_options_follow_project_dimension_and_scene_entities():
    project = SimpleNamespace(
        dimension=3,
        avatars=[_avatar("mesh", [0.0, 0.0, 0.0], "CYANx")],
        populations=[],
        visibility=[],
    )

    assert _body_options(project) == ["RBDY3", "MAILx"]


def test_default_contactor_suggestion_matches_avatar_type_and_dimension():
    project = SimpleNamespace(
        dimension=2,
        avatars=[_avatar("rigidDisk", [0.0, 0.0], "BLUEx")],
        populations=[],
    )

    assert _project_contact_options(project) == [
        ("RBDY2", "DISKx", "BLUEx", "candidate")
    ]


def test_population_suggestions_match_its_dimension_type_and_color():
    population = SimpleNamespace(
        avatar_type="rigidSphere",
        dimension=3,
        color="GOLDx",
    )
    project = SimpleNamespace(
        dimension=3,
        avatars=[],
        populations=[population],
    )

    assert _project_contact_options(project) == [
        ("RBDY3", "SPHER", "GOLDx", "candidate")
    ]


def test_shapes_for_link_dialog_are_filtered_by_candidate_or_antagonist_role():
    project = SimpleNamespace(
        dimension=2,
        avatars=[
            _avatar("rigidDisk", [0.0, 0.0], "BLUEx"),
            _avatar("roughWall", [0.0, 0.0], "GRAYx"),
        ],
        populations=[],
    )

    assert _project_shapes(project, role="candidate") == ["DISKx"]
    assert _project_shapes(project, role="antagonist") == ["JONCx"]