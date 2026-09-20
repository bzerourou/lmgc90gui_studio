"""DOF : disque libre + mur fixe (imposeDrivenDof)."""
from lmgc90_core import pre, DOFOperation
from ._helpers import setup_rigid_2d, iqs_law, see_disk_wall


def build(controller) -> None:
    setup_rigid_2d(controller)
    controller.project.name = "dof_conditions"
    floor = controller.add_avatar(pre.smoothWall(
        l=2.0, h=0.1, center=[0.0, 0.0], model="rigid", material="TDURx", color="GRAYx"))
    controller.add_avatar(pre.rigidDisk(
        r=0.12, center=[0.0, 0.5], model="rigid", material="TDURx", color="BLUEx"))
    iqs_law(controller, "iqsc0", 0.3)
    see_disk_wall(controller, "iqsc0")
    controller.add_dof(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="avatar",
        target_value=floor.avatar_id,
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
