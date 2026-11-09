import math

import numpy as np
import pytest

from lmgc90_core import GranuloConfig, Loop
from lmgc90_core import generate
from lmgc90_core.generate import NumpyGranulo, loop_positions
from lmgc90_core.types import AvatarType


def test_circle_on_radius():
    loop = Loop("Cercle", "x", count=8, radius=2.0, offset_x=1.0, offset_y=0.5)
    pts = loop_positions(loop)
    assert len(pts) == 8
    for x, y in pts:
        dist = math.hypot(x - 1.0, y - 0.5)
        assert abs(dist - 2.0) < 1e-12


def test_grid_3x3():
    loop = Loop("grid", "x", count=9, step=1.0)
    pts = loop_positions(loop)
    assert pts == [
        [0, 0], [1, 0], [2, 0],
        [0, 1], [1, 1], [2, 1],
        [0, 2], [1, 2], [2, 2],
    ]


def test_line_vertical():
    loop = Loop("line", "x", count=3, step=1.5, invert_axis=True)
    pts = loop_positions(loop)
    assert [c[0] for c in pts] == [0, 0, 0]
    assert [c[1] for c in pts] == [0.0, 1.5, 3.0]


def test_numpy_box_is_deterministic():
    cfg = GranuloConfig(
        nb_particles=60, radius_min=0.03, radius_max=0.05,
        container_type="Box2D", container_params={"lx": 1.2, "ly": 1.2},
        material_name="STEEL", model_name="rigid", seed=7,
    )
    a = NumpyGranulo().deposit(cfg)
    b = NumpyGranulo().deposit(cfg)
    assert a.nb_placed == b.nb_placed
    assert (a.population.centers == b.population.centers).all()
    lo, hi = a.population.bounds()
    assert lo[0] >= -0.6 - 1e-9 and hi[0] <= 0.6 + 1e-9


def test_particles_do_not_overlap():
    cfg = GranuloConfig(
        nb_particles=40, radius_min=0.04, radius_max=0.04,
        container_type="Disk2D", container_params={"r": 0.8},
        material_name="STEEL", model_name="rigid", seed=3,
    )
    res = NumpyGranulo().deposit(cfg)
    c, r = res.population.centers, res.population.radii
    for i in range(len(r)):
        d2 = ((c[i + 1:] - c[i]) ** 2).sum(axis=1)
        min2 = (r[i + 1:] + r[i]) ** 2
        assert (d2 >= min2 - 1e-12).all()


@pytest.mark.parametrize(
    "distribution_type",
    ["granulo_ReadFromFile", "granulo_BetaDistribution"],
)
def test_pre_sampled_radii_are_retried_after_rejected_candidates(
    monkeypatch, distribution_type,
):
    config = GranuloConfig(
        nb_particles=2,
        radius_min=0.1,
        radius_max=0.1,
        container_type="Box2D",
        container_params={"lx": 2.0, "ly": 2.0},
        material_name="MAT",
        model_name="MODEL",
        distribution_type=distribution_type,
    )
    monkeypatch.setattr(
        generate, "sample_radii",
        lambda config, *, rng: np.array([0.1, 0.1]),
    )
    generator = NumpyGranulo()
    sampled_batches = 0

    def sample_centers(rng, n, cfg, radii):
        nonlocal sampled_batches
        sampled_batches += 1
        if sampled_batches == 1:
            return np.full((n, 2), 10.0)
        centers = np.tile([[0.3, 0.3], [1.5, 1.5]], (n // 2 + 1, 1))
        return centers[:n]

    monkeypatch.setattr(generator, "_sample", sample_centers)

    result = generator.deposit(config)

    assert result.nb_placed == 2
    assert result.attempts > len(result.population.radii)
    assert sampled_batches >= 2


@pytest.mark.parametrize(
    ("avatar_type", "dimension", "nb_vertices"),
    [
        (AvatarType.RIGID_POLYGON, 2, 6),
        (AvatarType.RIGID_POLYHEDRON, 3, 8),
    ],
)
def test_numpy_deposit_sets_polygon_population_shape_parameters(
    avatar_type, dimension, nb_vertices,
):
    config = GranuloConfig(
        nb_particles=1,
        radius_min=0.1,
        radius_max=0.1,
        container_type="Box2D" if dimension == 2 else "Box3D",
        container_params={"lx": 1.0, "ly": 1.0, "lz": 1.0},
        material_name="MAT",
        model_name="MODEL",
        avatar_type=avatar_type.value,
        dimension=dimension,
        seed=1,
    )

    result = NumpyGranulo().deposit(config)

    assert result.population.extra_params["nb_vertices"] == nb_vertices
