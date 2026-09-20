"""Dépôt granulométrique 2D (population SoA)."""
import numpy as np
from lmgc90_core import pre
from lmgc90_core.population import ParticlePopulation
from ._helpers import setup_rigid_2d, iqs_law, see_disk_disk, see_disk_wall


def build(controller) -> None:
    setup_rigid_2d(controller)
    controller.project.name = "granulo_deposit"
    controller.add_avatar(pre.smoothWall(
        l=3.0, h=0.1, center=[0.0, -0.2], model="rigid", material="TDURx", color="GRAYx"))
    rng = np.random.default_rng(42)
    n = 40
    centers = rng.uniform([-1.0, 0.2], [1.0, 1.5], size=(n, 2))
    radii = rng.uniform(0.04, 0.08, size=n)
    pop = ParticlePopulation.create(
        avatar_type="rigidDisk",
        material_name="TDURx",
        model_name="rigid",
        centers=centers,
        radii=radii,
        color="CYANx",
    )
    controller.add_population(pop)
    iqs_law(controller, "iqsc0", 0.35)
    see_disk_wall(controller, "iqsc0")
    see_disk_disk(controller, "iqsc0")
