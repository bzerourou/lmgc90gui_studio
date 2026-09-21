"""Shared pure-project helpers for demo scenes (entities only — no ``pre``)."""
from __future__ import annotations

from ..entities import (
    Avatar,
    ContactLaw,
    Material,
    Model,
    VisibilityRule,
)
from ..project import Project
from ..types import AvatarOrigin, AvatarType, ContactLawType, MaterialType


def ensure_rigid_2d(project: Project, *, density: float = 2500.0) -> None:
    if not any(m.name == "TDURx" for m in project.materials):
        project.add(Material(
            name="TDURx", material_type=MaterialType.RIGID, density=density,
        ))
    if not any(m.name == "rigid" for m in project.models):
        project.add(Model(
            name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
        ))


def ensure_rigid_3d(project: Project, *, density: float = 2500.0) -> None:
    if not any(m.name == "TDURx" for m in project.materials):
        project.add(Material(
            name="TDURx", material_type=MaterialType.RIGID, density=density,
        ))
    if not any(m.name == "rigid" for m in project.models):
        project.add(Model(
            name="rigid", physics="MECAx", element="Rxx3D", dimension=3,
        ))


def iqs(project: Project, name: str = "iqsc0", fric: float = 0.3) -> None:
    if not any(l.name == name for l in project.laws):
        project.add(ContactLaw(
            name=name, law_type=ContactLawType.IQS_CLB, friction=fric,
        ))


def see_table(
    project: Project,
    *,
    cand_body: str,
    cand: str,
    cand_color: str,
    ant_body: str,
    ant: str,
    ant_color: str,
    law: str,
    alert: float = 0.05,
) -> None:
    project.add(VisibilityRule(
        candidate_body=cand_body,
        candidate_contactor=cand,
        candidate_color=cand_color,
        antagonist_body=ant_body,
        antagonist_contactor=ant,
        antagonist_color=ant_color,
        behavior_name=law,
        alert=alert,
    ))


def see_dd(project: Project, law: str = "iqsc0", alert: float = 0.05) -> None:
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="DISKx", ant_color="BLUEx",
        law=law, alert=alert,
    )


def see_dw(project: Project, law: str = "iqsc0", alert: float = 0.05) -> None:
    see_table(
        project,
        cand_body="RBDY2", cand="DISKx", cand_color="BLUEx",
        ant_body="RBDY2", ant="JONCx", ant_color="GRAYx",
        law=law, alert=alert,
    )


# --- avatar constructors (core entities only) ---

def disk(*, r, center, material="TDURx", model="rigid", color="BLUEx",
         is_hollow=False) -> Avatar:
    return Avatar(
        avatar_type=AvatarType.RIGID_DISK,
        center=list(center),
        material_name=material,
        model_name=model,
        color=color,
        origin=AvatarOrigin.MANUAL,
        radius=float(r),
        is_hollow=bool(is_hollow),
    )


def sphere(*, r, center, material="TDURx", model="rigid", color="BLUEx") -> Avatar:
    return Avatar(
        avatar_type=AvatarType.RIGID_SPHERE,
        center=list(center),
        material_name=material,
        model_name=model,
        color=color,
        origin=AvatarOrigin.MANUAL,
        radius=float(r),
    )


def jonc(*, axe1, axe2, center, material="TDURx", model="rigid", color="BLUEx") -> Avatar:
    return Avatar(
        avatar_type=AvatarType.RIGID_JONC,
        center=list(center),
        material_name=material,
        model_name=model,
        color=color,
        origin=AvatarOrigin.MANUAL,
        axis={"axe1": float(axe1), "axe2": float(axe2)},
    )


def plan(*, axe1, axe2, axe3, center, material="TDURx", model="rigid", color="BLUEx") -> Avatar:
    return Avatar(
        avatar_type=AvatarType.RIGID_PLAN,
        center=list(center),
        material_name=material,
        model_name=model,
        color=color,
        origin=AvatarOrigin.MANUAL,
        axis={"axe1": float(axe1), "axe2": float(axe2), "axe3": float(axe3)},
    )


def cylinder(*, r, h, center, material="TDURx", model="rigid", color="BLUEx") -> Avatar:
    return Avatar(
        avatar_type=AvatarType.RIGID_CYLINDER,
        center=list(center),
        material_name=material,
        model_name=model,
        color=color,
        origin=AvatarOrigin.MANUAL,
        radius=float(r),
        wall_params={"h": float(h)},
    )


def cluster(*, r, center, nb_disk=3, material="TDURx", model="rigid", color="BLUEx") -> Avatar:
    return Avatar(
        avatar_type=AvatarType.RIGID_CLUSTER,
        center=list(center),
        material_name=material,
        model_name=model,
        color=color,
        origin=AvatarOrigin.MANUAL,
        radius=float(r),
        nb_vertices=int(nb_disk),
        wall_params={"nb_disk": int(nb_disk)},
    )


def smooth_wall(*, l, h, center, material="TDURx", model="rigid", color="GRAYx",
                nb_polyg=24) -> Avatar:
    return Avatar(
        avatar_type=AvatarType.SMOOTH_WALL,
        center=list(center),
        material_name=material,
        model_name=model,
        color=color,
        origin=AvatarOrigin.MANUAL,
        wall_params={"l": float(l), "h": float(h), "nb_polyg": int(nb_polyg)},
    )


def rough_wall(*, l, r, center, material="TDURx", model="rigid", color="GRAYx",
               nb_vertex=10) -> Avatar:
    return Avatar(
        avatar_type=AvatarType.ROUGH_WALL,
        center=list(center),
        material_name=material,
        model_name=model,
        color=color,
        origin=AvatarOrigin.MANUAL,
        wall_params={"l": float(l), "r": float(r), "nb_vertex": int(nb_vertex)},
    )


def mesh_rect(*, lx, ly, nx, ny, center, material, model, color="CYANx",
              mesh_type="2T3", contactors=None) -> Avatar:
    cx, cy = float(center[0]), float(center[1])
    mp = {
        "geom": "Rectangle", "dim": 2,
        "lx": float(lx), "ly": float(ly), "nx": int(nx), "ny": int(ny),
        "mesh_type": mesh_type, "cx": cx, "cy": cy,
    }
    return Avatar(
        avatar_type=AvatarType.MESH_DEFORMABLE,
        center=list(center),
        material_name=material,
        model_name=model,
        color=color,
        origin=AvatarOrigin.MANUAL,
        mesh_params=mp,
        contactors=list(contactors or []),
    )
