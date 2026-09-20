"""Trémie 2D avec ouverture et dépôt de disques."""
from lmgc90_core import pre
from ._helpers import setup_rigid_2d, iqs_law, see_disk_disk, see_disk_wall


def build(controller) -> None:
    setup_rigid_2d(controller)
    controller.project.name = "hopper_discharge"
    # silo walls (approximated with joncs)
    controller.add_avatar(pre.rigidJonc(axe1=1.2, axe2=0.05, center=[-0.8, 1.0], model="rigid", material="TDURx", color="GRAYx"))
    controller.add_avatar(pre.rigidJonc(axe1=1.2, axe2=0.05, center=[0.8, 1.0], model="rigid", material="TDURx", color="GRAYx"))
    # hopper slopes
    controller.add_avatar(pre.rigidJonc(axe1=0.6, axe2=0.05, center=[-0.45, 0.2], model="rigid", material="TDURx", color="GRAYx"))
    controller.add_avatar(pre.rigidJonc(axe1=0.6, axe2=0.05, center=[0.45, 0.2], model="rigid", material="TDURx", color="GRAYx"))
    # floor
    controller.add_avatar(pre.smoothWall(l=3.0, h=0.08, center=[0.0, -0.6], model="rigid", material="TDURx", color="GRAYx"))
    for i in range(8):
        for j in range(5):
            controller.add_avatar(pre.rigidDisk(
                r=0.07, center=[-0.45 + i * 0.12, 0.6 + j * 0.15],
                model="rigid", material="TDURx", color="BLUEx"))
    iqs_law(controller, "iqsc0", 0.3)
    see_disk_disk(controller, "iqsc0")
    see_disk_wall(controller, "iqsc0")
