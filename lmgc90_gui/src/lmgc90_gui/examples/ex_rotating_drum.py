"""Tambour rotatif 2D (disques dans un anneau de joncs)."""
import math
from lmgc90_core import pre
from ._helpers import setup_rigid_2d, iqs_law, see_disk_disk, see_disk_wall


def build(controller) -> None:
    setup_rigid_2d(controller)
    controller.project.name = "rotating_drum"
    # rough approximation: polygon of short walls
    R, nseg = 1.0, 24
    for i in range(nseg):
        a0 = 2 * math.pi * i / nseg
        a1 = 2 * math.pi * (i + 1) / nseg
        mx = 0.5 * R * (math.cos(a0) + math.cos(a1))
        my = 0.5 * R * (math.sin(a0) + math.sin(a1))
        controller.add_avatar(pre.rigidJonc(
            axe1=0.15, axe2=0.04, center=[mx, my], model="rigid",
            material="TDURx", color="GRAYx"))
    for i in range(15):
        a = 2 * math.pi * i / 15
        controller.add_avatar(pre.rigidDisk(
            r=0.06, center=[0.45 * math.cos(a), 0.45 * math.sin(a)],
            model="rigid", material="TDURx", color="BLUEx"))
    iqs_law(controller, "iqsc0", 0.4)
    see_disk_disk(controller, "iqsc0")
    see_disk_wall(controller, "iqsc0")
