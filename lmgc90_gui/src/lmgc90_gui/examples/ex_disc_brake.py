"""Frein à disque simplifié 3D (cylindre + plaquettes)."""
from lmgc90_core import pre
from ._helpers import setup_rigid_3d, iqs_law


def build(controller) -> None:
    setup_rigid_3d(controller, density=7800.0)
    controller.project.name = "disc_brake"
    controller.add_avatar(pre.rigidCylinder(
        r=0.15, h=0.02, center=[0.0, 0.0, 0.0], model="rigid", material="TDURx", color="GRAYx"))
    controller.add_avatar(pre.rigidSphere(
        r=0.03, center=[0.16, 0.0, 0.0], model="rigid", material="TDURx", color="REEDx"))
    controller.add_avatar(pre.rigidSphere(
        r=0.03, center=[-0.16, 0.0, 0.0], model="rigid", material="TDURx", color="REEDx"))
    iqs_law(controller, "iqsc0", 0.5)
    controller.add_visibility(pre.see_table(
        CorpsCandidat="RBDY3", candidat="SPHER", colorCandidat="REEDx",
        CorpsAntagoniste="RBDY3", antagoniste="CYLND", colorAntagoniste="GRAYx",
        behav="iqsc0", alert=0.02))
