"""Helpers for example builders — only lmgc90_core + controller public API."""
from __future__ import annotations

from lmgc90_core import pre


def setup_rigid_2d(controller, *, density: float = 2500.0) -> None:
    controller.project.dimension = 2
    controller.add_material(
        pre.material(name="TDURx", materialType="RIGID", density=density)
    )
    controller.add_model(
        pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2)
    )


def setup_rigid_3d(controller, *, density: float = 2500.0) -> None:
    controller.project.dimension = 3
    controller.add_material(
        pre.material(name="TDURx", materialType="RIGID", density=density)
    )
    controller.add_model(
        pre.model(name="rigid", physics="MECAx", element="Rxx3D", dimension=3)
    )


def iqs_law(controller, name: str = "iqsc0", fric: float = 0.3):
    return controller.add_law(pre.tact_behav(name=name, law="IQS_CLB", fric=fric))


def see_disk_wall(controller, law: str = "iqsc0", alert: float = 0.05):
    controller.add_visibility(
        pre.see_table(
            CorpsCandidat="RBDY2",
            candidat="DISKx",
            colorCandidat="BLUEx",
            CorpsAntagoniste="RBDY2",
            antagoniste="JONCx",
            colorAntagoniste="GRAYx",
            behav=law,
            alert=alert,
        )
    )


def see_disk_disk(controller, law: str = "iqsc0", alert: float = 0.05):
    controller.add_visibility(
        pre.see_table(
            CorpsCandidat="RBDY2",
            candidat="DISKx",
            colorCandidat="BLUEx",
            CorpsAntagoniste="RBDY2",
            antagoniste="DISKx",
            colorAntagoniste="BLUEx",
            behav=law,
            alert=alert,
        )
    )
