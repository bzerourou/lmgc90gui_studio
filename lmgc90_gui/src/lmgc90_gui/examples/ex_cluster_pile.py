"""Quelques clusters 2D au-dessus d'un sol."""
from lmgc90_core import pre
from ._helpers import setup_rigid_2d, iqs_law, see_disk_disk, see_disk_wall


def build(controller) -> None:
    setup_rigid_2d(controller)
    controller.project.name = "cluster_pile"
    controller.add_avatar(pre.smoothWall(
        l=3.0, h=0.1, center=[0.0, -0.2], model="rigid", material="TDURx", color="GRAYx"))
    for i, x in enumerate([-0.6, 0.0, 0.6]):
        controller.add_avatar(pre.rigidCluster(
            r=0.05, center=[x, 0.4 + 0.1 * i], model="rigid", material="TDURx",
            color="BLUEx", nb_disk=4))
    iqs_law(controller, "iqsc0", 0.3)
    see_disk_disk(controller, "iqsc0")
    see_disk_wall(controller, "iqsc0")
