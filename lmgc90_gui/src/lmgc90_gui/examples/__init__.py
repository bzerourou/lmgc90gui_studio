"""GUI catalog — metadata only; geometry in ``lmgc90_core.scenes``."""
from __future__ import annotations

from lmgc90_core.scenes import SCENE_BUILDERS
from lmgc90_core.scenes import (
    cell_adhesion_v1,
    cell_adhesion_v2,
    cell_adhesion_v3,
    cell_adhesion_v4,
    cell_adhesion_v5,
    avalanche_slope,
    ball_bearing,
    biaxial_compression,
    cable_pendulum,
    circle_loop,
    cluster_pile,
    cohesive_wall,
    couette_shear,
    deformable_drop,
    deformable_impact,
    disc_brake,
    dof_conditions,
    dumbbell,
    factory_injection,
    falling_disks,
    for_loop_ramp,
    granulo_deposit,
    hexagon_packing,
    hopper_discharge,
    l_shaped_wall,
    masonry_wall,
    rotating_drum,
    sphere_stack,
)
from .base import ExampleSpec

EXAMPLES: list[ExampleSpec] = [
    ExampleSpec("falling_disks", "🎱 Chute de disques 2D", "Bases",
        "Sol unique + boucle de disques.", 2, "Débutant", falling_disks, tags=["loop"]),
    ExampleSpec("sphere_stack", "⚪ Pile de sphères 3D", "Bases",
        "Sphères sur plan.", 3, "Débutant", sphere_stack, tags=["3D"]),
    ExampleSpec("dof_conditions", "📌 Conditions DOF", "Bases",
        "Mur fixé + disque libre.", 2, "Débutant", dof_conditions, tags=["DOF"]),
    ExampleSpec("for_loop_ramp", "🔁 Boucle For (rayons)", "Génération",
        "Rayon croissant via ForLoop.", 2, "Intermédiaire", for_loop_ramp, tags=["ForLoop"]),
    ExampleSpec("circle_loop", "⭕ Boucle circulaire", "Génération",
        "Disques en cercle.", 2, "Débutant", circle_loop, tags=["loop"]),
    ExampleSpec("hexagon_packing", "⬡ Empilement hexagonal", "Génération",
        "Réseau hexagonal.", 2, "Débutant", hexagon_packing, tags=["packing"]),
    ExampleSpec("granulo_deposit", "⚪ Dépôt granulométrique", "Génération",
        "500 disques Box2D (depositInBox2D).", 2, "Intermédiaire", granulo_deposit, tags=["granulo"]),
    ExampleSpec("couette_shear", "🔄 Cellule de Couette", "Génération",
        "Dépôt anneau Couette2D.", 2, "Intermédiaire", couette_shear, tags=["granulo", "Couette"]),
    ExampleSpec("factory_injection", "🏭 Factory (injection)", "Génération",
        "Conteneur + premier batch (meta factory).", 2, "Avancé", factory_injection, tags=["factory"]),
    ExampleSpec("masonry_wall", "🧱 Mur de maçonnerie", "Structures",
        "Briques JONCx.", 2, "Intermédiaire", masonry_wall, tags=["masonry"]),
    ExampleSpec("cohesive_wall", "🔗 Mur cohésif (CZM)", "Structures",
        "Assises + IQS_MAC_CZM.", 2, "Avancé", cohesive_wall, tags=["CZM"]),
    ExampleSpec("l_shaped_wall", "📐 Mur en L", "Structures",
        "Assise + colonne en L.", 2, "Intermédiaire", l_shaped_wall, tags=["masonry"]),
    ExampleSpec("rotating_drum", "⚙️ Tambour rotatif", "Mécanismes",
        "Disque creux + Drum2D.", 2, "Avancé", rotating_drum, tags=["drum"]),
    ExampleSpec("hopper_discharge", "⬇️ Décharge en trémie", "Mécanismes",
        "Parois en V + dépôt.", 2, "Avancé", hopper_discharge, tags=["hopper"]),
    ExampleSpec("avalanche_slope", "🏔️ Avalanche sur pente", "Mécanismes",
        "Fondation inclinée + grains.", 2, "Intermédiaire", avalanche_slope, tags=["slope"]),
    ExampleSpec("biaxial_compression", "↔️ Compression biaxiale", "Mécanismes",
        "Parois verticales + lit granulaire.", 2, "Avancé", biaxial_compression, tags=["biaxial"]),
    ExampleSpec("ball_bearing", "⚙️ Roulement à billes", "Mécanismes",
        "Type 608 coupe 2D.", 2, "Avancé", ball_bearing, tags=["bearing"]),
    ExampleSpec("disc_brake", "🚲 Frein à disque", "Mécanismes",
        "Cylindre 3D simplifié.", 3, "Avancé", disc_brake, tags=["3D"]),
    ExampleSpec("cluster_pile", "🔗 Clusters", "Avatars",
        "rigidCluster sur sol unique.", 2, "Intermédiaire", cluster_pile, tags=["cluster"]),
    ExampleSpec("dumbbell", "🏋️ Haltère", "Avatars",
        "emptyAvatar + contacteurs.", 2, "Intermédiaire", dumbbell, tags=["emptyAvatar"]),
    ExampleSpec("cable_pendulum", "🎯 Pendule", "Avatars",
        "Ancrage + masse.", 2, "Intermédiaire", cable_pendulum, tags=["DOF"]),
                    ExampleSpec("cell_adhesion_v5", "🧬 Cellule (vague 5 — showcase)", "Biologie",
        "Complet : dual DATBOX SPRD/STBL + PHASES.json + DOF predefined.", 3, "Expert",
        cell_adhesion_v5, tags=["cell", "3D", "showcase", "DATBOX"]),
    ExampleSpec("cell_adhesion_v4", "🧬 Cellule (vague 4)", "Biologie",
        "DOF predefined focals + dual phase SPRD/STBL + post-pro.", 3, "Avancé",
        cell_adhesion_v4, tags=["cell", "3D", "SPRD", "STBL"]),
    ExampleSpec("cell_adhesion_v3", "🧬 Cellule (vague 3)", "Biologie",
        "Réseaux MF/MT/IF + ELASTIC_WIRE/ROD + membrane + focals.", 3, "Avancé",
        cell_adhesion_v3, tags=["cell", "3D", "cytoskeleton"]),
    ExampleSpec("cell_adhesion_v2", "🧬 Cellule (vague 2)", "Biologie",
        "Membrane cellulaire + focals + noyau + cytosol + substrat.", 3, "Avancé",
        cell_adhesion_v2, tags=["cell", "3D", "biology", "focals"]),
    ExampleSpec("cell_adhesion_v1", "🧬 Cellule (vague 1)", "Biologie",
        "Substrat + membrane noyau + cytosol 3D (squelette Vassaux).", 3, "Avancé",
        cell_adhesion_v1, tags=["cell", "3D", "biology"]),
    ExampleSpec("deformable_drop", "🟦 Déformable sur sol", "Déformables",
        "Maillage T3 + sol + GAP_SGR_CLB.", 2, "Avancé", deformable_drop, tags=["FEM"]),
    ExampleSpec("deformable_impact", "🟦 Déformable (impact)", "Déformables",
        "Maillage plus fin + CLxxx.", 2, "Avancé", deformable_impact, tags=["FEM"]),
]

for _ex in EXAMPLES:
    assert _ex.id in SCENE_BUILDERS, _ex.id
    assert SCENE_BUILDERS[_ex.id] is _ex.scene, _ex.id


def get_examples():
    return list(EXAMPLES)


def get_example(example_id: str):
    for ex in EXAMPLES:
        if ex.id == example_id:
            return ex
    return None


__all__ = ["ExampleSpec", "EXAMPLES", "get_examples", "get_example"]
