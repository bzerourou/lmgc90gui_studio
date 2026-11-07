"""Exercise avatar factory behavior without requiring pylmgc90."""
from __future__ import annotations

import sys
from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest

from lmgc90_core import Avatar, AvatarType, ParticlePopulation
from lmgc90_engine import avatar_factory


def _avatar(avatar_type: AvatarType, **kwargs) -> Avatar:
    center = kwargs.pop("center", [2.0, 3.0])
    return Avatar(
        avatar_type=avatar_type,
        center=center,
        material_name="MAT",
        model_name="MODEL",
        **kwargs,
    )


def _build(monkeypatch, pre, avatar: Avatar):
    monkeypatch.setattr(avatar_factory, "_pre", lambda: pre)
    return avatar_factory.build_avatar(
        avatar, materials={"MAT": "material"}, models={"MODEL": "model"},
    )


def test_rigid_factories_forward_normalized_parameters(monkeypatch):
    calls = []

    def rigid_disk(*, r, center, model, material, color, is_Hollow=False):
        calls.append(("disk", {
            "r": r, "center": center, "model": model, "material": material,
            "color": color, "is_Hollow": is_Hollow,
        }))
        return "disk"

    def rigid_cylinder(**kwargs):
        calls.append(("cylinder", kwargs))
        return "cylinder"

    pre = SimpleNamespace(rigidDisk=rigid_disk, rigidCylinder=rigid_cylinder)
    disk = _avatar(
        AvatarType.RIGID_DISK, radius=0.25, is_hollow=True,
    )
    cylinder = _avatar(
        AvatarType.RIGID_CYLINDER, radius=0.5, wall_params={"h": 1.25},
    )

    assert _build(monkeypatch, pre, disk) == "disk"
    assert _build(monkeypatch, pre, cylinder) == "cylinder"
    assert calls == [
        ("disk", {
            "r": 0.25, "center": [2.0, 3.0], "model": "model",
            "material": "material", "color": "BLUEx", "is_Hollow": True,
        }),
        ("cylinder", {
            "r": 0.5, "h": 1.25, "center": [2.0, 3.0], "model": "model",
            "material": "material", "color": "BLUEx",
        }),
    ]


@pytest.mark.parametrize(
    "avatar_type, avatar_options, factory_name, expected",
    [
        (AvatarType.RIGID_SPHERE, {"radius": 0.3}, "rigidSphere", {"r": 0.3}),
        (
            AvatarType.RIGID_JONC, {"axis": {"axe1": 0.8, "axe2": 0.2}},
            "rigidJonc", {"axe1": 0.8, "axe2": 0.2},
        ),
        (
            AvatarType.RIGID_DISCRETE, {"radius": 0.4},
            "rigidDiscreteDisk", {"r": 0.4},
        ),
        (
            AvatarType.RIGID_CLUSTER, {"radius": 0.5, "nb_vertices": 7},
            "rigidCluster", {"r": 0.5, "nb_disk": 7},
        ),
        (
            AvatarType.RIGID_PLAN, {"axis": {"axe1": 1.0, "axe2": 2.0, "axe3": 3.0}},
            "rigidPlan", {"axe1": 1.0, "axe2": 2.0, "axe3": 3.0},
        ),
        (
            AvatarType.RIGID_OVOID, {"radius": 0.6}, "rigidOvoidPolygon",
            {"radius": 0.6},
        ),
    ],
)
def test_remaining_rigid_factories_use_avatar_properties(
    monkeypatch, avatar_type, avatar_options, factory_name, expected,
):
    calls = []

    def factory(**kwargs):
        calls.append(kwargs)
        return "body"

    avatar = _avatar(avatar_type, **avatar_options)
    assert _build(
        monkeypatch, SimpleNamespace(**{factory_name: factory}), avatar,
    ) == "body"
    assert len(calls) == 1
    for key, value in expected.items():
        assert calls[0][key] == value
    assert calls[0]["center"] == [2.0, 3.0]
    assert calls[0]["model"] == "model"
    assert calls[0]["material"] == "material"


def test_polygon_vertices_are_localized_before_factory_call(monkeypatch):
    calls = []

    def rigid_polygon(**kwargs):
        calls.append(kwargs)
        return "polygon"

    avatar = _avatar(
        AvatarType.RIGID_POLYGON,
        vertices=[[1.0, 2.0], [3.0, 2.0], [2.0, 4.0]],
    )
    assert _build(monkeypatch, SimpleNamespace(rigidPolygon=rigid_polygon), avatar) == "polygon"

    assert calls[0]["generation_type"] == "full"
    np.testing.assert_array_equal(
        calls[0]["vertices"], [[-1.0, -1.0], [1.0, -1.0], [0.0, 1.0]],
    )
    assert calls[0]["model"] == "model"
    assert calls[0]["material"] == "material"


def test_polyhedron_factory_receives_vertex_geometry(monkeypatch):
    calls = []

    def rigid_polyhedron(**kwargs):
        calls.append(kwargs)
        return "polyhedron"

    avatar = _avatar(
        AvatarType.RIGID_POLYHEDRON,
        vertices=[
            [0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
        ],
    )
    assert _build(
        monkeypatch, SimpleNamespace(rigidPolyhedron=rigid_polyhedron), avatar,
    ) == "polyhedron"

    assert calls[0]["generation_type"] == "vertices"
    assert calls[0]["nb_vertices"] == 4
    np.testing.assert_array_equal(calls[0]["vertices"], avatar.vertices)


def test_rigid_factory_errors_are_wrapped_with_avatar_context(monkeypatch):
    avatar = _avatar(AvatarType.RIGID_DISK, radius=0.25)

    def broken_factory(**kwargs):
        raise RuntimeError("constructor failed")

    with pytest.raises(
        avatar_factory.MaterializationError,
        match=f"failed to build rigidDisk avatar_id={avatar.avatar_id}: constructor failed",
    ):
        _build(monkeypatch, SimpleNamespace(rigidDisk=broken_factory), avatar)


def test_expand_mesh_calls_reader_and_factory_without_keyword_signature(monkeypatch):
    calls = []
    bodies = [object(), object()]

    class FakePre:
        def readMesh(self, filepath, dimension):
            calls.append(("read", filepath, dimension))
            return "mesh"

        def rigidsFromMesh2D(self, mesh, model, material, color):
            calls.append(("expand", mesh, model, material, color))
            return bodies

    monkeypatch.setattr(avatar_factory, "_pre", FakePre)
    monkeypatch.setattr(
        avatar_factory, "resolve_mesh_filepath",
        lambda filepath, *, dim, mesh_size=None: "resolved.msh",
    )
    avatar = _avatar(
        AvatarType.EMPTY_AVATAR,
        mesh_params={"filepath": "mesh.msh", "dim": 2},
    )

    result = avatar_factory.expand_rigids_from_mesh2d(
        avatar, materials={"MAT": "material"}, models={"MODEL": "model"},
    )

    assert result == bodies
    assert calls == [
        ("read", "resolved.msh", 2),
        ("expand", "mesh", "model", "material", "BLUEx"),
    ]


def test_deformable_rectangle_builds_mesh_at_avatar_center(monkeypatch):
    calls = []

    class FakePre:
        def buildMesh2D(self, mesh_type, x0, y0, lx, ly, nx, ny):
            calls.append(("mesh", mesh_type, x0, y0, lx, ly, nx, ny))
            return "mesh"

        def buildMeshedAvatar(self, *, mesh, model, material):
            calls.append(("avatar", mesh, model, material))
            return "deformable"

    avatar = _avatar(
        AvatarType.MESH_DEFORMABLE,
        mesh_params={"geom": "Rectangle", "lx": 4.0, "ly": 2.0, "nx": 4, "ny": 2},
    )
    assert _build(monkeypatch, FakePre(), avatar) == "deformable"

    assert calls == [
        ("mesh", "2T3", 0.0, 2.0, 4.0, 2.0, 4, 2),
        ("avatar", "mesh", "model", "material"),
    ]


def test_deformable_h8_uses_3d_mesh_builder(monkeypatch):
    calls = []

    class FakePre:
        def buildMesh2D(self, *args):
            raise AssertionError("2D mesh builder is not used for H8")

        def buildMeshH8(self, *args):
            calls.append(("mesh", args))
            return "mesh3d"

        def buildMeshedAvatar(self, *, mesh, model, material):
            calls.append(("avatar", mesh, model, material))
            return "deformable3d"

    avatar = _avatar(
        AvatarType.MESH_DEFORMABLE,
        center=[2.0, 3.0, 4.0],
        mesh_params={
            "geom": "H8", "lx": 2.0, "ly": 4.0, "lz": 6.0,
            "nx": 2, "ny": 4, "nz": 6,
        },
    )
    assert _build(monkeypatch, FakePre(), avatar) == "deformable3d"
    assert calls == [
        ("mesh", (1.0, 1.0, 1.0, 2.0, 4.0, 6.0, 2, 4, 6)),
        ("avatar", "mesh3d", "model", "material"),
    ]


@pytest.mark.parametrize(
    ("geom", "center", "params", "expected_dimension", "expected_method"),
    [
        ("Disque", [1.0, 2.0], {"r": 0.5, "nr": 4, "ntheta": 16}, 2, "disk"),
        (
            "Sphère", [1.0, 2.0, 3.0],
            {"r": 0.5, "nr": 4, "ntheta": 16, "nphi": 8},
            3, "sphere",
        ),
        (
            "Cylindre", [1.0, 2.0, 3.0],
            {"r": 0.5, "h": 1.5, "nr": 4, "ntheta": 16, "nz": 6},
            3, "cylinder",
        ),
    ],
)
def test_gmsh_primitive_geometry_materializes(
    monkeypatch, geom, center, params, expected_dimension, expected_method,
):
    calls = []

    class OCC:
        def addDisk(self, *args):
            calls.append(("disk", args))

        def addSphere(self, *args):
            calls.append(("sphere", args))

        def addCylinder(self, *args):
            calls.append(("cylinder", args))

        def synchronize(self):
            calls.append(("synchronize",))

    class Mesh:
        def generate(self, dimension):
            calls.append(("generate", dimension))

    class Model:
        occ = OCC()
        mesh = Mesh()

        def add(self, name):
            calls.append(("model", name))

    class Option:
        def setNumber(self, name, value):
            calls.append(("option", name, value))

    class FakeGmsh:
        model = Model()
        option = Option()

        @staticmethod
        def initialize():
            calls.append(("initialize",))

        @staticmethod
        def write(path):
            Path(path).write_text("mesh", encoding="utf-8")
            calls.append(("write",))

        @staticmethod
        def finalize():
            calls.append(("finalize",))

    class FakePre:
        def readMesh(self, path, dimension):
            assert Path(path).is_file()
            calls.append(("read", dimension))
            return "mesh"

        def buildMeshedAvatar(self, *, mesh, model, material):
            calls.append(("avatar", mesh, model, material))
            return "deformable"

    monkeypatch.setitem(sys.modules, "gmsh", FakeGmsh)
    avatar = _avatar(
        AvatarType.MESH_DEFORMABLE,
        center=center,
        mesh_params={"geom": geom, **params},
    )

    assert _build(monkeypatch, FakePre(), avatar) == "deformable"
    assert ("generate", expected_dimension) in calls
    assert any(call[0] == expected_method for call in calls)
    assert ("read", expected_dimension) in calls
    assert calls[-2] == ("read", expected_dimension)
    assert calls[-1] == ("avatar", "mesh", "model", "material")


def test_external_mesh_reader_supports_legacy_one_argument_signature(
    monkeypatch, tmp_path,
):
    calls = []
    mesh_file = tmp_path / "mesh.msh"
    mesh_file.write_text("mesh", encoding="utf-8")

    class FakePre:
        def buildMesh2D(self, *args):
            raise AssertionError("rectangle mesh builder is not used for file meshes")

        def readMesh(self, filepath):
            calls.append(("read", filepath))
            return "mesh"

        def buildMeshedAvatar(self, mesh, model, material, /):
            calls.append(("avatar", mesh, model, material))
            return "deformable"

    monkeypatch.setattr(avatar_factory, "_pre", FakePre)
    avatar = _avatar(
        AvatarType.MESH_DEFORMABLE,
        mesh_params={"geom": "file", "filepath": str(mesh_file), "dim": 2},
    )

    assert _build(monkeypatch, FakePre(), avatar) == "deformable"
    assert calls == [
        ("read", str(mesh_file.resolve())),
        ("avatar", "mesh", "model", "material"),
    ]


def test_deformable_brick_uses_supported_brick_parameters(monkeypatch):
    calls = []

    class Brick:
        def deformableBrick(self, **kwargs):
            calls.append(kwargs)
            return "brick"

    class FakePre:
        @staticmethod
        def brick2D(name, lx, ly):
            calls.append({"name": name, "lx": lx, "ly": ly})
            return Brick()

    avatar = _avatar(
        AvatarType.MESH_DEFORMABLE,
        mesh_params={
            "geom": "deformableBrick",
            "brick_name": "B1",
            "brick_lx": 1.2,
            "brick_ly": 0.6,
            "nb_elem_x": 3,
            "nb_elem_y": 2,
            "mesh_type": "Q4",
            "colors": ["REDxx"],
        },
    )
    assert _build(monkeypatch, FakePre(), avatar) == "brick"

    assert calls[0] == {"name": "B1", "lx": 1.2, "ly": 0.6}
    assert calls[1]["center"] == [2.0, 3.0]
    assert calls[1]["mesh_type"] == "Q4"
    assert calls[1]["nb_elem_x"] == 3
    assert calls[1]["nb_elem_y"] == 2
    assert calls[1]["colors"] == ["REDxx"]


def test_empty_avatar_uses_native_constructor_signature(monkeypatch):
    calls = []

    class FakePre:
        def emptyAvatar(self, *, model, material):
            calls.append((model, material))
            return "empty"

    avatar = _avatar(AvatarType.EMPTY_AVATAR)
    assert _build(monkeypatch, FakePre(), avatar) == "empty"
    assert calls == [("model", "material")]


def test_empty_avatar_builds_composite_shell_when_native_constructor_absent(
    monkeypatch,
):
    calls = []

    class Body:
        def addBulk(self, bulk):
            calls.append(("bulk", bulk))

        def addNode(self, node):
            calls.append(("node", node))

        def defineGroups(self):
            calls.append(("groups",))

        def defineModel(self, *, model):
            calls.append(("model", model))

        def defineMaterial(self, *, material):
            calls.append(("material", material))

    class FakePre:
        @staticmethod
        def avatar(dimension):
            calls.append(("avatar", dimension))
            return Body()

        @staticmethod
        def rigid2d():
            return "bulk"

        @staticmethod
        def node(*, coor, number):
            return ("node", coor.tolist(), number)

    avatar = _avatar(AvatarType.EMPTY_AVATAR)
    _build(monkeypatch, FakePre(), avatar)
    assert calls[0] == ("avatar", 2)
    assert calls[1] == ("bulk", "bulk")
    assert calls[2] == ("node", ("node", [2.0, 3.0], 1))
    assert calls[3:] == [("groups",), ("model", "model"), ("material", "material")]


def test_empty_brick_uses_brick_rigid_factory(monkeypatch):
    calls = []

    class Brick:
        def rigidBrick(self, *, center, model, material, color):
            calls.append((center, model, material, color))
            return "rigid-brick"

    class FakePre:
        @staticmethod
        def brick2D(name, lx, ly):
            calls.append((name, lx, ly))
            return Brick()

    avatar = _avatar(
        AvatarType.EMPTY_AVATAR,
        wall_params={"brick_name": "brick", "l": 1.0, "h": 0.25},
    )
    assert _build(monkeypatch, FakePre(), avatar) == "rigid-brick"
    assert calls == [
        ("brick", 1.0, 0.25),
        ([2.0, 3.0], "model", "material", "BLUEx"),
    ]


def test_population_expansion_passes_each_particle_to_constructor(monkeypatch):
    calls = []

    class FakePre:
        def rigidDisk(self, **kwargs):
            calls.append(kwargs)
            return ("body", kwargs["center"])

    population = ParticlePopulation.create(
        avatar_type=AvatarType.RIGID_DISK,
        material_name="MAT",
        model_name="MODEL",
        centers=[[0.0, 1.0], [2.0, 3.0]],
        radii=[0.1, 0.2],
    )
    monkeypatch.setattr(avatar_factory, "_pre", FakePre)

    bodies = avatar_factory.build_population_bodies(
        population, materials={"MAT": "material"}, models={"MODEL": "model"},
    )

    assert bodies == [("body", [0.0, 1.0]), ("body", [2.0, 3.0])]
    assert [call["r"] for call in calls] == [0.1, 0.2]
    assert all(call["model"] == "model" for call in calls)
    assert all(call["material"] == "material" for call in calls)


def test_population_constructor_error_identifies_particle(monkeypatch):
    class FakePre:
        def rigidDisk(self, **kwargs):
            raise RuntimeError("bad particle")

    population = ParticlePopulation.create(
        avatar_type=AvatarType.RIGID_DISK,
        material_name="MAT",
        model_name="MODEL",
        centers=[[0.0, 1.0]],
        radii=[0.1],
        population_id="pop_test",
    )
    monkeypatch.setattr(avatar_factory, "_pre", FakePre)

    with pytest.raises(
        avatar_factory.MaterializationError,
        match="population pop_test particle 0: bad particle",
    ):
        avatar_factory.build_population_bodies(
            population, materials={"MAT": "material"}, models={"MODEL": "model"},
        )


@pytest.mark.parametrize(
    ("avatar_type", "constructor_name", "dimension", "nb_vertices"),
    [
        (AvatarType.RIGID_POLYGON, "rigidPolygon", 2, 6),
        (AvatarType.RIGID_POLYHEDRON, "rigidPolyhedron", 3, 8),
    ],
)
def test_polygon_population_uses_radius_constructor_argument(
    monkeypatch, avatar_type, constructor_name, dimension, nb_vertices,
):
    calls = []

    class FakePre:
        def rigidPolygon(self, **kwargs):
            calls.append(("rigidPolygon", kwargs))
            return "polygon"

        def rigidPolyhedron(self, **kwargs):
            calls.append(("rigidPolyhedron", kwargs))
            return "polyhedron"

    population = ParticlePopulation.create(
        avatar_type=avatar_type,
        material_name="MAT",
        model_name="MODEL",
        centers=[[0.0] * dimension],
        radii=[0.25],
    )
    monkeypatch.setattr(avatar_factory, "_pre", FakePre)

    bodies = avatar_factory.build_population_bodies(
        population, materials={"MAT": "material"}, models={"MODEL": "model"},
    )

    assert bodies == ["polygon" if dimension == 2 else "polyhedron"]
    assert calls == [
        (constructor_name, {
            "radius": 0.25,
            "center": [0.0] * dimension,
            "model": "model",
            "material": "material",
            "color": population.color,
            "generation_type": "regular",
            "nb_vertices": nb_vertices,
        }),
    ]
