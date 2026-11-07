"""Wall avatar factory calls must match the supported pre constructors."""
from __future__ import annotations

import pytest

from lmgc90_core import pre
from lmgc90_engine.avatar_factory import (
    _call_supported_signature,
    _apply_contactors,
    build_avatar,
)
from lmgc90_engine.errors import MaterializationError


def test_compatible_call_selects_signature_before_invoking():
    calls = []

    def factory(mesh, model, material, color):
        calls.append((mesh, model, material, color))
        return "body"

    result = _call_supported_signature(factory, [
        ((), {
            "surfacic_mesh": "mesh",
            "model": "model",
            "material": "material",
            "color": "color",
        }),
        (("mesh", "model", "material", "color"), {}),
    ])

    assert result == "body"
    assert calls == [("mesh", "model", "material", "color")]


def test_typeerror_inside_factory_is_not_retried_with_another_signature():
    calls = []

    def factory(*, surfacic_mesh, model, material, color):
        calls.append(surfacic_mesh)
        raise TypeError("factory implementation failed")

    with pytest.raises(TypeError, match="factory implementation failed"):
        _call_supported_signature(factory, [
            ((), {
                "surfacic_mesh": "mesh",
                "model": "model",
                "material": "material",
                "color": "color",
            }),
            (("mesh", "model", "material", "color"), {}),
        ])

    assert calls == ["mesh"]


@pytest.mark.parametrize("group", [None, ""])
def test_mesh_contactor_requires_explicit_group(group):
    avatar = pre.meshed_rectangle(
        lx=1.0, ly=1.0, nx=1, ny=1, center=[0, 0],
        model="mesh", material="MAT",
        contactors=[{"shape": "CLxxx", "color": "CYANx", **(
            {"group": group} if group is not None else {}
        )}],
    )

    class Body:
        def __init__(self):
            self.added = []

        def addContactors(self, **kwargs):
            self.added.append(kwargs)

    body = Body()
    with pytest.raises(MaterializationError, match="requires an explicit non-empty group"):
        _apply_contactors(body, avatar)

    assert body.added == []


def test_mesh_contactor_uses_only_the_explicit_group():
    avatar = pre.meshed_rectangle(
        lx=1.0, ly=1.0, nx=1, ny=1, center=[0, 0],
        model="mesh", material="MAT",
        contactors=[{"shape": "CLxxx", "color": "CYANx", "group": "right"}],
    )

    class Body:
        def __init__(self):
            self.added = []

        def addContactors(self, **kwargs):
            self.added.append(kwargs)

    body = Body()
    _apply_contactors(body, avatar)

    assert body.added == [{
        "shape": "CLxxx", "group": "right", "color": "CYANx",
    }]


def test_mesh_contactor_accepts_legacy_by_as_explicit_group():
    avatar = pre.meshed_rectangle(
        lx=1.0, ly=1.0, nx=1, ny=1, center=[0, 0],
        model="mesh", material="MAT",
        contactors=[{"shape": "CLxxx", "color": "CYANx", "by": "down"}],
    )

    class Body:
        def __init__(self):
            self.added = []

        def addContactors(self, **kwargs):
            self.added.append(kwargs)

    body = Body()
    _apply_contactors(body, avatar)

    assert body.added == [{
        "shape": "CLxxx", "group": "down", "color": "CYANx",
    }]


def test_mesh_contactor_rejects_conflicting_by_and_group():
    avatar = pre.meshed_rectangle(
        lx=1.0, ly=1.0, nx=1, ny=1, center=[0, 0],
        model="mesh", material="MAT",
        contactors=[{
            "shape": "CLxxx", "color": "CYANx",
            "by": "down", "group": "up",
        }],
    )

    class Body:
        def addContactors(self, **kwargs):
            raise AssertionError("invalid contactor must not be added")

    with pytest.raises(MaterializationError, match="conflicting 'by' and 'group'"):
        _apply_contactors(Body(), avatar)


@pytest.mark.parametrize(
    "shape, constructor, center, options",
    [
        (
            "PT2Dx",
            pre.rigidDisk,
            [0, 0],
            {"color": "VERTx", "shift": [0.0, 0.0]},
        ),
        (
            "PT3Dx",
            pre.rigidSphere,
            [0, 0, 0],
            {"color": "BNOYp"},
        ),
    ],
)
def test_point_contactors_attach_to_rigid_bodies_without_mesh_group(
    shape, constructor, center, options,
):
    avatar = constructor(
        r=0.1, center=center, model="rigid", material="MAT",
    )
    avatar.contactors.append({"shape": shape, **options})

    class Body:
        def __init__(self):
            self.added = []

        def addContactors(self, **kwargs):
            self.added.append(kwargs)

    body = Body()
    _apply_contactors(body, avatar)

    assert body.added == [{"shape": shape, **options}]


@pytest.mark.parametrize(
    "shape, options",
    [
        ("DISKx", {"byrd": 0.1, "shfit": [0.0, 0.0]}),
        ("CLxxx", {"group": "down", "colro": "CYANx"}),
    ],
)
def test_unknown_contactor_options_raise_instead_of_being_dropped(shape, options):
    avatar = pre.meshed_rectangle(
        lx=1.0, ly=1.0, nx=1, ny=1, center=[0, 0],
        model="mesh", material="MAT",
        contactors=[{"shape": shape, **options}],
    )

    class Body:
        def __init__(self):
            self.added = []

        def addContactors(self, **kwargs):
            self.added.append(kwargs)

    body = Body()
    with pytest.raises(
        MaterializationError,
        match=f"{shape} contactor has unsupported option",
    ):
        _apply_contactors(body, avatar)

    assert body.added == []


class _WallPre:
    def fineWall(
        self, *, l, r, center, model, material, color="BLUEx", nb_vertex=10,
    ):
        return {
            "kind": "fineWall", "l": l, "r": r, "center": center,
            "model": model, "material": material, "color": color,
            "nb_vertex": nb_vertex,
        }

    def granuloRoughWall(
        self, *, l, rmin, rmax, center, model, material, color="BLUEx",
        nb_vertex=10,
    ):
        return {
            "kind": "granuloRoughWall", "l": l, "rmin": rmin, "rmax": rmax,
            "center": center, "model": model, "material": material,
            "color": color, "nb_vertex": nb_vertex,
        }


def test_fine_wall_factory_uses_supported_parameters(monkeypatch):
    monkeypatch.setattr("lmgc90_engine.avatar_factory._pre", _WallPre)
    avatar = pre.fineWall(
        l=2.0, h=0.08, nb_vertex=16, center=[0.0, 0.0],
        model="rigid", material="WALL",
    )

    body = build_avatar(
        avatar, materials={"WALL": object()}, models={"rigid": object()},
    )

    assert body["kind"] == "fineWall"
    assert (body["l"], body["r"], body["nb_vertex"]) == (2.0, 0.04, 16)


def test_granulo_rough_wall_factory_uses_supported_parameters(monkeypatch):
    monkeypatch.setattr("lmgc90_engine.avatar_factory._pre", _WallPre)
    avatar = pre.granuloRoughWall(
        l=2.0, h=0.06, rmin=0.01, nb_vertex=18, center=[0.0, 0.0],
        model="rigid", material="WALL",
    )

    body = build_avatar(
        avatar, materials={"WALL": object()}, models={"rigid": object()},
    )

    assert body["kind"] == "granuloRoughWall"
    assert (body["l"], body["rmin"], body["rmax"], body["nb_vertex"]) == (
        2.0, 0.01, 0.03, 18,
    )
