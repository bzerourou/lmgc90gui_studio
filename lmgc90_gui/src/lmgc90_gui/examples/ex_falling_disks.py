"""Chute de disques 2D sous gravité dans une boîte ouverte."""
from lmgc90_core import pre
from ._helpers import setup_rigid_2d, iqs_law, see_disk_disk, see_disk_wall


def build(controller) -> None:
    setup_rigid_2d(controller)
    controller.project.name = "falling_disks"
    controller.add_avatar(pre.smoothWall(
        l=4.0, h=0.1, center=[0.0, -0.5], model="rigid", material="TDURx", color="GRAYx"))
    ids = []
    for i in range(10):
        av = controller.add_avatar(pre.rigidDisk(
            r=0.1, center=[-1.35 + i * 0.3, 1.0], model="rigid", material="TDURx", color="BLUEx"))
        ids.append(av.avatar_id)
    iqs_law(controller, "iqsc0", 0.3)
    see_disk_wall(controller, "iqsc0")
    see_disk_disk(controller, "iqsc0")
    controller.group("disques_chute", ids)
