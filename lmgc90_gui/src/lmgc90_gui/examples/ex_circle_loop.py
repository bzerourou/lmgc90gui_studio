"""Boucle circulaire de disques 2D."""
import math
from lmgc90_core import pre
from ._helpers import setup_rigid_2d, iqs_law, see_disk_disk


def build(controller) -> None:
    setup_rigid_2d(controller)
    controller.project.name = "circle_loop"
    ids = []
    n, R, r = 12, 0.8, 0.08
    for i in range(n):
        a = 2 * math.pi * i / n
        av = controller.add_avatar(pre.rigidDisk(
            r=r, center=[R * math.cos(a), R * math.sin(a)], model="rigid",
            material="TDURx", color="BLUEx"))
        ids.append(av.avatar_id)
    controller.add_avatar(pre.rigidDisk(
        r=0.15, center=[0.0, 0.0], model="rigid", material="TDURx", color="REEDx"))
    iqs_law(controller, "iqsc0", 0.2)
    see_disk_disk(controller, "iqsc0")
    controller.group("anneau", ids)
