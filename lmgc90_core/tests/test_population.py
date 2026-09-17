import numpy as np
import pytest

from lmgc90_core import ParticlePopulation
from lmgc90_core.types import AvatarOrigin, AvatarType
from lmgc90_core.validate import compatible_contactors, is_shape_compatible


def test_create_rejects_nonpositive_radius():
    with pytest.raises(ValueError, match="positive"):
        ParticlePopulation.create(
            avatar_type="rigidDisk", material_name="STEEL", model_name="rigid",
            centers=[[0, 0]], radii=[0.0],
        )


def test_create_rejects_bad_dim():
    with pytest.raises(ValueError, match="centers"):
        ParticlePopulation.create(
            avatar_type="rigidDisk", material_name="STEEL", model_name="rigid",
            centers=[[0, 0, 0, 0]], radii=[0.1],
        )


def test_derived_ids_and_view():
    pop = ParticlePopulation.create(
        avatar_type=AvatarType.RIGID_DISK,
        material_name="STEEL", model_name="rigid",
        centers=np.array([[0.0, 0.0], [1.0, 0.0]]),
        radii=np.array([0.1, 0.2]),
        origin=AvatarOrigin.GRANULO,
    )
    assert pop.particle_avatar_id(0) == f"{pop.population_id}:0"
    view = pop.as_avatar_view(1)
    assert view.center == [1.0, 0.0]
    assert view.radius == 0.2
    assert view.avatar_id == f"{pop.population_id}:1"
    meta = pop.to_meta_dict()
    assert "centers" not in meta
    assert meta["n_particles"] == 2


def test_contactors_mesh_vs_rigid():
    from lmgc90_core.types import AvatarType
    assert "CLxxx" in compatible_contactors(AvatarType.MESH_DEFORMABLE, 2)
    assert is_shape_compatible("DISKx", AvatarType.RIGID_DISK, 2)
    assert not is_shape_compatible("CLxxx", AvatarType.RIGID_DISK, 2)
