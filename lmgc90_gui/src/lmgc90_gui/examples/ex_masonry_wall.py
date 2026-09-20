"""Petit mur de maçonnerie 2D (briques = joncs)."""
from lmgc90_core import pre
from ._helpers import setup_rigid_2d, iqs_law


def build(controller) -> None:
    setup_rigid_2d(controller)
    controller.project.name = "masonry_wall"
    controller.add_avatar(pre.smoothWall(
        l=3.0, h=0.1, center=[0.0, -0.1], model="rigid", material="TDURx", color="GRAYx"))
    lx, ly, gap = 0.25, 0.12, 0.01
    ids = []
    for row in range(5):
        cols = 6 if row % 2 == 0 else 5
        x0 = -0.75 if row % 2 == 0 else -0.75 + (lx + gap) / 2
        for col in range(cols):
            av = controller.add_avatar(pre.rigidJonc(
                axe1=lx / 2, axe2=ly / 2,
                center=[x0 + col * (lx + gap), row * (ly + gap) + 0.1],
                model="rigid", material="TDURx", color="REEDx"))
            ids.append(av.avatar_id)
    iqs_law(controller, "iqsc0", 0.5)
    controller.add_visibility(pre.see_table(
        CorpsCandidat="RBDY2", candidat="JONCx", colorCandidat="REEDx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="REEDx",
        behav="iqsc0", alert=0.02))
    controller.add_visibility(pre.see_table(
        CorpsCandidat="RBDY2", candidat="JONCx", colorCandidat="REEDx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="GRAYx",
        behav="iqsc0", alert=0.02))
    controller.group("briques", ids)
