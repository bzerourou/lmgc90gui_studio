"""Avalanche sur pente 2D."""
from lmgc90_core import pre
from ._helpers import setup_rigid_2d, iqs_law, see_disk_disk, see_disk_wall


def build(controller) -> None:
    setup_rigid_2d(controller)
    controller.project.name = "avalanche_slope"
    controller.add_avatar(pre.rigidJonc(
        axe1=1.8, axe2=0.06, center=[0.0, 0.0], model="rigid", material="TDURx", color="GRAYx"))
    controller.add_avatar(pre.smoothWall(
        l=2.5, h=0.1, center=[1.2, -0.8], model="rigid", material="TDURx", color="GRAYx"))
    for i in range(12):
        controller.add_avatar(pre.rigidDisk(
            r=0.07, center=[-0.8 + (i % 4) * 0.16, 0.4 + (i // 4) * 0.16],
            model="rigid", material="TDURx", color="BLUEx"))
    iqs_law(controller, "iqsc0", 0.35)
    see_disk_disk(controller, "iqsc0")
    see_disk_wall(controller, "iqsc0")
