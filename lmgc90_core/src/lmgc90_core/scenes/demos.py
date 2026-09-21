"""Demo scenes — pure ``Project`` + ``entities`` only (no ``pre``, no engine, no Qt).

Architecture::

    lmgc90_core.scenes  →  Project.add(Material|Model|Avatar|...)
    lmgc90_gui          →  controller.apply_scene(builder)
    lmgc90_engine       →  materialize / depositIn* when needed
"""
from __future__ import annotations

import math

import numpy as np

from ..entities import (
    Avatar,
    ContactLaw,
    DOFOperation,
    ForLoop,
    GranuloConfig,
    Loop,
    Material,
    Model,
    PostProCommand,
    VisibilityRule,
)
from ..population import ParticlePopulation
from ..project import Project
from ..types import (
    AvatarOrigin,
    AvatarType,
    ContactLawType,
    MaterialType,
)
from ._common import (
    cluster,
    cylinder,
    disk,
    ensure_rigid_2d,
    ensure_rigid_3d,
    iqs,
    jonc,
    mesh_rect,
    plan,
    rough_wall,
    see_dd,
    see_dw,
    see_table,
    smooth_wall,
    sphere,
)


def falling_disks(project: Project) -> None:
    """One floor + template disk expanded by a line Loop (no side walls)."""
    ensure_rigid_2d(project)
    # foundation only
    project.add(smooth_wall(
        l=4.0, h=0.1, center=[0.0, -0.5], model="rigid", material="TDURx", color="GRAYx",
    ))
    # template avatar for the loop
    template = project.add(disk(
        r=0.1, center=[-1.35, 1.0], model="rigid", material="TDURx", color="BLUEx",
    ))
    loop = Loop(
        loop_type="line",
        model_avatar_id=template.avatar_id,
        count=10,
        step=0.3,
        offset_x=-1.35,
        offset_y=1.0,
        group_name="disques_chute",
    )
    project.apply_loop(loop, template=template)
    iqs(project, "iqsc0", 0.3)
    see_dw(project, "iqsc0")
    see_dd(project, "iqsc0")


def sphere_stack(project: Project) -> None:
    ensure_rigid_3d(project)
    project.add(plan(
        axe1=1.5, axe2=1.5, axe3=0.05, center=[0.0, 0.0, -0.1],
        model="rigid", material="TDURx", color="GRAYx"))
    for iz in range(4):
        for iy in range(3):
            for ix in range(3):
                project.add(sphere(
                    r=0.08,
                    center=[(ix - 1) * 0.18, (iy - 1) * 0.18, 0.1 + iz * 0.18],
                    model="rigid", material="TDURx", color="BLUEx"))
    iqs(project, "iqsc0", 0.25)
    see_table(
        project,
        cand_body="RBDY3", cand="SPHER", cand_color="BLUEx",
        ant_body="RBDY3", ant="SPHER", ant_color="BLUEx",
        law="iqsc0", alert=0.05,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="SPHER", cand_color="BLUEx",
        ant_body="RBDY3", ant="PLANx", ant_color="GRAYx",
        law="iqsc0", alert=0.05,
    )


def circle_loop(project: Project) -> None:
    ensure_rigid_2d(project)
    project.add(disk(r=0.15, center=[0.0, 0.0], model="rigid", material="TDURx", color="REEDx"))
    template = project.add(disk(
        r=0.08, center=[0.8, 0.0], model="rigid", material="TDURx", color="BLUEx",
    ))
    loop = Loop(
        loop_type="circle",
        model_avatar_id=template.avatar_id,
        count=12,
        radius=0.8,
        group_name="anneau",
    )
    project.apply_loop(loop, template=template)
    iqs(project, "iqsc0", 0.2)
    see_dd(project, "iqsc0")


def hexagon_packing(project: Project) -> None:
    ensure_rigid_2d(project)
    project.add(smooth_wall(l=3.0, h=0.1, center=[0.0, -0.15], model="rigid", material="TDURx", color="GRAYx"))
    r, rows, cols = 0.08, 5, 8
    for j in range(rows):
        for i in range(cols):
            x = -0.9 + i * 2 * r * 1.05 + (r if j % 2 else 0)
            y = 0.1 + j * r * math.sqrt(3)
            project.add(disk(r=r, center=[x, y], model="rigid", material="TDURx", color="BLUEx"))
    iqs(project, "iqsc0", 0.25)
    see_dd(project, "iqsc0")
    see_dw(project, "iqsc0")


def granulo_deposit(project: Project) -> None:
    """Intent de dépôt 500 disques (Box2D 4×4) — exécution via ``controller.deposit``.

    La scène **n'enregistre que** un ``GranuloConfig`` (+ matériau / modèle / lois).
    Le dépôt réel est fait par la couche supérieure :
      - GUI / engine : ``pre.depositInBox2D`` si pylmgc90 disponible
      - sinon core : ``NumpyGranulo`` RSA dense sans chevauchement
    """
    from ..entities import GranuloConfig

    ensure_rigid_2d(project, density=2600.0)
    config = GranuloConfig(
        nb_particles=500,
        radius_min=0.03,
        radius_max=0.08,
        container_type="Box2D",
        container_params={"lx": 4.0, "ly": 4.0},
        material_name="TDURx",
        model_name="rigid",
        avatar_type="rigidDisk",
        color="BLUEx",
        seed=42,
        group_name="depot_box",
        dimension=2,
    )
    project.granulo.append(config)
    project.add(ContactLaw(name="iqsc0", law_type=ContactLawType.IQS_CLB, friction=0.3))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="BLUEx",
        law="iqsc0", alert=0.05,
    )


def masonry_wall(project: Project) -> None:
    ensure_rigid_2d(project)
    project.add(smooth_wall(l=3.0, h=0.1, center=[0.0, -0.1], model="rigid", material="TDURx", color="GRAYx"))
    lx, ly, gap = 0.25, 0.12, 0.01
    ids = []
    for row in range(5):
        cols = 6 if row % 2 == 0 else 5
        x0 = -0.75 if row % 2 == 0 else -0.75 + (lx + gap) / 2
        for col in range(cols):
            av = project.add(jonc(
                axe1=lx / 2, axe2=ly / 2,
                center=[x0 + col * (lx + gap), row * (ly + gap) + 0.1],
                model="rigid", material="TDURx", color="REEDx"))
            ids.append(av.avatar_id)
    iqs(project, "iqsc0", 0.5)
    see_table(
        project,
        cand_body="RBDY2", cand="JONCx", cand_color="REEDx",
        ant_body="RBDY2", ant="JONCx", ant_color="REEDx",
        law="iqsc0", alert=0.02,
    )
    see_table(
        project,
        cand_body="RBDY2", cand="JONCx", cand_color="REEDx",
        ant_body="RBDY2", ant="JONCx", ant_color="GRAYx",
        law="iqsc0", alert=0.02,
    )
    project.group("briques", ids)


def rotating_drum(project: Project) -> None:
    """Tambour rotatif 2D — disque creux (xKSID) + dépôt Drum2D, comme MVC.

    - Tambour : ``rigidDisk`` is_Hollow, r=2.2, translation fixée, ω = 0.5 rad/s
    - Grains : ``GranuloConfig`` Drum2D r=2.0, 200 particules (résolu par controller.deposit)
    - Contacts DISKx/DISKx + DISKx/xKSID
    """
    from ..entities import DOFOperation, GranuloConfig, PostProCommand

    ensure_rigid_2d(project, density=2600.0)

    drum = project.add(disk(
        r=2.2, center=[0.0, 0.0], model="rigid", material="TDURx",
        color="GRAYx", is_hollow=True,
    ))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="avatar",
        target_value=drum.avatar_id,
        parameters={"component": [1, 2], "dofty": "vlocy", "ct": 0.0},
    ))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="avatar",
        target_value=drum.avatar_id,
        parameters={"component": 3, "dofty": "vlocy", "ct": 0.5},
    ))
    project.add(DOFOperation(
        operation_type="translate",
        target_type="avatar",
        target_value=drum.avatar_id,
        parameters={"dx": 0.9*2.2, "dy": 1.0*2.2},
    ))

    project.granulo.append(GranuloConfig(
        nb_particles=200,
        radius_min=0.05,
        radius_max=0.09,
        container_type="Drum2D",
        container_params={"r": 2.0},
        material_name="TDURx",
        model_name="rigid",
        avatar_type="rigidDisk",
        color="BLUEx",
        seed=21,
        group_name="grains_tambour",
        dimension=2,
    ))

    project.add(ContactLaw(name="law01", law_type=ContactLawType.IQS_CLB, friction=0.45))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="BLUEx",
        law="law01", alert=0.05,
    )
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="xKSID", ant_color="GRAYx",
        law="law01", alert=0.05,
    )
    project.add(PostProCommand(name="COORDINATION NUMBER", step=50))


def hopper_discharge(project: Project) -> None:
    """Décharge en trémie — 2 roughWall inclinés + dépôt Box2D (MVC 0.5.7).

    Géométrie dans le repère depositInBox2D [0,lx]×[0,ly], puis parois
    décalées vers le bas (translate groupe) pour placer le V sous le nuage.
    """
    import math
    from ..entities import DOFOperation, GranuloConfig, PostProCommand

    ensure_rigid_2d(project, density=2600.0)

    box_lx, box_ly = 2.0, 1.6
    top_width, bottom_width, height = 1.6, 0.45, 1.2
    half_top, half_bot = top_width / 2.0, bottom_width / 2.0
    thickness = 0.03
    bottom_offset = thickness * 0.75
    x_center = box_lx / 2.0
    left_bottom = [x_center - (half_bot + bottom_offset), 0.0]
    left_top = [x_center - half_top, height]
    right_bottom = [x_center + (half_bot + bottom_offset), 0.0]
    right_top = [x_center + half_top, height]

    def _inclined_wall(bottom, top, color="GRAYx"):
        dx = top[0] - bottom[0]
        dy = top[1] - bottom[1]
        length = math.hypot(dx, dy)
        angle = math.atan2(dy, dx)
        cx = (bottom[0] + top[0]) / 2.0
        cy = (bottom[1] + top[1]) / 2.0
        wall = project.add(rough_wall(
            l=length, r=thickness, center=[cx, cy],
            model="rigid", material="TDURx", color=color, nb_vertex=10,
        ))
        project.add(DOFOperation(
            operation_type="rotate",
            target_type="avatar",
            target_value=wall.avatar_id,
            parameters={
                "description": "axis",
                "center": [cx, cy],
                "alpha": angle,
            },
        ))
        return wall

    w_left = _inclined_wall(left_bottom, left_top)
    w_right = _inclined_wall(right_bottom, right_top)
    hopper_ids = [w_left.avatar_id, w_right.avatar_id]
    project.group("hopper_walls", hopper_ids)

    project.add(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="group",
        target_value="hopper_walls",
        parameters={"component": [1, 2, 3], "dofty": "vlocy"},
    ))
    # shift V below the deposit box (same as old example: dy = -box_lx)
    project.add(DOFOperation(
        operation_type="translate",
        target_type="group",
        target_value="hopper_walls",
        parameters={"dx": 0.0, "dy": -box_lx},
    ))

    project.granulo.append(GranuloConfig(
        nb_particles=180,
        radius_min=0.04,
        radius_max=0.07,
        container_type="Box2D",
        container_params={"lx": box_lx, "ly": box_ly},
        material_name="TDURx",
        model_name="rigid",
        avatar_type="rigidDisk",
        color="BLUEx",
        seed=17,
        group_name="grains_tremie",
        dimension=2,
    ))

    project.add(ContactLaw(name="grain", law_type=ContactLawType.IQS_CLB, friction=0.4))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="BLUEx",
        law="grain", alert=0.05,
    )
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="JONCx", ant_color="GRAYx",
        law="grain", alert=0.05,
    )
    project.add(PostProCommand(name="KINETIC ENERGY", step=20))


def avalanche_slope(project: Project) -> None:
    """Avalanche : dépôt Box2D dans [0,lx]×[0,ly], pente décalée sous le nuage."""
    import math
    from ..entities import DOFOperation, GranuloConfig

    ensure_rigid_2d(project, density=2600.0)
    box_lx, box_ly = 1.5, 1.0
    slope_length = 4.0
    slope_angle = math.radians(25.0)
    slope = project.add(smooth_wall(
        l=slope_length, h=0.1, center=[0.0, 0.0], model="rigid", material="TDURx",
        color="REEDx", nb_polyg=30,
    ))
    project.add(DOFOperation(
        operation_type="rotate", target_type="avatar", target_value=slope.avatar_id,
        parameters={"description": "axis", "center": [0.0, 0.0],
                    "axis": [0.0, 0.0, 1.0], "alpha": slope_angle},
    ))
    # place slope under deposit box centre (lx/2, ~0)
    project.add(DOFOperation(
        operation_type="translate", target_type="avatar", target_value=slope.avatar_id,
        parameters={"dx": box_lx / 2.0, "dy": -0.4},
    ))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof", target_type="avatar",
        target_value=slope.avatar_id,
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    project.granulo.append(GranuloConfig(
        nb_particles=200, radius_min=0.03, radius_max=0.05,
        container_type="Box2D", container_params={"lx": box_lx, "ly": box_ly},
        material_name="TDURx", model_name="rigid", avatar_type="rigidDisk",
        color="BLUEx", seed=7, group_name="grains_avalanche", dimension=2,
    ))
    project.add(ContactLaw(name="law01", law_type=ContactLawType.IQS_CLB, friction=0.35))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="BLUEx",
        law="law01", alert=0.05,
    )
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="JONCx", ant_color="REEDx",
        law="law01", alert=0.05,
    )



def cluster_pile(project: Project) -> None:
    """Empilement de rigidCluster au-dessus d'un **seul sol** fixe (comme MVC).

    Pas de parois latérales : les clusters tombent librement sur le smoothWall.
    """
    from ..entities import DOFOperation

    ensure_rigid_2d(project, density=2400.0)
    floor = project.add(smooth_wall(
        l=3.0, h=0.1, center=[0.0, -0.05], model="rigid", material="TDURx", color="GRAYx"))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="avatar",
        target_value=floor.avatar_id,
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    ids = []
    nb_cols, nb_rows, spacing = 4, 3, 0.4
    for row in range(nb_rows):
        for col in range(nb_cols):
            cx = (col - (nb_cols - 1) / 2.0) * spacing
            cy = row * spacing + 1.5
            cl = project.add(cluster(
                r=0.06, center=[cx, cy], model="rigid", material="TDURx",
                color="BLUEx", nb_disk=3,
            ))
            ids.append(cl.avatar_id)
    project.group("clusters", ids)
    project.add(ContactLaw(name="law01", law_type=ContactLawType.IQS_CLB, friction=0.4))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="BLUEx",
        law="law01", alert=0.05,
    )
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="JONCx", ant_color="GRAYx",
        law="law01", alert=0.05,
    )


def dof_conditions(project: Project) -> None:
    ensure_rigid_2d(project)
    floor = project.add(smooth_wall(
        l=2.0, h=0.1, center=[0.0, 0.0], model="rigid", material="TDURx", color="GRAYx"))
    project.add(disk(r=0.12, center=[0.0, 0.5], model="rigid", material="TDURx", color="BLUEx"))
    iqs(project, "iqsc0", 0.3)
    see_dw(project, "iqsc0")
    project.add(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="avatar",
        target_value=floor.avatar_id,
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))


def disc_brake(project: Project) -> None:
    ensure_rigid_3d(project, density=7800.0)
    project.add(cylinder(
        r=0.15, h=0.02, center=[0.0, 0.0, 0.0], model="rigid", material="TDURx", color="GRAYx"))
    project.add(sphere(r=0.03, center=[0.16, 0.0, 0.0], model="rigid", material="TDURx", color="REEDx"))
    project.add(sphere(r=0.03, center=[-0.16, 0.0, 0.0], model="rigid", material="TDURx", color="REEDx"))
    iqs(project, "iqsc0", 0.5)
    see_table(
        project,
        cand_body="RBDY3", cand="SPHER", cand_color="REEDx",
        ant_body="RBDY3", ant="CYLND", ant_color="GRAYx",
        law="iqsc0", alert=0.02,
    )



def ball_bearing(project: Project) -> None:
    """Roulement à billes type 608 — coupe 2D (comme LMG90_GUI_MVC).

    - Bague ext. : disque creux (is_hollow) fixe
    - Bague int. : disque plein, rotation pilotée
    - 7 billes libres sur le cercle primitif
    """
    from ..entities import DOFOperation

    project.add(Material(name="acier", material_type=MaterialType.RIGID, density=7800.0))
    project.add(Model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))

    outer_race_inner_radius = 0.0095
    inner_race_outer_radius = 0.0050
    ball_radius = (outer_race_inner_radius - inner_race_outer_radius) / 2.0
    pitch_radius = inner_race_outer_radius + ball_radius
    nb_balls = 7
    center = [0.0, 0.0]

    outer = project.add(disk(
        r=outer_race_inner_radius, center=center, model="rigid", material="acier",
        color="GRAYx", is_hollow=True,
    ))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="avatar",
        target_value=outer.avatar_id,
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))

    inner = project.add(disk(
        r=inner_race_outer_radius, center=center, model="rigid", material="acier",
        color="ORANx", is_hollow=False,
    ))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="avatar",
        target_value=inner.avatar_id,
        parameters={"component": [1, 2], "dofty": "vlocy", "ct": 0.0},
    ))
    inner_omega = 300.0 * 2.0 * math.pi / 60.0
    project.add(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="avatar",
        target_value=inner.avatar_id,
        parameters={"component": 3, "dofty": "vlocy", "ct": inner_omega},
    ))

    ball_ids = []
    for k in range(nb_balls):
        angle = 2.0 * math.pi * k / nb_balls
        bx = center[0] + pitch_radius * math.cos(angle)
        by = center[1] + pitch_radius * math.sin(angle)
        b = project.add(disk(
            r=ball_radius, center=[bx, by], model="rigid", material="acier", color="BLUEx",
        ))
        ball_ids.append(b.avatar_id)
    project.group("billes", ball_ids)

    project.add(ContactLaw(name="law01", law_type=ContactLawType.IQS_CLB, friction=0.05))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="ORANx",
        law="law01", alert=0.0005,
    )
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="xKSID", ant_color="GRAYx",
        law="law01", alert=0.0005,
    )



def for_loop_ramp(project: Project) -> None:
    """ForLoop : 12 disques, rayon croissant (expr_radius)."""
    from ..entities import ForLoop

    ensure_rigid_2d(project)
    template = project.add(disk(
        r=0.05, center=[0.0, 0.0], model="rigid", material="TDURx", color="JAUNx",
    ))
    fl = ForLoop(
        var_name="i",
        start=0.0,
        stop=12.0,
        step=1.0,
        model_avatar_id=template.avatar_id,
        expr_x="i * 0.35",
        expr_y="0.0",
        expr_radius="0.05 + i * 0.01",
        group_name="rampe_croissante",
    )
    project.apply_for_loop(fl, template=template)


def dumbbell(project: Project) -> None:
    """Haltère composite (emptyAvatar + contacteurs DISKx / JONCx) + sol."""
    from ..entities import Avatar, DOFOperation
    from ..types import AvatarOrigin, AvatarType
    from ..ids import new_avatar_id

    ensure_rigid_2d(project)
    length, disk_radius = 0.4, 0.06
    half = length / 2.0
    # emptyAvatar with manual contactors (core entity)
    av = Avatar(
        avatar_id=new_avatar_id(),
        avatar_type=AvatarType.EMPTY_AVATAR,
        center=[0.0, 2.0],
        material_name="TDURx",
        model_name="rigid",
        color="VIOLx",
        origin=AvatarOrigin.MANUAL,
        contactors=[
            {"shape": "DISKx", "color": "VIOLx", "params": {"byrd": disk_radius, "shift": [-half, 0.0]}},
            {"shape": "DISKx", "color": "VIOLx", "params": {"byrd": disk_radius, "shift": [half, 0.0]}},
            {"shape": "JONCx", "color": "VIOLx", "params": {"axe1": half, "axe2": 0.015}},
        ],
    )
    project.add(av)
    floor = project.add(smooth_wall(
        l=2.0, h=0.1, center=[0.0, -0.05], model="rigid", material="TDURx", color="GRAYx"))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof", target_type="avatar",
        target_value=floor.avatar_id,
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    project.add(ContactLaw(name="iqsc0", law_type=ContactLawType.IQS_CLB, friction=0.3))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="VIOLx",
        ant_body="RBDY2", ant="JONCx", ant_color="GRAYx",
        law="iqsc0", alert=0.05,
    )


def cohesive_wall(project: Project) -> None:
    """Deux assises de briques (JONCx) + loi IQS_MAC_CZM."""
    ensure_rigid_2d(project, density=1800.0)
    # rename material density via ensure already TDURx — add brick material
    project.add(Material(name="brick", material_type=MaterialType.RIGID, density=1800.0))
    # model rigid already
    lx, ly, nb_cols = 0.25, 0.10, 6
    ids = []
    for row in range(2):
        for col in range(nb_cols):
            cx = col * lx + lx / 2.0
            cy = row * ly + ly / 2.0
            b = project.add(jonc(
                axe1=lx / 2, axe2=ly / 2, center=[cx, cy],
                model="rigid", material="brick", color="ORANx",
            ))
            ids.append(b.avatar_id)
    project.group("assises_collees", ids)
    project.add(ContactLaw(name="czm01", law_type=ContactLawType.IQS_MAC_CZM, properties={"stfr": 1e10, "dyfr": 1e10, "cn": 1e10, "ct": 1e10, "b": 0.0, "w": 50.0}))
    see_table(
        project,
        cand_body="RBDY2", cand="JONCx", cand_color="ORANx",
        ant_body="RBDY2", ant="JONCx", ant_color="ORANx",
        law="czm01", alert=0.01,
    )


def cable_pendulum(project: Project) -> None:
    """Pendule : ancrage fixe + masse (disques) — câble en loi de contact wire si dispo."""
    from ..entities import DOFOperation

    ensure_rigid_2d(project)
    anchor = project.add(disk(
        r=0.02, center=[0.0, 3.0], model="rigid", material="TDURx", color="REEDx"))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof", target_type="avatar",
        target_value=anchor.avatar_id,
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    bob = project.add(disk(
        r=0.08, center=[1.2, 1.5], model="rigid", material="TDURx", color="BLUEx"))
    project.add(ContactLaw(
        name="wire1", law_type=ContactLawType.IQS_CLB, friction=0.0,
    ))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="REEDx",
        law="wire1", alert=0.05,
    )


# Registry used by GUI (metadata only in GUI; callables here)

def couette_shear(project: Project) -> None:
    """Dépôt dans une cellule de Couette (anneau rint–rext)."""
    from ..entities import GranuloConfig

    ensure_rigid_2d(project, density=2600.0)
    project.granulo.append(GranuloConfig(
        nb_particles=250,
        radius_min=0.03,
        radius_max=0.05,
        container_type="Couette2D",
        container_params={"rint": 1.0, "rext": 2.0},
        material_name="TDURx",
        model_name="rigid",
        avatar_type="rigidDisk",
        color="TURQx",
        seed=11,
        group_name="depot_couette",
        dimension=2,
    ))
    project.add(ContactLaw(name="iqsc0", law_type=ContactLawType.IQS_CLB, friction=0.3))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="TURQx",
        ant_body="RBDY2", ant="DISKx", ant_color="TURQx",
        law="iqsc0", alert=0.05,
    )


def biaxial_compression(project: Project) -> None:
    """Compression biaxiale — dépôt [0,lx]×[0,ly], sol et parois calés sur ce cadre."""
    import math
    from ..entities import DOFOperation, GranuloConfig, PostProCommand

    ensure_rigid_2d(project, density=2600.0)
    box_lx, box_ly = 2.0, 1.5
    thickness = 0.04
    floor = project.add(smooth_wall(
        l=box_lx + 0.4, h=0.1, center=[box_lx / 2.0, -0.05],
        model="rigid", material="TDURx", color="GRAYx"))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof", target_type="avatar",
        target_value=floor.avatar_id,
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))

    def _vertical_wall(x):
        h = box_ly + 0.3
        w = project.add(rough_wall(
            l=h, r=thickness, center=[x, h / 2.0],
            model="rigid", material="TDURx", color="GRAYx", nb_vertex=10,
        ))
        project.add(DOFOperation(
            operation_type="rotate", target_type="avatar", target_value=w.avatar_id,
            parameters={"description": "axis", "center": [x, h / 2.0],
                        "axis": [0.0, 0.0, 1.0], "alpha": math.pi / 2.0},
        ))
        return w

    left = _vertical_wall(-thickness)
    right = _vertical_wall(box_lx + thickness)
    project.group("press_walls", [left.avatar_id, right.avatar_id])
    project.add(DOFOperation(
        operation_type="imposeDrivenDof", target_type="group",
        target_value="press_walls",
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    project.granulo.append(GranuloConfig(
        nb_particles=200, radius_min=0.04, radius_max=0.07,
        container_type="Box2D", container_params={"lx": box_lx, "ly": box_ly},
        material_name="TDURx", model_name="rigid", avatar_type="rigidDisk",
        color="BLUEx", seed=9, group_name="grains_biaxial", dimension=2,
    ))
    project.add(ContactLaw(name="iqsc0", law_type=ContactLawType.IQS_CLB, friction=0.35))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="BLUEx",
        law="iqsc0", alert=0.05,
    )
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="JONCx", ant_color="GRAYx",
        law="iqsc0", alert=0.05,
    )
    project.add(PostProCommand(name="COORDINATION NUMBER", step=20))


def l_shaped_wall(project: Project) -> None:
    """Structure en L — ``brick2D`` / emptyAvatar (comme MVC), pas JONCx.

    Core : Avatar EMPTY_AVATAR + wall_params ``{l, h, brick_name}`` + contactor POLYG.
    Engine : ``pre.brick2D(...).rigidBrick(...)`` à la materialisation.
    """
    from ..entities import DOFOperation, GranuloConfig

    ensure_rigid_2d(project, density=2600.0)
    project.add(Material(name="brick", material_type=MaterialType.RIGID, density=1800.0))
    lx, ly = 0.25, 0.10

    def _brick(cx, cy, color="ORANx") -> Avatar:
        return project.add(Avatar(
            avatar_type=AvatarType.EMPTY_AVATAR,
            center=[cx, cy],
            material_name="brick",
            model_name="rigid",
            color=color,
            origin=AvatarOrigin.MANUAL,
            wall_params={"l": lx, "h": ly, "brick_name": "std"},
            contactors=[{"shape": "POLYG", "color": color}],
        ))

    ids = []
    # horizontal arm 6 cols x 2 rows
    for row in range(2):
        for col in range(6):
            ids.append(_brick(col * lx + lx / 2.0, row * ly + ly / 2.0).avatar_id)
    # vertical arm 2 cols x 6 rows (corner overlap intentional)
    for row in range(6):
        for col in range(2):
            ids.append(_brick(col * lx + lx / 2.0, row * ly + ly / 2.0).avatar_id)
    project.group("mur_L", ids)
    project.add(DOFOperation(
        operation_type="imposeDrivenDof", target_type="group",
        target_value="mur_L",
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    project.add(DOFOperation(
        operation_type="translate", target_type="group",
        target_value="mur_L",
        parameters={"dx": -2 * lx, "dy": -lx},
    ))

    project.granulo.append(GranuloConfig(
        nb_particles=120,
        radius_min=0.03,
        radius_max=0.05,
        container_type="Box2D",
        container_params={"lx": 1.2, "ly": 0.8},
        material_name="TDURx",
        model_name="rigid",
        avatar_type="rigidDisk",
        color="BLUEx",
        seed=5,
        group_name="grains_coin",
        dimension=2,
    ))

    project.add(ContactLaw(
        name="law01",
        law_type=ContactLawType.IQS_DS_CLB,
        friction=0.4,
        properties={"stfr": 1e8, "dyfr": 1e8},
    ))
    project.add(ContactLaw(
        name="law02", law_type=ContactLawType.IQS_CLB, friction=0.4,
    ))
    see_table(
        project,
        cand_body="RBDY2", cand="POLYG", cand_color="ORANx",
        ant_body="RBDY2", ant="POLYG", ant_color="ORANx",
        law="law01", alert=0.02,
    )
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="BLUEx",
        law="law02", alert=0.05,
    )
    see_table(
        project,
        cand_body="RBDY2", cand="POLYG", cand_color="ORANx",
        ant_body="RBDY2", ant="DISKx", ant_color="BLUEx",
        law="law02", alert=0.05,
    )
    
def deformable_drop(project: Project) -> None:
    """Corps déformable (maillage rectangle) tombant sur un sol rigide."""
    from ..entities import DOFOperation

    # ELAS material + FEM model + rigid floor
    project.add(Material(name="ELAS1", material_type=MaterialType.ELAS, density=2700.0, properties={"young": 70e9, "nu": 0.3, "elas": "standard", "anisotropy": "isotropic"}))
    project.add(Material(name="TDURx", material_type=MaterialType.RIGID, density=2500.0))
    project.add(Model(name="femxx", physics="MECAx", element="T3xxx", dimension=2, options={"anisotropy": "iso__", "kinematic": "small", "formulation": "UpdtL", "mass_storage": "lump_", "material": "elas_", "external_model": "no___"}))
    project.add(Model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))

    lx, ly, nx, ny = 1.0, 0.4, 6, 3
    project.add(mesh_rect(
        lx=lx, ly=ly, nx=nx, ny=ny,
        center=[0.0, 2.2],
        model="femxx", material="ELAS1", color="CYANx", mesh_type="2T3",
        contactors=[{"shape": "CLxxx", "color": "CYANx", "group": "down", "params": {}}],
    ))
    floor = project.add(smooth_wall(
        l=3.0, h=0.1, center=[0.0, -0.05], model="rigid", material="TDURx", color="GRAYx"))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof", target_type="avatar",
        target_value=floor.avatar_id,
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    project.add(ContactLaw(name="gapc0", law_type=ContactLawType.GAP_SGR_CLB, friction=0.3))
    see_table(
        project,
        cand_body="MAILx", cand="CLxxx", cand_color="CYANx",
        ant_body="RBDY2", ant="JONCx", ant_color="GRAYx",
        law="gapc0", alert=0.05,
    )


def deformable_impact(project: Project) -> None:
    """Bloc déformable + sol, maillage plus fin + contacteur CLxxx (impact)."""
    from ..entities import DOFOperation

    project.add(Material(name="ELAS1", material_type=MaterialType.ELAS, density=2700.0, properties={"young": 70e9, "nu": 0.3, "elas": "standard", "anisotropy": "isotropic"}))
    project.add(Material(name="TDURx", material_type=MaterialType.RIGID, density=2500.0))
    project.add(Model(name="femxx", physics="MECAx", element="T3xxx", dimension=2, options={"anisotropy": "iso__", "kinematic": "small", "formulation": "UpdtL", "mass_storage": "lump_", "material": "elas_", "external_model": "no___"}))
    project.add(Model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))

    project.add(mesh_rect(
        lx=1.0, ly=0.4, nx=8, ny=4,
        center=[0.0, 2.0],
        model="femxx", material="ELAS1", color="CYANx", mesh_type="2T3",
        contactors=[{"shape": "CLxxx", "color": "CYANx", "group": "down", "params": {}}],
    ))
    floor = project.add(smooth_wall(
        l=3.0, h=0.1, center=[0.0, -0.05], model="rigid", material="TDURx", color="GRAYx"))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof", target_type="avatar",
        target_value=floor.avatar_id,
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    project.add(ContactLaw(name="gapc0", law_type=ContactLawType.GAP_SGR_CLB, friction=0.3))
    see_table(
        project,
        cand_body="MAILx", cand="CLxxx", cand_color="CYANx",
        ant_body="RBDY2", ant="JONCx", ant_color="GRAYx",
        law="gapc0", alert=0.05,
    )


def factory_injection(project: Project) -> None:
    """Conteneur ouvert calé sur dépôt Box2D [0,lx]×[0,ly] + premier batch."""
    from ..entities import DOFOperation, GranuloConfig

    ensure_rigid_2d(project, density=2500.0)
    zone_lx, zone_ly = 1.5, 1.0
    floor = project.add(smooth_wall(
        l=zone_lx + 0.5, h=0.08, center=[zone_lx / 2.0, -0.05],
        model="rigid", material="TDURx", color="GRAYx"))
    left = project.add(smooth_wall(
        l=0.08, h=zone_ly + 0.5, center=[-0.05, zone_ly / 2.0],
        model="rigid", material="TDURx", color="GRAYx"))
    right = project.add(smooth_wall(
        l=0.08, h=zone_ly + 0.5, center=[zone_lx + 0.05, zone_ly / 2.0],
        model="rigid", material="TDURx", color="GRAYx"))
    for w in (floor, left, right):
        project.add(DOFOperation(
            operation_type="imposeDrivenDof", target_type="avatar",
            target_value=w.avatar_id,
            parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
        ))
    project.granulo.append(GranuloConfig(
        nb_particles=40, radius_min=0.04, radius_max=0.06,
        container_type="Box2D", container_params={"lx": zone_lx, "ly": zone_ly},
        material_name="TDURx", model_name="rigid", avatar_type="rigidDisk",
        color="BLUEx", seed=7, group_name="factory_batch0", dimension=2,
    ))
    project.dynamic_vars["factory_injection"] = "{'type':'PERIODIC','nb':200}"
    project.add(ContactLaw(name="iqsc0", law_type=ContactLawType.IQS_CLB, friction=0.3))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="JONCx", ant_color="GRAYx",
        law="iqsc0", alert=0.05,
    )
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="BLUEx",
        law="iqsc0", alert=0.05,
    )



SCENE_BUILDERS = {
    "factory_injection": factory_injection,
    "deformable_impact": deformable_impact,
    "deformable_drop": deformable_drop,
    "l_shaped_wall": l_shaped_wall,
    "biaxial_compression": biaxial_compression,
    "couette_shear": couette_shear,
    "for_loop_ramp": for_loop_ramp,
    "dumbbell": dumbbell,
    "cohesive_wall": cohesive_wall,
    "cable_pendulum": cable_pendulum,
    "ball_bearing": ball_bearing,
    "falling_disks": falling_disks,
    "sphere_stack": sphere_stack,
    "circle_loop": circle_loop,
    "hexagon_packing": hexagon_packing,
    "granulo_deposit": granulo_deposit,
    "masonry_wall": masonry_wall,
    "rotating_drum": rotating_drum,
    "hopper_discharge": hopper_discharge,
    "avalanche_slope": avalanche_slope,
    "cluster_pile": cluster_pile,
    "dof_conditions": dof_conditions,
    "disc_brake": disc_brake,
}
