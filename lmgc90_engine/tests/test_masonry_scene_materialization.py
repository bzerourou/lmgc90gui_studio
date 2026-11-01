import pytest

pytest.importorskip("pylmgc90")

from lmgc90_core import Project
from lmgc90_core.scenes.demos import (
    cohesive_wall,
    masonry_deformable_wall,
    masonry_wall,
)
from lmgc90_engine.materialize import materialize_project


@pytest.mark.pylmgc
@pytest.mark.parametrize(
    "builder",
    [masonry_wall, cohesive_wall, masonry_deformable_wall],
    ids=["masonry_wall", "cohesive_wall", "masonry_deformable_wall"],
)
def test_masonry_scenes_materialize_with_pylmgc(builder):
    project = Project(name=builder.__name__, dimension=2)
    builder(project)

    materialize_project(project)