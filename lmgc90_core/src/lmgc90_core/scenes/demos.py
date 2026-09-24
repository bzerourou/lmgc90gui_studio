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
        name="wire", law_type=ContactLawType.IQS_CLB, friction=0.0,
    ))
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="REEDx",
        law="wire", alert=0.05,
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


def cell_adhesion_v1(project: Project) -> None:
    """Vague 1 — squelette cellule 3D (adhésion LMGC90 / Vassaux, allégé).

    Architecture pure core (entities only) :
      • substrat fixe (grille de sphères SUBST)
      • membrane du noyau (coque sphérique BNOYs)
      • cytosol (sphères CTSLs filtrées hors noyau / dans la cellule)
      • 1 loi IQS_CLB + see-tables minimales
      • groupes : substrate, nucleus, cytosol, cell

    Paramètres volontairement réduits pour le viewer (vague A).
    Vagues suivantes : membrane cellulaire, focals, réseaux, dual DATBOX.
    """
    from ..entities import DOFOperation

    # --- dimensions (µm, proportions cell.py, effectifs réduits) ---
    diam_cell = 30.0
    diam_core = diam_cell / 1.5
    lref = diam_cell / 60.0
    x0 = y0 = z0 = 0.0

    subst_r = 5.0 * lref
    subst_gap = 2.5 * subst_r  # grille un peu plus lâche
    lxsubst = lysubst = 60.0  # allégé vs 200 (vague 1)
    z_subst = -0.75 * diam_cell

    corb_r = lref
    corb_gap = 2.0 * corb_r
    radii_corb = diam_core / 2.0 + corb_r

    ctsl_r_min = 2.0 * lref
    ctsl_r_max = 3.0 * lref
    n_cytosol = 50
    seed = 42

    # --- matériaux / modèle 3D ---
    if not any(m.name == "TDURx" for m in project.materials):
        project.add(Material(
            name="TDURx", material_type=MaterialType.RIGID, density=1.0,
        ))
    if not any(m.name == "CELLx" for m in project.materials):
        project.add(Material(
            name="CELLx", material_type=MaterialType.RIGID, density=1.0e-8,
        ))
    if not any(m.name == "rigid" for m in project.models):
        project.add(Model(
            name="rigid", physics="MECAx", element="Rxx3D", dimension=3,
        ))

    # --- substrat (grille XY, z fixe) ---
    subst_ids: list[str] = []
    npx = max(2, int(lxsubst / subst_gap))
    npy = max(2, int(lysubst / subst_gap))
    for i in range(npx):
        px = -lxsubst / 2.0 + x0 + (i + 0.5) * (lxsubst / npx)
        for j in range(npy):
            py = -lysubst / 2.0 + y0 + (j + 0.5) * (lysubst / npy)
            av = project.add(sphere(
                r=subst_r,
                center=[px, py, z_subst],
                material="TDURx",
                model="rigid",
                color="SUBST",
            ))
            subst_ids.append(av.avatar_id)
            project.add(DOFOperation(
                operation_type="imposeDrivenDof",
                target_type="avatar",
                target_value=av.avatar_id,
                parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
            ))
    project.group("substrate", subst_ids)

    # --- membrane noyau (coque φ–θ, dense réduite pour vague 1 / viewer) ---
    nucleus_ids: list[str] = []
    # ~12×24 ≈ 288 pts max (vs coque "physique" trop lourde)
    nphi = 12
    phi = -math.pi / 2.0
    for _i in range(nphi):
        cos_phi = math.cos(phi)
        ntheta = max(8, int(24 * max(abs(cos_phi), 0.2)))
        theta = 0.0
        for _j in range(ntheta):
            cx = x0 + radii_corb * cos_phi * math.cos(theta)
            cy = y0 + radii_corb * cos_phi * math.sin(theta)
            cz = z0 + radii_corb * math.sin(phi)
            av = project.add(Avatar(
                avatar_type=AvatarType.RIGID_SPHERE,
                center=[cx, cy, cz],
                material_name="CELLx",
                model_name="rigid",
                color="BNOYs",
                origin=AvatarOrigin.MANUAL,
                radius=corb_r,
                contactors=[{"shape": "PT3Dx", "color": "BNOYp"}],
            ))
            nucleus_ids.append(av.avatar_id)
            theta += 2.0 * math.pi / ntheta
        phi += math.pi / nphi
    project.group("nucleus", nucleus_ids)

    # --- cytosol : tirage dans une boîte, filtre hors noyau / dans cellule ---
    rng = np.random.default_rng(seed)
    cytosol_ids: list[str] = []
    r_cell = diam_cell / 2.0
    r_core = diam_core / 2.0
    attempts = 0
    max_attempts = n_cytosol * 40
    while len(cytosol_ids) < n_cytosol and attempts < max_attempts:
        attempts += 1
        r = float(rng.uniform(ctsl_r_min, ctsl_r_max))
        px = float(rng.uniform(x0 - r_cell, x0 + r_cell))
        py = float(rng.uniform(y0 - r_cell, y0 + r_cell))
        pz = float(rng.uniform(z0 - r_cell, z0 + r_cell))
        dist = math.sqrt((px - x0) ** 2 + (py - y0) ** 2 + (pz - z0) ** 2)
        if dist + r >= r_cell:
            continue
        if dist - r <= r_core + corb_r:
            continue
        av = project.add(Avatar(
            avatar_type=AvatarType.RIGID_SPHERE,
            center=[px, py, pz],
            material_name="CELLx",
            model_name="rigid",
            color="CTSLs",
            origin=AvatarOrigin.MANUAL,
            radius=r,
            contactors=[{"shape": "PT3Dx", "color": "CTSLp"}],
        ))
        cytosol_ids.append(av.avatar_id)
    project.group("cytosol", cytosol_ids)
    project.group("cell", nucleus_ids + cytosol_ids)

    # --- contact minimal ---
    project.add(ContactLaw(
        name="ictn0", law_type=ContactLawType.IQS_CLB, friction=0.07,
    ))
    alert_core = max(corb_r, ctsl_r_max)
    see_table(
        project,
        cand_body="RBDY3", cand="SPHER", cand_color="CTSLs",
        ant_body="RBDY3", ant="SPHER", ant_color="CTSLs",
        law="ictn0", alert=ctsl_r_max,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="SPHER", cand_color="CTSLs",
        ant_body="RBDY3", ant="SPHER", ant_color="BNOYs",
        law="ictn0", alert=alert_core,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="SPHER", cand_color="BNOYs",
        ant_body="RBDY3", ant="SPHER", ant_color="BNOYs",
        law="ictn0", alert=corb_r,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="SPHER", cand_color="CTSLs",
        ant_body="RBDY3", ant="SPHER", ant_color="SUBST",
        law="ictn0", alert=ctsl_r_max,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="SPHER", cand_color="BNOYs",
        ant_body="RBDY3", ant="SPHER", ant_color="SUBST",
        law="ictn0", alert=0.1 * corb_r,
    )

    project.dynamic_vars["cell_adhesion"] = (
        f"{{'wave':1,'diam_cell':{diam_cell},'diam_core':{diam_core},"
        f"'n_substrat':{len(subst_ids)},'n_nucleus':{len(nucleus_ids)},"
        f"'n_cytosol':{len(cytosol_ids)}}}"
    )



def cell_adhesion_v2(project: Project) -> None:
    """Vague 2 — cellule 3D : vague 1 + membrane cellulaire + focals.

    Ajouts (inspiré cell.py / Vassaux, densités réduites) :
      • membrane cellulaire = 2 calottes sphériques (BCELs / BCELp / BCELt)
      • ~24 adhesions focales (INTEs) positionnées ventrale + DOF fixés (simplifié)
      • groupes membrane, focals
      • see-tables membrane ↔ cytosol / noyau / substrat

    Pas encore : réseaux MF/MT/IF, ELASTIC_WIRE, dual DATBOX, DOF predefined.
    """
    from ..entities import DOFOperation

    diam_cell = 30.0
    diam_core = diam_cell / 1.5
    lref = diam_cell / 60.0
    x0 = y0 = z0 = 0.0

    # substrate
    subst_r = 5.0 * lref
    subst_gap = 2.5 * subst_r
    lxsubst = lysubst = 60.0
    z_subst = -0.75 * diam_cell

    # nucleus shell
    corb_r = lref
    radii_corb = diam_core / 2.0 + corb_r

    # cell membrane (two large spheres whose intersection ≈ cell)
    diam_cm = 2.5 * diam_cell
    radii_cm = diam_cm / 2.0 + 3.0 * lref
    celb_r = 3.0 * lref
    z_cm1 = +(diam_cm / 2.0 - 0.75 * diam_cell / 2.0)
    z_cm2 = -(diam_cm / 2.0 - 0.75 * diam_cell / 2.0)

    # cytosol
    ctsl_r_min = 2.0 * lref
    ctsl_r_max = 3.0 * lref
    n_cytosol = 50
    seed = 42

    # focals
    nb_focals = 24
    nb_focals_ptour = 8
    shift_amp = 2.5
    radii_celb = diam_cell / 2.0 + celb_r

    # --- materials / model ---
    if not any(m.name == "TDURx" for m in project.materials):
        project.add(Material(name="TDURx", material_type=MaterialType.RIGID, density=1.0))
    if not any(m.name == "CELLx" for m in project.materials):
        project.add(Material(name="CELLx", material_type=MaterialType.RIGID, density=1.0e-8))
    if not any(m.name == "rigid" for m in project.models):
        project.add(Model(name="rigid", physics="MECAx", element="Rxx3D", dimension=3))

    # --- substrate ---
    subst_ids: list[str] = []
    npx = max(2, int(lxsubst / subst_gap))
    npy = max(2, int(lysubst / subst_gap))
    for i in range(npx):
        px = -lxsubst / 2.0 + x0 + (i + 0.5) * (lxsubst / npx)
        for j in range(npy):
            py = -lysubst / 2.0 + y0 + (j + 0.5) * (lysubst / npy)
            av = project.add(sphere(
                r=subst_r, center=[px, py, z_subst],
                material="TDURx", model="rigid", color="SUBST",
            ))
            subst_ids.append(av.avatar_id)
            project.add(DOFOperation(
                operation_type="imposeDrivenDof", target_type="avatar",
                target_value=av.avatar_id,
                parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
            ))
    project.group("substrate", subst_ids)

    # --- nucleus membrane (coarse shell) ---
    nucleus_ids: list[str] = []
    nphi = 12
    phi = -math.pi / 2.0
    for _i in range(nphi):
        cos_phi = math.cos(phi)
        ntheta = max(8, int(24 * max(abs(cos_phi), 0.2)))
        theta = 0.0
        for _j in range(ntheta):
            cx = x0 + radii_corb * cos_phi * math.cos(theta)
            cy = y0 + radii_corb * cos_phi * math.sin(theta)
            cz = z0 + radii_corb * math.sin(phi)
            av = project.add(Avatar(
                avatar_type=AvatarType.RIGID_SPHERE,
                center=[cx, cy, cz],
                material_name="CELLx", model_name="rigid", color="BNOYs",
                origin=AvatarOrigin.MANUAL, radius=corb_r,
                contactors=[{"shape": "PT3Dx", "color": "BNOYp"}],
            ))
            nucleus_ids.append(av.avatar_id)
            theta += 2.0 * math.pi / ntheta
        phi += math.pi / nphi
    project.group("nucleus", nucleus_ids)

    # --- cell membrane: lower half of cm1 + upper half of cm2 ---
    membrane_ids: list[str] = []
    nphi_m = 10

    def _membrane_shell(z_ctr: float, keep_below: bool) -> None:
        phi_m = -math.pi / 2.0
        for _i in range(nphi_m):
            cos_phi = math.cos(phi_m)
            ntheta = max(8, int(20 * max(abs(cos_phi), 0.2)))
            theta = 0.0
            for _j in range(ntheta):
                cz = z_ctr + radii_cm * math.sin(phi_m)
                if keep_below and cz >= z0:
                    theta += 2.0 * math.pi / ntheta
                    continue
                if (not keep_below) and cz <= z0:
                    theta += 2.0 * math.pi / ntheta
                    continue
                cx = x0 + radii_cm * cos_phi * math.cos(theta)
                cy = y0 + radii_cm * cos_phi * math.sin(theta)
                av = project.add(Avatar(
                    avatar_type=AvatarType.RIGID_SPHERE,
                    center=[cx, cy, cz],
                    material_name="CELLx", model_name="rigid", color="BCELs",
                    origin=AvatarOrigin.MANUAL, radius=celb_r,
                    contactors=[
                        {"shape": "PT3Dx", "color": "BCELp"},
                        {"shape": "SPHER", "color": "BCELt", "byrd": celb_r / 10.0},
                    ],
                ))
                membrane_ids.append(av.avatar_id)
                theta += 2.0 * math.pi / ntheta
            phi_m += math.pi / nphi_m

    _membrane_shell(z_cm1, keep_below=True)   # lower part of upper centre
    _membrane_shell(z_cm2, keep_below=False)  # upper part of lower centre
    project.group("membrane", membrane_ids)

    # --- cytosol filtered ---
    rng = np.random.default_rng(seed)
    cytosol_ids: list[str] = []
    r_cell = diam_cell / 2.0
    r_core = diam_core / 2.0
    attempts = 0
    while len(cytosol_ids) < n_cytosol and attempts < n_cytosol * 50:
        attempts += 1
        r = float(rng.uniform(ctsl_r_min, ctsl_r_max))
        px = float(rng.uniform(x0 - r_cell, x0 + r_cell))
        py = float(rng.uniform(y0 - r_cell, y0 + r_cell))
        pz = float(rng.uniform(z0 - r_cell, z0 + r_cell))
        dist = math.sqrt((px - x0) ** 2 + (py - y0) ** 2 + (pz - z0) ** 2)
        d1 = math.sqrt((px - x0) ** 2 + (py - y0) ** 2 + (pz - z_cm1) ** 2)
        d2 = math.sqrt((px - x0) ** 2 + (py - y0) ** 2 + (pz - z_cm2) ** 2)
        if dist - r <= r_core + corb_r:
            continue
        if d1 + r >= diam_cm / 2.0 or d2 + r >= diam_cm / 2.0:
            continue
        if dist + r >= r_cell * 1.15:
            continue
        av = project.add(Avatar(
            avatar_type=AvatarType.RIGID_SPHERE,
            center=[px, py, pz],
            material_name="CELLx", model_name="rigid", color="CTSLs",
            origin=AvatarOrigin.MANUAL, radius=r,
            contactors=[{"shape": "PT3Dx", "color": "CTSLp"}],
        ))
        cytosol_ids.append(av.avatar_id)
    project.group("cytosol", cytosol_ids)

    # --- focal adhesions (ventral ring → mapped on lower membrane) ---
    focal_ids: list[str] = []
    for i in range(nb_focals):
        nb_tours = max(1, nb_focals // nb_focals_ptour)
        rad = radii_celb - int(i / nb_focals_ptour) * (radii_celb / nb_tours)
        theta = 2.0 * i * math.pi / nb_focals_ptour
        # protein target on substrate plane (binding site)
        px_p = x0 + shift_amp * rad * math.cos(theta)
        py_p = y0 + shift_amp * rad * math.sin(theta)
        # focal on lower membrane (approx projection)
        dist_xy = math.sqrt(px_p ** 2 + py_p ** 2) + 1e-12
        ang = (math.pi / 4.0) * min(1.0, dist_xy / (shift_amp * radii_celb + 1e-12))
        proj = radii_cm * math.sin(ang)
        fx = (proj / dist_xy) * px_p
        fy = (proj / dist_xy) * py_p
        fz = -radii_cm * math.cos(ang) + z_cm1
        name = f"I{i:04d}"
        av = project.add(Avatar(
            avatar_type=AvatarType.RIGID_SPHERE,
            center=[fx, fy, fz],
            material_name="CELLx", model_name="rigid", color="INTEs",
            origin=AvatarOrigin.MANUAL, radius=celb_r,
            contactors=[{"shape": "PT3Dx", "color": name}],
        ))
        focal_ids.append(av.avatar_id)
        # vague 2: fixed focals (predefined spreading → vague 4)
        project.add(DOFOperation(
            operation_type="imposeDrivenDof", target_type="avatar",
            target_value=av.avatar_id,
            parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
        ))
    project.group("focals", focal_ids)
    project.group("cell", nucleus_ids + membrane_ids + cytosol_ids + focal_ids)

    # --- contacts ---
    project.add(ContactLaw(
        name="ictn0", law_type=ContactLawType.IQS_CLB, friction=0.07,
    ))
    pairs = [
        ("CTSLs", "CTSLs", ctsl_r_max),
        ("CTSLs", "BNOYs", max(corb_r, ctsl_r_max)),
        ("BNOYs", "BNOYs", corb_r),
        ("CTSLs", "SUBST", ctsl_r_max),
        ("BNOYs", "SUBST", 0.1 * corb_r),
        ("BCELs", "BCELs", celb_r / 10.0),
        ("BCELs", "BNOYs", max(corb_r, celb_r)),
        ("BCELs", "CTSLs", ctsl_r_max),
        ("BCELs", "SUBST", 0.1 * celb_r),
        ("BCELt", "BCELt", celb_r / 10.0),
        ("INTEs", "SUBST", 0.1 * celb_r),
        ("INTEs", "BCELs", celb_r),
    ]
    for c1, c2, alert in pairs:
        see_table(
            project,
            cand_body="RBDY3", cand="SPHER", cand_color=c1,
            ant_body="RBDY3", ant="SPHER", ant_color=c2,
            law="ictn0", alert=float(alert),
        )

    project.dynamic_vars["cell_adhesion"] = (
        f"{{'wave':2,'diam_cell':{diam_cell},'n_substrat':{len(subst_ids)},"
        f"'n_nucleus':{len(nucleus_ids)},'n_membrane':{len(membrane_ids)},"
        f"'n_cytosol':{len(cytosol_ids)},'n_focals':{len(focal_ids)}}}"
    )



def cell_adhesion_v3(project: Project) -> None:
    """Vague 3 — cellule + réseaux cytosquelette (MF / MT / IF).

    Ajouts vs vague 2 :
      • microfilaments (MFsxx / MFpxx) — distribution radiale aléatoire
      • microtubules (MTsxx / MTpxx) — orientation préférentielle
      • filaments intermédiaires (IFsxx / IFpxx)
      • lois ``ELASTIC_WIRE`` / ``ELASTIC_ROD`` + see-tables PT3Dx
      • densités réduites (viewer) ; dual DATBOX / DOF predefined → vagues 4–5

    Core pur (entities only).
    """
    from ..entities import DOFOperation

    diam_cell = 30.0
    diam_core = diam_cell / 1.5
    lref = diam_cell / 60.0
    x0 = y0 = z0 = 0.0

    subst_r = 5.0 * lref
    subst_gap = 2.5 * subst_r
    lxsubst = lysubst = 60.0
    z_subst = -0.75 * diam_cell

    corb_r = lref
    radii_corb = diam_core / 2.0 + corb_r

    diam_cm = 2.5 * diam_cell
    radii_cm = diam_cm / 2.0 + 3.0 * lref
    celb_r = 3.0 * lref
    z_cm1 = +(diam_cm / 2.0 - 0.75 * diam_cell / 2.0)
    z_cm2 = -(diam_cm / 2.0 - 0.75 * diam_cell / 2.0)

    ctsl_r_min, ctsl_r_max = 2.0 * lref, 3.0 * lref
    n_cytosol = 40
    seed = 42

    nb_focals, nb_focals_ptour = 20, 8
    shift_amp = 2.5
    radii_celb = diam_cell / 2.0 + celb_r

    # networks (allégés vs cell.py 400/400/200)
    nb_mf, nb_mt, nb_if = 50, 50, 30
    r_net = 1.0 * lref
    alert_intra = 4.0 * r_net
    alert_extra = 2.0 * r_net
    stiff = 0.20  # phase "stabilisation" (cell.py i==1)

    # --- materials / model ---
    if not any(m.name == "TDURx" for m in project.materials):
        project.add(Material(name="TDURx", material_type=MaterialType.RIGID, density=1.0))
    if not any(m.name == "CELLx" for m in project.materials):
        project.add(Material(name="CELLx", material_type=MaterialType.RIGID, density=1.0e-8))
    if not any(m.name == "rigid" for m in project.models):
        project.add(Model(name="rigid", physics="MECAx", element="Rxx3D", dimension=3))

    def _fix(aid: str) -> None:
        project.add(DOFOperation(
            operation_type="imposeDrivenDof", target_type="avatar",
            target_value=aid,
            parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
        ))

    def _inside_cytoplasm(px, py, pz, r) -> bool:
        dist = math.sqrt((px - x0) ** 2 + (py - y0) ** 2 + (pz - z0) ** 2)
        d1 = math.sqrt((px - x0) ** 2 + (py - y0) ** 2 + (pz - z_cm1) ** 2)
        d2 = math.sqrt((px - x0) ** 2 + (py - y0) ** 2 + (pz - z_cm2) ** 2)
        if dist - r <= diam_core / 2.0 + corb_r:
            return False
        if d1 + r >= diam_cm / 2.0 or d2 + r >= diam_cm / 2.0:
            return False
        return True

    # --- substrate ---
    subst_ids: list[str] = []
    npx = max(2, int(lxsubst / subst_gap))
    npy = max(2, int(lysubst / subst_gap))
    for i in range(npx):
        px = -lxsubst / 2.0 + x0 + (i + 0.5) * (lxsubst / npx)
        for j in range(npy):
            py = -lysubst / 2.0 + y0 + (j + 0.5) * (lysubst / npy)
            av = project.add(sphere(
                r=subst_r, center=[px, py, z_subst],
                material="TDURx", model="rigid", color="SUBST",
            ))
            subst_ids.append(av.avatar_id)
            _fix(av.avatar_id)
    project.group("substrate", subst_ids)

    # --- nucleus ---
    nucleus_ids: list[str] = []
    nphi = 12
    phi = -math.pi / 2.0
    for _i in range(nphi):
        cos_phi = math.cos(phi)
        ntheta = max(8, int(24 * max(abs(cos_phi), 0.2)))
        theta = 0.0
        for _j in range(ntheta):
            cx = x0 + radii_corb * cos_phi * math.cos(theta)
            cy = y0 + radii_corb * cos_phi * math.sin(theta)
            cz = z0 + radii_corb * math.sin(phi)
            av = project.add(Avatar(
                avatar_type=AvatarType.RIGID_SPHERE,
                center=[cx, cy, cz],
                material_name="CELLx", model_name="rigid", color="BNOYs",
                origin=AvatarOrigin.MANUAL, radius=corb_r,
                contactors=[{"shape": "PT3Dx", "color": "BNOYp"}],
            ))
            nucleus_ids.append(av.avatar_id)
            theta += 2.0 * math.pi / ntheta
        phi += math.pi / nphi
    project.group("nucleus", nucleus_ids)

    # --- membrane ---
    membrane_ids: list[str] = []
    nphi_m = 10

    def _membrane_shell(z_ctr: float, keep_below: bool) -> None:
        phi_m = -math.pi / 2.0
        for _i in range(nphi_m):
            cos_phi = math.cos(phi_m)
            ntheta = max(8, int(20 * max(abs(cos_phi), 0.2)))
            theta = 0.0
            for _j in range(ntheta):
                cz = z_ctr + radii_cm * math.sin(phi_m)
                skip = (keep_below and cz >= z0) or ((not keep_below) and cz <= z0)
                if not skip:
                    cx = x0 + radii_cm * cos_phi * math.cos(theta)
                    cy = y0 + radii_cm * cos_phi * math.sin(theta)
                    av = project.add(Avatar(
                        avatar_type=AvatarType.RIGID_SPHERE,
                        center=[cx, cy, cz],
                        material_name="CELLx", model_name="rigid", color="BCELs",
                        origin=AvatarOrigin.MANUAL, radius=celb_r,
                        contactors=[
                            {"shape": "PT3Dx", "color": "BCELp"},
                            {"shape": "SPHER", "color": "BCELt", "byrd": celb_r / 10.0},
                        ],
                    ))
                    membrane_ids.append(av.avatar_id)
                theta += 2.0 * math.pi / ntheta
            phi_m += math.pi / nphi_m

    _membrane_shell(z_cm1, True)
    _membrane_shell(z_cm2, False)
    project.group("membrane", membrane_ids)

    # --- cytosol ---
    rng = np.random.default_rng(seed)
    cytosol_ids: list[str] = []
    attempts = 0
    while len(cytosol_ids) < n_cytosol and attempts < n_cytosol * 50:
        attempts += 1
        r = float(rng.uniform(ctsl_r_min, ctsl_r_max))
        px = float(rng.uniform(x0 - diam_cell / 2, x0 + diam_cell / 2))
        py = float(rng.uniform(y0 - diam_cell / 2, y0 + diam_cell / 2))
        pz = float(rng.uniform(z0 - diam_cell / 2, z0 + diam_cell / 2))
        if not _inside_cytoplasm(px, py, pz, r):
            continue
        av = project.add(Avatar(
            avatar_type=AvatarType.RIGID_SPHERE,
            center=[px, py, pz],
            material_name="CELLx", model_name="rigid", color="CTSLs",
            origin=AvatarOrigin.MANUAL, radius=r,
            contactors=[{"shape": "PT3Dx", "color": "CTSLp"}],
        ))
        cytosol_ids.append(av.avatar_id)
    project.group("cytosol", cytosol_ids)

    # --- focals ---
    focal_ids: list[str] = []
    for i in range(nb_focals):
        nb_tours = max(1, nb_focals // nb_focals_ptour)
        rad = radii_celb - int(i / nb_focals_ptour) * (radii_celb / nb_tours)
        theta = 2.0 * i * math.pi / nb_focals_ptour
        px_p = x0 + shift_amp * rad * math.cos(theta)
        py_p = y0 + shift_amp * rad * math.sin(theta)
        dist_xy = math.sqrt(px_p ** 2 + py_p ** 2) + 1e-12
        ang = (math.pi / 4.0) * min(1.0, dist_xy / (shift_amp * radii_celb + 1e-12))
        proj = radii_cm * math.sin(ang)
        fx = (proj / dist_xy) * px_p
        fy = (proj / dist_xy) * py_p
        fz = -radii_cm * math.cos(ang) + z_cm1
        av = project.add(Avatar(
            avatar_type=AvatarType.RIGID_SPHERE,
            center=[fx, fy, fz],
            material_name="CELLx", model_name="rigid", color="INTEs",
            origin=AvatarOrigin.MANUAL, radius=celb_r,
            contactors=[{"shape": "PT3Dx", "color": f"I{i:04d}"}],
        ))
        focal_ids.append(av.avatar_id)
        _fix(av.avatar_id)
    project.group("focals", focal_ids)

    # --- networks ---
    def _place_network(n: int, color_s: str, color_p: str, preferential: bool) -> list[str]:
        ids: list[str] = []
        dir_phi = float(rng.uniform(0.0, 2.0 * math.pi))
        dir_theta = float(rng.uniform(-math.pi / 2.0, math.pi / 2.0))
        tries = 0
        while len(ids) < n and tries < n * 80:
            tries += 1
            rad = float(rng.uniform(
                diam_core / 2.0 + 2.0 * corb_r + r_net,
                max(diam_cm, diam_cm) / 2.0 - r_net,
            ))
            if preferential:
                theta = float(rng.normal(dir_theta, math.pi / 2.0))
                phi_n = float(rng.normal(dir_phi, math.pi / 2.0))
            else:
                theta = float(rng.uniform(0.0, 2.0 * math.pi))
                phi_n = float(rng.uniform(-math.pi / 2.0, math.pi / 2.0))
            px = x0 + rad * math.cos(phi_n) * math.cos(theta)
            py = y0 + rad * math.cos(phi_n) * math.sin(theta)
            pz = z0 + rad * math.sin(phi_n)
            if not _inside_cytoplasm(px, py, pz, r_net):
                continue
            av = project.add(Avatar(
                avatar_type=AvatarType.RIGID_SPHERE,
                center=[px, py, pz],
                material_name="CELLx", model_name="rigid", color=color_s,
                origin=AvatarOrigin.MANUAL, radius=r_net,
                contactors=[{"shape": "PT3Dx", "color": color_p}],
            ))
            ids.append(av.avatar_id)
        return ids

    mf_ids = _place_network(nb_mf, "MFsxx", "MFpxx", preferential=False)
    mt_ids = _place_network(nb_mt, "MTsxx", "MTpxx", preferential=True)
    if_ids = _place_network(nb_if, "IFsxx", "IFpxx", preferential=False)
    project.group("microfilaments", mf_ids)
    project.group("microtubules", mt_ids)
    project.group("interm_filaments", if_ids)
    project.group(
        "cell",
        nucleus_ids + membrane_ids + cytosol_ids + focal_ids + mf_ids + mt_ids + if_ids,
    )

    # --- laws: contact + elastic networks (phase stabilisation) ---
    project.add(ContactLaw(
        name="ictn0", law_type=ContactLawType.IQS_CLB, friction=0.07,
    ))
    project.add(ContactLaw(
        name="ismt0", law_type=ContactLawType.ELASTIC_ROD,
        properties={"stiffness": 22.8e0 * stiff, "prestrain": 0.0},
    ))
    project.add(ContactLaw(
        name="icif0", law_type=ContactLawType.ELASTIC_WIRE,
        properties={"stiffness": 15.7e0 * stiff, "prestrain": 0.10},
    ))
    project.add(ContactLaw(
        name="icmf0", law_type=ContactLawType.ELASTIC_WIRE,
        properties={"stiffness": 1.00e0 * stiff, "prestrain": -0.04},
    ))
    project.add(ContactLaw(
        name="icnm0", law_type=ContactLawType.ELASTIC_ROD,
        properties={"stiffness": 1.00e0 * stiff, "prestrain": 0.0},
    ))
    project.add(ContactLaw(
        name="iccm0", law_type=ContactLawType.ELASTIC_ROD,
        properties={"stiffness": 5.00e0 * stiff, "prestrain": -0.04},
    ))
    project.add(ContactLaw(
        name="icfa0", law_type=ContactLawType.ELASTIC_WIRE,
        properties={"stiffness": 10.0e0 * stiff, "prestrain": 0.0},
    ))
    project.add(ContactLaw(
        name="icci0", law_type=ContactLawType.ELASTIC_WIRE,
        properties={"stiffness": 100.0e0 * stiff, "prestrain": 0.0},
    ))

    # sphere contacts
    for c1, c2, alert in [
        ("CTSLs", "CTSLs", ctsl_r_max),
        ("CTSLs", "BNOYs", max(corb_r, ctsl_r_max)),
        ("BNOYs", "BNOYs", corb_r),
        ("CTSLs", "SUBST", ctsl_r_max),
        ("BNOYs", "SUBST", 0.1 * corb_r),
        ("BCELs", "BCELs", celb_r / 10.0),
        ("BCELs", "BNOYs", max(corb_r, celb_r)),
        ("BCELs", "CTSLs", ctsl_r_max),
        ("BCELs", "SUBST", 0.1 * celb_r),
        ("BCELs", "MFsxx", celb_r),
        ("BCELs", "MTsxx", celb_r),
        ("BCELs", "IFsxx", celb_r),
        ("BNOYs", "MFsxx", corb_r),
        ("BNOYs", "MTsxx", corb_r),
        ("BNOYs", "IFsxx", corb_r),
        ("INTEs", "SUBST", 0.1 * celb_r),
        ("INTEs", "BCELs", celb_r),
    ]:
        see_table(
            project,
            cand_body="RBDY3", cand="SPHER", cand_color=c1,
            ant_body="RBDY3", ant="SPHER", ant_color=c2,
            law="ictn0", alert=float(alert),
        )

    # PT3Dx elastic networks (intra)
    see_table(
        project,
        cand_body="RBDY3", cand="PT3Dx", cand_color="MTpxx",
        ant_body="RBDY3", ant="PT3Dx", ant_color="MTpxx",
        law="ismt0", alert=alert_intra,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="PT3Dx", cand_color="IFpxx",
        ant_body="RBDY3", ant="PT3Dx", ant_color="IFpxx",
        law="icif0", alert=alert_intra,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="PT3Dx", cand_color="MFpxx",
        ant_body="RBDY3", ant="PT3Dx", ant_color="MFpxx",
        law="icmf0", alert=alert_intra,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="PT3Dx", cand_color="BNOYp",
        ant_body="RBDY3", ant="PT3Dx", ant_color="BNOYp",
        law="icnm0", alert=2.0 * 2.0 * corb_r,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="PT3Dx", cand_color="BCELp",
        ant_body="RBDY3", ant="PT3Dx", ant_color="BCELp",
        law="iccm0", alert=2.0 * 2.0 * celb_r,
    )
    # cross-network
    see_table(
        project,
        cand_body="RBDY3", cand="PT3Dx", cand_color="MTpxx",
        ant_body="RBDY3", ant="PT3Dx", ant_color="MFpxx",
        law="icci0", alert=alert_extra,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="PT3Dx", cand_color="MFpxx",
        ant_body="RBDY3", ant="PT3Dx", ant_color="BNOYp",
        law="icci0", alert=alert_extra,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="PT3Dx", cand_color="MFpxx",
        ant_body="RBDY3", ant="PT3Dx", ant_color="BCELp",
        law="icci0", alert=alert_extra,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="PT3Dx", cand_color="IFpxx",
        ant_body="RBDY3", ant="PT3Dx", ant_color="BNOYp",
        law="icci0", alert=alert_extra,
    )
    # focals ↔ membrane (generic color; per-focal tables → later)
    see_table(
        project,
        cand_body="RBDY3", cand="PT3Dx", cand_color="BCELp",
        ant_body="RBDY3", ant="PT3Dx", ant_color="I0000",
        law="icfa0", alert=5.0 * 2.0 * celb_r,
    )

    project.dynamic_vars["cell_adhesion"] = (
        f"{{'wave':3,'diam_cell':{diam_cell},"
        f"'n_mf':{len(mf_ids)},'n_mt':{len(mt_ids)},'n_if':{len(if_ids)},"
        f"'n_total':{len(project.avatars)},'stiff_scale':{stiff}}}"
    )



def cell_adhesion_v4(project: Project) -> None:
    """Vague 4 — dual phase SPRD/STBL + DOF predefined focals.

    • Reprend la géométrie vague 3 (membrane, réseaux, focals)
    • Focals : ``imposeDrivenDof`` *predefined* vers sites substrat
      (ct = Δx/Δt_phase, rampi horizontal/vertical) — comme cell.py
    • Lois actives = phase **stabilisation** ; paramètres phase **spreading**
      stockés dans ``dynamic_vars['cell_phases']`` pour export dual DATBOX
    • Post-pro : KINETIC ENERGY, SOLVER INFORMATIONS, tracking (métadonnée groupes)

    Export dual réel DATBOX_SPRD / DATBOX_STBL → engine (vague 4b / 5).
    """
    from ..entities import DOFOperation, PostProCommand

    # --- timing (defaults ; overridable via dynamic_vars before run) ---
    nsteps_sprd, dt_sprd = 500, 1.0e-4
    nsteps_stbl, dt_stbl = 1000, 1.0e-4
    noutp = 20
    charinc_sprd = 1.0 / (nsteps_sprd * dt_sprd)

    diam_cell = 30.0
    diam_core = diam_cell / 1.5
    lref = diam_cell / 60.0
    x0 = y0 = z0 = 0.0

    subst_r = 5.0 * lref
    subst_gap = 2.5 * subst_r
    lxsubst = lysubst = 60.0
    z_subst = -0.75 * diam_cell

    corb_r = lref
    radii_corb = diam_core / 2.0 + corb_r
    diam_cm = 2.5 * diam_cell
    radii_cm = diam_cm / 2.0 + 3.0 * lref
    celb_r = 3.0 * lref
    z_cm1 = +(diam_cm / 2.0 - 0.75 * diam_cell / 2.0)
    z_cm2 = -(diam_cm / 2.0 - 0.75 * diam_cell / 2.0)

    ctsl_r_min, ctsl_r_max = 2.0 * lref, 3.0 * lref
    n_cytosol = 40
    seed = 42
    nb_focals, nb_focals_ptour = 20, 8
    shift_amp = 2.5
    radii_celb = diam_cell / 2.0 + celb_r

    nb_mf, nb_mt, nb_if = 50, 50, 30
    r_net = 1.0 * lref
    alert_intra = 4.0 * r_net
    alert_extra = 2.0 * r_net
    # stabilisation (active in project)
    stiff = 0.20
    pstr = 2.00

    if not any(m.name == "TDURx" for m in project.materials):
        project.add(Material(name="TDURx", material_type=MaterialType.RIGID, density=1.0))
    if not any(m.name == "CELLx" for m in project.materials):
        project.add(Material(name="CELLx", material_type=MaterialType.RIGID, density=1.0e-8))
    if not any(m.name == "rigid" for m in project.models):
        project.add(Model(name="rigid", physics="MECAx", element="Rxx3D", dimension=3))

    def _fix(aid: str) -> None:
        project.add(DOFOperation(
            operation_type="imposeDrivenDof", target_type="avatar",
            target_value=aid,
            parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
        ))

    def _inside_cytoplasm(px, py, pz, r) -> bool:
        dist = math.sqrt((px - x0) ** 2 + (py - y0) ** 2 + (pz - z0) ** 2)
        d1 = math.sqrt((px - x0) ** 2 + (py - y0) ** 2 + (pz - z_cm1) ** 2)
        d2 = math.sqrt((px - x0) ** 2 + (py - y0) ** 2 + (pz - z_cm2) ** 2)
        if dist - r <= diam_core / 2.0 + corb_r:
            return False
        if d1 + r >= diam_cm / 2.0 or d2 + r >= diam_cm / 2.0:
            return False
        return True

    # substrate
    subst_ids: list[str] = []
    npx = max(2, int(lxsubst / subst_gap))
    npy = max(2, int(lysubst / subst_gap))
    for i in range(npx):
        px = -lxsubst / 2.0 + x0 + (i + 0.5) * (lxsubst / npx)
        for j in range(npy):
            py = -lysubst / 2.0 + y0 + (j + 0.5) * (lysubst / npy)
            av = project.add(sphere(
                r=subst_r, center=[px, py, z_subst],
                material="TDURx", model="rigid", color="SUBST",
            ))
            subst_ids.append(av.avatar_id)
            _fix(av.avatar_id)
    project.group("substrate", subst_ids)

    # nucleus
    nucleus_ids: list[str] = []
    nphi = 12
    phi = -math.pi / 2.0
    for _i in range(nphi):
        cos_phi = math.cos(phi)
        ntheta = max(8, int(24 * max(abs(cos_phi), 0.2)))
        theta = 0.0
        for _j in range(ntheta):
            cx = x0 + radii_corb * cos_phi * math.cos(theta)
            cy = y0 + radii_corb * cos_phi * math.sin(theta)
            cz = z0 + radii_corb * math.sin(phi)
            av = project.add(Avatar(
                avatar_type=AvatarType.RIGID_SPHERE,
                center=[cx, cy, cz],
                material_name="CELLx", model_name="rigid", color="BNOYs",
                origin=AvatarOrigin.MANUAL, radius=corb_r,
                contactors=[{"shape": "PT3Dx", "color": "BNOYp"}],
            ))
            nucleus_ids.append(av.avatar_id)
            theta += 2.0 * math.pi / ntheta
        phi += math.pi / nphi
    project.group("nucleus", nucleus_ids)

    # membrane
    membrane_ids: list[str] = []
    nphi_m = 10

    def _membrane_shell(z_ctr: float, keep_below: bool) -> None:
        phi_m = -math.pi / 2.0
        for _i in range(nphi_m):
            cos_phi = math.cos(phi_m)
            ntheta = max(8, int(20 * max(abs(cos_phi), 0.2)))
            theta = 0.0
            for _j in range(ntheta):
                cz = z_ctr + radii_cm * math.sin(phi_m)
                skip = (keep_below and cz >= z0) or ((not keep_below) and cz <= z0)
                if not skip:
                    cx = x0 + radii_cm * cos_phi * math.cos(theta)
                    cy = y0 + radii_cm * cos_phi * math.sin(theta)
                    av = project.add(Avatar(
                        avatar_type=AvatarType.RIGID_SPHERE,
                        center=[cx, cy, cz],
                        material_name="CELLx", model_name="rigid", color="BCELs",
                        origin=AvatarOrigin.MANUAL, radius=celb_r,
                        contactors=[
                            {"shape": "PT3Dx", "color": "BCELp"},
                            {"shape": "SPHER", "color": "BCELt", "byrd": celb_r / 10.0},
                        ],
                    ))
                    membrane_ids.append(av.avatar_id)
                theta += 2.0 * math.pi / ntheta
            phi_m += math.pi / nphi_m

    _membrane_shell(z_cm1, True)
    _membrane_shell(z_cm2, False)
    project.group("membrane", membrane_ids)

    # cytosol
    rng = np.random.default_rng(seed)
    cytosol_ids: list[str] = []
    attempts = 0
    while len(cytosol_ids) < n_cytosol and attempts < n_cytosol * 50:
        attempts += 1
        r = float(rng.uniform(ctsl_r_min, ctsl_r_max))
        px = float(rng.uniform(x0 - diam_cell / 2, x0 + diam_cell / 2))
        py = float(rng.uniform(y0 - diam_cell / 2, y0 + diam_cell / 2))
        pz = float(rng.uniform(z0 - diam_cell / 2, z0 + diam_cell / 2))
        if not _inside_cytoplasm(px, py, pz, r):
            continue
        av = project.add(Avatar(
            avatar_type=AvatarType.RIGID_SPHERE,
            center=[px, py, pz],
            material_name="CELLx", model_name="rigid", color="CTSLs",
            origin=AvatarOrigin.MANUAL, radius=r,
            contactors=[{"shape": "PT3Dx", "color": "CTSLp"}],
        ))
        cytosol_ids.append(av.avatar_id)
    project.group("cytosol", cytosol_ids)

    # focals + predefined DOF toward substrate binding sites
    focal_ids: list[str] = []
    protein_targets: list[list[float]] = []
    for i in range(nb_focals):
        nb_tours = max(1, nb_focals // nb_focals_ptour)
        rad = radii_celb - int(i / nb_focals_ptour) * (radii_celb / nb_tours)
        theta = 2.0 * i * math.pi / nb_focals_ptour
        px_p = x0 + shift_amp * rad * math.cos(theta)
        py_p = y0 + shift_amp * rad * math.sin(theta)
        pz_p = z_subst  # binding on substrate plane
        protein_targets.append([px_p, py_p, pz_p])

        dist_xy = math.sqrt(px_p ** 2 + py_p ** 2) + 1e-12
        ang = (math.pi / 4.0) * min(1.0, dist_xy / (shift_amp * radii_celb + 1e-12))
        proj = radii_cm * math.sin(ang)
        fx = (proj / dist_xy) * px_p
        fy = (proj / dist_xy) * py_p
        fz = -radii_cm * math.cos(ang) + z_cm1

        av = project.add(Avatar(
            avatar_type=AvatarType.RIGID_SPHERE,
            center=[fx, fy, fz],
            material_name="CELLx", model_name="rigid", color="INTEs",
            origin=AvatarOrigin.MANUAL, radius=celb_r,
            contactors=[{"shape": "PT3Dx", "color": f"I{i:04d}"}],
        ))
        focal_ids.append(av.avatar_id)

        # Spreading DOF (phase SPRD): velocity toward protein site
        # ct = charinc * Δposition  → reaches target in ~1/charinc time units
        dx = px_p - fx
        dy = py_p - fy
        dz = pz_p - fz
        for comp, delta, rampi in (
            (1, dx, 1.0),  # horizontal
            (2, dy, 1.0),
            (3, dz, 1.0),  # vertical (vspread in cell.py phase 0)
        ):
            project.add(DOFOperation(
                operation_type="imposeDrivenDof",
                target_type="avatar",
                target_value=av.avatar_id,
                parameters={
                    "component": comp,
                    "description": "predefined",
                    "ct": charinc_sprd * delta,
                    "amp": 0.0,
                    "omega": 0.0,
                    "phi": 0.0,
                    "rampi": rampi,
                    "ramp": 0.0,
                    "dofty": "vlocy",
                    "phase": "SPRD",
                },
            ))
    project.group("focals", focal_ids)

    # networks
    def _place_network(n: int, color_s: str, color_p: str, preferential: bool) -> list[str]:
        ids: list[str] = []
        dir_phi = float(rng.uniform(0.0, 2.0 * math.pi))
        dir_theta = float(rng.uniform(-math.pi / 2.0, math.pi / 2.0))
        tries = 0
        while len(ids) < n and tries < n * 80:
            tries += 1
            rad = float(rng.uniform(
                diam_core / 2.0 + 2.0 * corb_r + r_net,
                diam_cm / 2.0 - r_net,
            ))
            if preferential:
                theta = float(rng.normal(dir_theta, math.pi / 2.0))
                phi_n = float(rng.normal(dir_phi, math.pi / 2.0))
            else:
                theta = float(rng.uniform(0.0, 2.0 * math.pi))
                phi_n = float(rng.uniform(-math.pi / 2.0, math.pi / 2.0))
            px = x0 + rad * math.cos(phi_n) * math.cos(theta)
            py = y0 + rad * math.cos(phi_n) * math.sin(theta)
            pz = z0 + rad * math.sin(phi_n)
            if not _inside_cytoplasm(px, py, pz, r_net):
                continue
            av = project.add(Avatar(
                avatar_type=AvatarType.RIGID_SPHERE,
                center=[px, py, pz],
                material_name="CELLx", model_name="rigid", color=color_s,
                origin=AvatarOrigin.MANUAL, radius=r_net,
                contactors=[{"shape": "PT3Dx", "color": color_p}],
            ))
            ids.append(av.avatar_id)
        return ids

    mf_ids = _place_network(nb_mf, "MFsxx", "MFpxx", False)
    mt_ids = _place_network(nb_mt, "MTsxx", "MTpxx", True)
    if_ids = _place_network(nb_if, "IFsxx", "IFpxx", False)
    project.group("microfilaments", mf_ids)
    project.group("microtubules", mt_ids)
    project.group("interm_filaments", if_ids)
    project.group(
        "cell",
        nucleus_ids + membrane_ids + cytosol_ids + focal_ids + mf_ids + mt_ids + if_ids,
    )
    project.group("nucleus_set", nucleus_ids)  # for post-pro rigid sets
    project.group("cell_set", nucleus_ids + membrane_ids + cytosol_ids)

    # --- laws: stabilisation (active) ---
    project.add(ContactLaw(name="ictn0", law_type=ContactLawType.IQS_CLB, friction=0.07))
    project.add(ContactLaw(
        name="ismt0", law_type=ContactLawType.ELASTIC_ROD,
        properties={"stiffness": 22.8 * stiff, "prestrain": 0.0},
    ))
    project.add(ContactLaw(
        name="icif0", law_type=ContactLawType.ELASTIC_WIRE,
        properties={"stiffness": 15.7 * stiff, "prestrain": 0.10},
    ))
    project.add(ContactLaw(
        name="icmf0", law_type=ContactLawType.ELASTIC_WIRE,
        properties={"stiffness": 1.0 * stiff, "prestrain": -0.02 * pstr},
    ))
    project.add(ContactLaw(
        name="icnm0", law_type=ContactLawType.ELASTIC_ROD,
        properties={"stiffness": 1.0 * stiff, "prestrain": 0.0},
    ))
    project.add(ContactLaw(
        name="iccm0", law_type=ContactLawType.ELASTIC_ROD,
        properties={"stiffness": 5.0 * stiff, "prestrain": -0.02 * pstr},
    ))
    project.add(ContactLaw(
        name="icfa0", law_type=ContactLawType.ELASTIC_WIRE,
        properties={"stiffness": 10.0 * stiff, "prestrain": 0.0},
    ))
    project.add(ContactLaw(
        name="icci0", law_type=ContactLawType.ELASTIC_WIRE,
        properties={"stiffness": 100.0 * stiff, "prestrain": 0.0},
    ))

    for c1, c2, alert in [
        ("CTSLs", "CTSLs", ctsl_r_max),
        ("CTSLs", "BNOYs", max(corb_r, ctsl_r_max)),
        ("BNOYs", "BNOYs", corb_r),
        ("CTSLs", "SUBST", ctsl_r_max),
        ("BNOYs", "SUBST", 0.1 * corb_r),
        ("BCELs", "BCELs", celb_r / 10.0),
        ("BCELs", "BNOYs", max(corb_r, celb_r)),
        ("BCELs", "CTSLs", ctsl_r_max),
        ("BCELs", "SUBST", 0.1 * celb_r),
        ("BCELs", "MFsxx", celb_r),
        ("BCELs", "MTsxx", celb_r),
        ("BCELs", "IFsxx", celb_r),
        ("BNOYs", "MFsxx", corb_r),
        ("BNOYs", "MTsxx", corb_r),
        ("BNOYs", "IFsxx", corb_r),
        ("INTEs", "SUBST", 0.1 * celb_r),
        ("INTEs", "BCELs", celb_r),
    ]:
        see_table(
            project,
            cand_body="RBDY3", cand="SPHER", cand_color=c1,
            ant_body="RBDY3", ant="SPHER", ant_color=c2,
            law="ictn0", alert=float(alert),
        )

    see_table(project, cand_body="RBDY3", cand="PT3Dx", cand_color="MTpxx",
              ant_body="RBDY3", ant="PT3Dx", ant_color="MTpxx", law="ismt0", alert=alert_intra)
    see_table(project, cand_body="RBDY3", cand="PT3Dx", cand_color="IFpxx",
              ant_body="RBDY3", ant="PT3Dx", ant_color="IFpxx", law="icif0", alert=alert_intra)
    see_table(project, cand_body="RBDY3", cand="PT3Dx", cand_color="MFpxx",
              ant_body="RBDY3", ant="PT3Dx", ant_color="MFpxx", law="icmf0", alert=alert_intra)
    see_table(project, cand_body="RBDY3", cand="PT3Dx", cand_color="BNOYp",
              ant_body="RBDY3", ant="PT3Dx", ant_color="BNOYp", law="icnm0", alert=4.0 * corb_r)
    see_table(project, cand_body="RBDY3", cand="PT3Dx", cand_color="BCELp",
              ant_body="RBDY3", ant="PT3Dx", ant_color="BCELp", law="iccm0", alert=4.0 * celb_r)
    see_table(project, cand_body="RBDY3", cand="PT3Dx", cand_color="MTpxx",
              ant_body="RBDY3", ant="PT3Dx", ant_color="MFpxx", law="icci0", alert=alert_extra)
    see_table(project, cand_body="RBDY3", cand="PT3Dx", cand_color="MFpxx",
              ant_body="RBDY3", ant="PT3Dx", ant_color="BNOYp", law="icci0", alert=alert_extra)
    see_table(project, cand_body="RBDY3", cand="PT3Dx", cand_color="MFpxx",
              ant_body="RBDY3", ant="PT3Dx", ant_color="BCELp", law="icci0", alert=alert_extra)
    see_table(project, cand_body="RBDY3", cand="PT3Dx", cand_color="IFpxx",
              ant_body="RBDY3", ant="PT3Dx", ant_color="BNOYp", law="icci0", alert=alert_extra)
    see_table(project, cand_body="RBDY3", cand="PT3Dx", cand_color="BCELp",
              ant_body="RBDY3", ant="PT3Dx", ant_color="I0000", law="icfa0", alert=10.0 * celb_r)

    # post-pro (names as cell.py)
    step_stbl = max(1, int(nsteps_stbl / noutp))
    project.add(PostProCommand(name="SOLVER INFORMATIONS", step=1))
    project.add(PostProCommand(name="KINETIC ENERGY", step=step_stbl))
    project.add(PostProCommand(
        name="NEW RIGID SETS", step=step_stbl,
        target_type="groups", target_value=["nucleus_set", "cell_set"],
    ))
    project.add(PostProCommand(
        name="TORQUE EVOLUTION", step=step_stbl,
        target_type="group", target_value="focals",
    ))
    project.add(PostProCommand(
        name="BODY TRACKING", step=step_stbl,
        target_type="group", target_value="cell_set",
    ))

    # dual-phase metadata for engine export
    project.dynamic_vars["cell_phases"] = (
        "{"
        f"'nsteps_sprd':{nsteps_sprd},'dt_sprd':{dt_sprd},"
        f"'nsteps_stbl':{nsteps_stbl},'dt_stbl':{dt_stbl},'noutp':{noutp},"
        f"'charinc_sprd':{charinc_sprd},"
        "'sprd':{'visco_pen':1e-8,'stiff_pen':5000.0,'pstr_pen':0.0,'path':'DATBOX_SPRD'},"
        "'stbl':{'visco_pen':1.0,'stiff_pen':0.20,'pstr_pen':2.0,'path':'DATBOX_STBL'},"
        f"'n_focals':{len(focal_ids)},'protein_targets':{protein_targets!r}"
        "}"
    )
    project.dynamic_vars["cell_adhesion"] = (
        f"{{'wave':4,'n_total':{len(project.avatars)},"
        f"'n_focal_dof_predefined':{len(focal_ids)*3},"
        f"'active_phase':'STBL','dual_datbox':True}}"
    )



def cell_adhesion_v5(project: Project) -> None:
    """Vague 5 — showcase complet cellule (Vassaux / LMGC90).

    Enchaîne vague 4 (géométrie + réseaux + DOF predefined + post-pro) et
    annote le projet pour l'export dual engine::

        session.write_cell_dual_datbox(out_dir)
        → DATBOX_SPRD/  DATBOX_STBL/  PHASES.json  pre_cell.py

    Architecture respectée : core = intent ; engine = pylmgc writeDatbox.
    """
    cell_adhesion_v4(project)
    # mark as final wave + export recipe
    meta = dict(project.dynamic_vars or {})
    meta["cell_adhesion"] = (
        "{'wave':5,'showcase':True,'export':'write_cell_dual_datbox',"
        "'paths':['DATBOX_SPRD','DATBOX_STBL','PHASES.json','pre_cell.py']}"
    )
    meta["cell_export"] = (
        "{'api':'EngineSession.write_cell_dual_datbox',"
        "'gui':'ProjectController.write_cell_dual_datbox'}"
    )
    project.dynamic_vars.update(meta)



def masonry_deformable_wall(project: Project) -> None:
    """Mur de maçonnerie déformable (gen_sample LMGC90) — pure core.

    Fidèle à gen_sample.py :
      • matériau ELAS ``stone`` + modèle Q4 ``M2D_L``
      • assises alternées demi-brique / brique (brique entière = 2 demi liées CZM)
      • fondation + poutre de charge en rigidJonc (WALLx)
      • lois MAL_CZM (joints + rupture brique) + COUPLED_DOF (poutre/fondation)
      • see-tables HORIx / VERTx / REDxx / UPxxx
      • DOF poutre : évolution vx (metadata + imposeDrivenDof)
    """
    from ..entities import DOFOperation, PostProCommand

    # --- dimensions (m) ---
    brick_length = 210.0e-3
    brick_height = 52.0e-3
    joint_thick = 10.0e-3
    lcx = (4.5 * brick_length + 4.0 * joint_thick) / (4.5 * 2.0)
    lcy = (18.0 * brick_height + 17.0 * joint_thick) / 18.0
    apab = [0.25, 0.75]
    ep_h = 0.0
    ep_v = 0.0

    # --- materials / models ---
    if not any(m.name == "TDURx" for m in project.materials):
        project.add(Material(
            name="TDURx", material_type=MaterialType.RIGID, density=2500.0,
        ))
    if not any(m.name == "stone" for m in project.materials):
        project.add(Material(
            name="stone",
            material_type=MaterialType.ELAS,
            density=2.5e3,
            properties={
                "elas": "standard",
                "young": 1.67e10,
                "nu": 0.15,
                "anisotropy": "isotropic",
            },
        ))
    if not any(m.name == "M2D_L" for m in project.models):
        project.add(Model(
            name="M2D_L",
            physics="MECAx",
            element="Q4xxx",
            dimension=2,
            options={
                "external_model": "MatL_",
                "kinematic": "small",
                "material": "elas_",
                "anisotropy": "iso__",
                "mass_storage": "lump_",
            },
        ))
    if not any(m.name == "rigid" for m in project.models):
        project.add(Model(
            name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
        ))

    # courses: 18 assises alternate
    # demi = lcx x lcy, full = 2*lcx x lcy (split into two demi)
    assise_paire = ["demi", "full", "full", "full", "full"]
    assise_impaire = ["full", "full", "full", "full", "demi"]
    mur = []
    for j in range(18):
        mur.append(assise_paire if j % 2 == 1 else assise_impaire)

    def _half_brick(cx: float, cy: float, colors: list[str] | None, top: bool) -> Avatar:
        nb_x = max(1, int((lcx / (0.5 * lcx))))
        nb_y = max(1, int((lcy / (0.5 * lcy))))
        # floor: demi_moellon.lx/(0.5*lcx) = lcx/(0.5*lcx)=2
        nb_elem_x = int(max(1, (lcx / (0.5 * lcx)) // 1))
        nb_elem_y = int(max(1, (lcy / (0.5 * lcy)) // 1))
        mp = {
            "geom": "deformableBrick",
            "source": "deformableBrick",
            "brick_name": "demi-brique",
            "brick_lx": lcx,
            "brick_ly": lcy,
            "mesh_type": "Q4",
            "nb_elem_x": nb_elem_x,
            "nb_elem_y": nb_elem_y,
            "apabh": list(apab),
            "apabv": list(apab),
        }
        if colors is not None:
            mp["colors"] = list(colors)
        contactors = []
        if top:
            contactors.append({
                "shape": "CLxxx", "color": "UPxxx", "group": "up",
                "params": {"weights": list(apab)},
            })
        return project.add(Avatar(
            avatar_type=AvatarType.MESH_DEFORMABLE,
            center=[cx, cy],
            material_name="stone",
            model_name="M2D_L",
            color="REDxx",
            origin=AvatarOrigin.MANUAL,
            mesh_params=mp,
            contactors=contactors,
        ))

    brick_ids: list[str] = []
    y = 0.0
    n_top = len(mur) - 1
    for j, assise in enumerate(mur):
        x = 0.0
        for i, kind in enumerate(assise):
            if i == 0:
                y += 0.5 * lcy
            if kind == "full":
                # full brick width 2*lcx — two half bricks
                x += 0.5 * (2.0 * lcx)
                # left / right colors from gen_sample
                left_colors = ["HORIx", "REDxx", "HORIx", "VERTx"]
                right_colors = ["HORIx", "VERTx", "HORIx", "REDxx"]
                top = (j == n_top)
                bl = _half_brick(x - 0.25 * (2.0 * lcx), y, left_colors, top)
                br = _half_brick(x + 0.25 * (2.0 * lcx), y, right_colors, top)
                brick_ids.extend([bl.avatar_id, br.avatar_id])
                x += 0.5 * (2.0 * lcx) + ep_v
            else:
                # demi
                x += 0.5 * lcx
                top = (j == n_top)
                b = _half_brick(x, y, None, top)
                brick_ids.append(b.avatar_id)
                x += 0.5 * lcx + ep_v
        y += 0.5 * lcy + ep_h

    project.group("bricks", brick_ids)

    # foundation
    floor = project.add(Avatar(
        avatar_type=AvatarType.RIGID_JONC,
        center=[4.5 * lcx, -0.5 * lcy],
        material_name="TDURx",
        model_name="rigid",
        color="WALLx",
        origin=AvatarOrigin.MANUAL,
        axis={"axe1": 4.5 * lcx, "axe2": 0.5 * lcy},
        # color WALLx → contactor JONCx already from rigidJonc (do not re-add without axe*)
    ))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="avatar",
        target_value=floor.avatar_id,
        parameters={"component": [1, 2, 3], "dofty": "vlocy", "ct": 0.0},
    ))

    # loading beam
    beam_length = 9.0 * lcx
    beam_height = brick_height
    beam = project.add(Avatar(
        avatar_type=AvatarType.RIGID_JONC,
        center=[0.5 * beam_length, 18.0 * lcy + 0.5 * beam_height],
        material_name="TDURx",
        model_name="rigid",
        color="WALLx",
        origin=AvatarOrigin.MANUAL,
        axis={"axe1": 0.5 * beam_length, "axe2": 0.5 * beam_height},
    ))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="avatar",
        target_value=beam.avatar_id,
        parameters={"component": [2, 3], "dofty": "vlocy", "ct": 0.0},
    ))
    project.add(DOFOperation(
        operation_type="imposeDrivenDof",
        target_type="avatar",
        target_value=beam.avatar_id,
        parameters={
            "description": "evolution",
            "component": 1,
            "dofty": "vlocy",
            "evolutionFile": "vx.dat",
        },
    ))
    project.group("beam", [beam.avatar_id])
    project.group("floor", [floor.avatar_id])

    # laws MAL_CZM joint / brick + COUPLED_DOF
    mu_joint = 0.75
    kn_joint, kt_joint = 8.2e10, 3.6e10
    sigmaMaxI_joint = 2.5e5
    GI_joint, GII_joint = 1.8e1, 1.25e2
    project.add(ContactLaw(
        name="malc0",
        law_type=ContactLawType.MAL_CZM,
        friction=mu_joint,
        properties={
            "dyfr": mu_joint, "stfr": mu_joint,
            "cn": kn_joint, "s1": sigmaMaxI_joint, "G1": GI_joint,
            "ct": kt_joint, "s2": 1.4 * sigmaMaxI_joint, "G2": GII_joint,
        },
    ))
    mu_brick = 0.0
    kn_brick = kt_brick = 1.0e15
    sigmaMaxI_brick = 2.5e5
    GI_brick = 8.0e1
    project.add(ContactLaw(
        name="malc1",
        law_type=ContactLawType.MAL_CZM,
        friction=mu_brick,
        properties={
            "dyfr": mu_brick, "stfr": mu_brick,
            "cn": kn_brick, "s1": sigmaMaxI_brick, "G1": GI_brick,
            "ct": kt_brick, "s2": sigmaMaxI_brick, "G2": GI_brick,
        },
    ))
    project.add(ContactLaw(
        name="cpld0", law_type=ContactLawType.COUPLED_DOF,
    ))

    alert = 0.1 * min(lcx, lcy)
    see_table(
        project,
        cand_body="MAILx", cand="CLxxx", cand_color="HORIx",
        ant_body="MAILx", ant="ALpxx", ant_color="HORIx",
        law="malc0", alert=alert,
    )
    see_table(
        project,
        cand_body="MAILx", cand="CLxxx", cand_color="VERTx",
        ant_body="MAILx", ant="ALpxx", ant_color="VERTx",
        law="malc0", alert=alert,
    )
    see_table(
        project,
        cand_body="MAILx", cand="CLxxx", cand_color="REDxx",
        ant_body="MAILx", ant="ALpxx", ant_color="REDxx",
        law="malc1", alert=alert,
    )
    see_table(
        project,
        cand_body="MAILx", cand="CLxxx", cand_color="HORIx",
        ant_body="RBDY2", ant="JONCx", ant_color="WALLx",
        law="cpld0", alert=alert,
    )
    see_table(
        project,
        cand_body="MAILx", cand="CLxxx", cand_color="UPxxx",
        ant_body="RBDY2", ant="JONCx", ant_color="WALLx",
        law="cpld0", alert=alert,
    )

    project.add(PostProCommand(
        name="BODY TRACKING", step=1, target_type="group", target_value="beam",
    ))
    project.add(PostProCommand(
        name="TORQUE EVOLUTION", step=1, target_type="group", target_value="beam",
    ))

    # evolution metadata (engine / command.py can emit vx.dat)
    project.dynamic_vars["vx_evolution"] = (
        "{'v_max':0.02,'t_rest':0.005,'t_ramp':0.01,'file':'vx.dat',"
        "'description':'0 until 0.005, linear ramp to v_max until 0.01, then constant'}"
    )
    project.dynamic_vars["masonry_deformable_wall"] = (
        f"{{'bricks':{len(brick_ids)},'lcx':{lcx},'lcy':{lcy},"
        f"'courses':18,'source':'gen_sample.py'}}"
    )



def cylinder_deposit_3d(project: Project) -> None:
    """Dépôt de sphères dans un cylindre creux 3D (gen_sample LMGC90).

    • granulo random [0.5, 2] + depositInCylinder3D (R=7.5, lz=10)
    • fond rigidPlan + cylindre creux (is_Hollow) VERTx
    • IQS_CLB grains / parois · see-tables SPHER / PLANx / DNLYC
    Core : GranuloConfig ; dépôt réel via engine (pylmgc ou fallback).
    """
    from ..entities import DOFOperation, GranuloConfig

    if not any(m.name == "PLEXx" for m in project.materials):
        project.add(Material(
            name="PLEXx", material_type=MaterialType.RIGID, density=100.0,
        ))
    if not any(m.name == "TDURx" for m in project.materials):
        project.add(Material(
            name="TDURx", material_type=MaterialType.RIGID, density=1000.0,
        ))
    if not any(m.name == "rigid" for m in project.models):
        project.add(Model(
            name="rigid", physics="MECAx", element="Rxx3D", dimension=3,
        ))

    R = 7.5
    lz = 10.0
    rmin, rmax = 0.3, 1.2
    nb = 100

    # walls first (fixed)
    floor = project.add(Avatar(
        avatar_type=AvatarType.RIGID_PLAN,
        center=[0.0, 0.0, -rmin],
        material_name="TDURx",
        model_name="rigid",
        color="VERTx",
        origin=AvatarOrigin.MANUAL,
        axis={"axe1": R, "axe2": R, "axe3": rmin},
    ))
    cyl = project.add(Avatar(
        avatar_type=AvatarType.RIGID_CYLINDER,
        center=[0.0, 0.0, 0.5 * lz],
        material_name="TDURx",
        model_name="rigid",
        color="VERTx",
        origin=AvatarOrigin.MANUAL,
        radius=R,
        is_hollow=True,
        wall_params={"h": lz, "r": R},
        contactors=[{"shape": "DNLYC", "color": "VERTx"}],
    ))
    for aid in (floor.avatar_id, cyl.avatar_id):
        project.add(DOFOperation(
            operation_type="imposeDrivenDof",
            target_type="avatar",
            target_value=aid,
            parameters={
                "component": [1, 2, 3, 4, 5, 6],
                "dofty": "vlocy",
                "ct": 0.0,
            },
        ))
    project.group("walls", [floor.avatar_id, cyl.avatar_id])

    # deposit intent — resolved by engine depositInCylinder3D
    project.granulo.append(GranuloConfig(
        nb_particles=nb,
        radius_min=rmin,
        radius_max=rmax,
        container_type="Cylinder3D",
        container_params={"R": R, "lz": lz, "r": R},
        material_name="PLEXx",
        model_name="rigid",
        avatar_type="rigidSphere",
        color="BLEUx",
        group_name="grains",
        dimension=3,
    ))

    project.add(ContactLaw(
        name="iqsc0", law_type=ContactLawType.IQS_CLB, friction=0.3,
    ))
    project.add(ContactLaw(
        name="iqsc1", law_type=ContactLawType.IQS_CLB, friction=0.5,
    ))
    alert = 0.1 * rmin
    see_table(
        project,
        cand_body="RBDY3", cand="SPHER", cand_color="BLEUx",
        ant_body="RBDY3", ant="SPHER", ant_color="BLEUx",
        law="iqsc0", alert=alert,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="SPHER", cand_color="BLEUx",
        ant_body="RBDY3", ant="PLANx", ant_color="VERTx",
        law="iqsc1", alert=alert,
    )
    see_table(
        project,
        cand_body="RBDY3", cand="SPHER", cand_color="BLEUx",
        ant_body="RBDY3", ant="DNLYC", ant_color="VERTx",
        law="iqsc1", alert=rmin,
    )
    project.dynamic_vars["cylinder_deposit_3d"] = (
        f"{{'nb':{nb},'R':{R},'lz':{lz},'rmin':{rmin},'rmax':{rmax},"
        f"'source':'gen_sample_cylinder3d'}}"
    )




SCENE_BUILDERS = {
    "cylinder_deposit_3d": cylinder_deposit_3d,
    "masonry_deformable_wall": masonry_deformable_wall,
    "cell_adhesion_v5": cell_adhesion_v5,
    "cell_adhesion_v4": cell_adhesion_v4,
    "cell_adhesion_v3": cell_adhesion_v3,
    "cell_adhesion_v2": cell_adhesion_v2,
    "cell_adhesion_v1": cell_adhesion_v1,
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
