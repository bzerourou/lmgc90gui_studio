import math

from lmgc90_core import GranuloConfig, Loop
from lmgc90_core.generate import NumpyGranulo, loop_positions


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
