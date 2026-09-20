"""GUI catalog of examples — NO scene geometry here.

All builders live in ``lmgc90_core.scenes``. Loading::

    controller.new_project(id, dimension=...)
    controller.apply_scene(example.scene)
"""
from __future__ import annotations

from lmgc90_core.scenes import SCENE_BUILDERS
from lmgc90_core.scenes import (
    avalanche_slope,
    ball_bearing,
    cable_pendulum,
    circle_loop,
    cluster_pile,
    cohesive_wall,
    disc_brake,
    dof_conditions,
    dumbbell,
    falling_disks,
    for_loop_ramp,
    granulo_deposit,
    hexagon_packing,
    hopper_discharge,
    masonry_wall,
    rotating_drum,
    sphere_stack,
)

from .base import ExampleSpec

EXAMPLES: list[ExampleSpec] = [
    ExampleSpec("falling_disks", "🎱 Chute de disques 2D", "Bases",
        "Disques sous gravité, sol unique, boucle ligne.", 2, "Débutant", falling_disks,
        tags=["avatar", "loop"]),
    ExampleSpec("sphere_stack", "⚪ Pile de sphères 3D", "Bases",
        "Empilement de sphères sur un plan.", 3, "Débutant", sphere_stack, tags=["3D"]),
    ExampleSpec("dof_conditions", "📌 Conditions DOF", "Bases",
        "Mur fixé + disque libre.", 2, "Débutant", dof_conditions, tags=["DOF"]),
    ExampleSpec("for_loop_ramp", "🔁 Boucle For (rayons)", "Génération",
        "12 disques, rayon croissant via ForLoop.", 2, "Intermédiaire", for_loop_ramp,
        tags=["ForLoop"]),
    ExampleSpec("circle_loop", "⭕ Boucle circulaire", "Génération",
        "Disques en cercle via Loop.", 2, "Débutant", circle_loop, tags=["loop"]),
    ExampleSpec("hexagon_packing", "⬡ Empilement hexagonal", "Génération",
        "Réseau hexagonal sur un sol.", 2, "Débutant", hexagon_packing, tags=["packing"]),
    ExampleSpec("granulo_deposit", "⚪ Dépôt granulométrique", "Génération",
        "500 disques Box2D (depositInBox2D / NumpyGranulo).", 2, "Intermédiaire",
        granulo_deposit, tags=["granulo", "SoA"]),
    ExampleSpec("masonry_wall", "🧱 Mur de maçonnerie", "Structures",
        "Briques JONCx en appareil.", 2, "Intermédiaire", masonry_wall, tags=["masonry"]),
    ExampleSpec("cohesive_wall", "🔗 Mur cohésif (CZM)", "Structures",
        "Deux assises + IQS_MAC_CZM.", 2, "Avancé", cohesive_wall, tags=["CZM"]),
    ExampleSpec("rotating_drum", "⚙️ Tambour rotatif", "Mécanismes",
        "Disque creux + dépôt Drum2D.", 2, "Avancé", rotating_drum, tags=["drum", "granulo"]),
    ExampleSpec("hopper_discharge", "⬇️ Décharge en trémie", "Mécanismes",
        "Deux roughWall en V + dépôt Box2D.", 2, "Avancé", hopper_discharge, tags=["hopper"]),
    ExampleSpec("avalanche_slope", "🏔️ Avalanche sur pente", "Mécanismes",
        "Une fondation inclinée + nuage de grains.", 2, "Intermédiaire", avalanche_slope,
        tags=["slope"]),
    ExampleSpec("ball_bearing", "⚙️ Roulement à billes", "Mécanismes",
        "Type 608 coupe 2D (bagues + 7 billes).", 2, "Avancé", ball_bearing, tags=["bearing"]),
    ExampleSpec("disc_brake", "🚲 Frein à disque (simplifié)", "Mécanismes",
        "Cylindre 3D + plaquettes.", 3, "Avancé", disc_brake, tags=["3D"]),
    ExampleSpec("cluster_pile", "🔗 Clusters", "Avatars",
        "Grille de rigidCluster dans une boîte.", 2, "Intermédiaire", cluster_pile,
        tags=["cluster"]),
    ExampleSpec("dumbbell", "🏋️ Haltère composite", "Avatars",
        "emptyAvatar + contacteurs DISKx/JONCx.", 2, "Intermédiaire", dumbbell,
        tags=["emptyAvatar"]),
    ExampleSpec("cable_pendulum", "🎯 Pendule", "Avatars",
        "Ancrage fixe + masse (disques).", 2, "Intermédiaire", cable_pendulum, tags=["DOF"]),
]

for _ex in EXAMPLES:
    if _ex.id not in SCENE_BUILDERS:
        raise RuntimeError(f"missing scene {_ex.id}")
    if SCENE_BUILDERS[_ex.id] is not _ex.scene:
        raise RuntimeError(f"mismatch {_ex.id}")


def get_examples() -> list[ExampleSpec]:
    return list(EXAMPLES)


def get_example(example_id: str) -> ExampleSpec | None:
    for ex in EXAMPLES:
        if ex.id == example_id:
            return ex
    return None


__all__ = ["ExampleSpec", "EXAMPLES", "get_examples", "get_example"]
