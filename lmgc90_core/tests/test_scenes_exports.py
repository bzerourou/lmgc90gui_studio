from lmgc90_core import scenes


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
