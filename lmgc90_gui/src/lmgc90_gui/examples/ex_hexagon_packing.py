"""Empilement hexagonal de disques."""
import math
from lmgc90_core import pre
from ._helpers import setup_rigid_2d, iqs_law, see_disk_disk, see_disk_wall


def build(controller) -> None:
    setup_rigid_2d(controller)
    controller.project.name = "hexagon_packing"
    controller.add_avatar(pre.smoothWall(
        l=3.0, h=0.1, center=[0.0, -0.15], model="rigid", material="TDURx", color="GRAYx"))
    r = 0.08
    rows, cols = 5, 8
    for j in range(rows):
        for i in range(cols):
            x = -0.9 + i * 2 * r * 1.05 + (r if j % 2 else 0)
            y = 0.1 + j * r * math.sqrt(3)
            controller.add_avatar(pre.rigidDisk(
                r=r, center=[x, y], model="rigid", material="TDURx", color="BLUEx"))
    iqs_law(controller, "iqsc0", 0.25)
    see_disk_disk(controller, "iqsc0")
    see_disk_wall(controller, "iqsc0")
