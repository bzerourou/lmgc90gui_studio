"""Pile de sphères 3D sur un plan."""
from lmgc90_core import pre
from ._helpers import setup_rigid_3d, iqs_law


def build(controller) -> None:
    setup_rigid_3d(controller)
    controller.project.name = "sphere_stack"
    controller.add_avatar(pre.rigidPlan(
        axe1=1.5, axe2=1.5, axe3=0.05, center=[0.0, 0.0, -0.1],
        model="rigid", material="TDURx", color="GRAYx"))
    for iz in range(4):
        for iy in range(3):
            for ix in range(3):
                controller.add_avatar(pre.rigidSphere(
                    r=0.08,
                    center=[(ix - 1) * 0.18, (iy - 1) * 0.18, 0.1 + iz * 0.18],
                    model="rigid", material="TDURx", color="BLUEx"))
    iqs_law(controller, "iqsc0", 0.25)
    controller.add_visibility(pre.see_table(
        CorpsCandidat="RBDY3", candidat="SPHER", colorCandidat="BLUEx",
        CorpsAntagoniste="RBDY3", antagoniste="SPHER", colorAntagoniste="BLUEx",
        behav="iqsc0", alert=0.05))
    controller.add_visibility(pre.see_table(
        CorpsCandidat="RBDY3", candidat="SPHER", colorCandidat="BLUEx",
        CorpsAntagoniste="RBDY3", antagoniste="PLANx", colorAntagoniste="GRAYx",
        behav="iqsc0", alert=0.05))
