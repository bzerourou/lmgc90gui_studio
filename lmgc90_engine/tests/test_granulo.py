from __future__ import annotations

from types import SimpleNamespace
import sys

import numpy as np
import pytest

from lmgc90_core import GranuloConfig
from lmgc90_core.types import AvatarType
from lmgc90_engine import granulo
from lmgc90_engine.granulo import _call_deposit


@pytest.mark.parametrize(
    ("container_type", "expected_helper"),
    [
        ("Disk2D", "depositInDisk2D"),
        ("Drum2D", "depositInDrum2D"),
    ],
)
def test_disk_and_drum_use_their_matching_helper_first(
    container_type, expected_helper,
):
    calls = []

    def radii_factory(count, radius_min, radius_max, seed=None):
        return np.full(count, radius_min)

    def make_deposit_helper(name):
        def deposit(radii, container_radius):
            calls.append(name)
            return len(radii), np.zeros((len(radii), 2)), radii

        return deposit

    fake_pre = SimpleNamespace(
        granulo_Random=radii_factory,
        depositInDisk2D=make_deposit_helper("depositInDisk2D"),
        depositInDrum2D=make_deposit_helper("depositInDrum2D"),
    )
    config = GranuloConfig(
        nb_particles=2,
        radius_min=0.1,
        radius_max=0.2,
        container_type=container_type,
        container_params={"r": 1.0},
        material_name="MAT",
        model_name="MODEL",
    )

    _call_deposit(fake_pre, config)

    assert calls == [expected_helper]


@pytest.mark.parametrize(
    ("avatar_type", "dimension", "nb_vertices"),
    [
        (AvatarType.RIGID_POLYGON, 2, 6),
        (AvatarType.RIGID_POLYHEDRON, 3, 8),
    ],
)
def test_pylmgc_deposit_sets_polygon_population_shape_parameters(
    monkeypatch, avatar_type, dimension, nb_vertices,
):
    monkeypatch.setitem(sys.modules, "pylmgc90", SimpleNamespace(pre=object()))
    monkeypatch.setattr(
        granulo, "_call_deposit",
        lambda _pre, _config: (np.zeros((1, dimension)), np.array([0.1])),
    )
    config = GranuloConfig(
        nb_particles=1,
        radius_min=0.1,
        radius_max=0.2,
        container_type="Box2D" if dimension == 2 else "Box3D",
        container_params={"lx": 1.0, "ly": 1.0, "lz": 1.0},
        material_name="MAT",
        model_name="MODEL",
        avatar_type=avatar_type.value,
        dimension=dimension,
    )

    population = granulo.deposit_population(config)

    assert population.extra_params["nb_vertices"] == nb_vertices
