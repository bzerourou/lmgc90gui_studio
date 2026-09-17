"""Factories whose names and kwargs match `pylmgc90.pre`.

A researcher who knows `pre.rigidDisk(r=..., center=..., ...)` can write
the same call against `lmgc90_core.pre` and get a pure dataclass instead
of a Fortran object. The GUI can show `Project.equivalent(obj)` to prove
the two are the same idea.
"""
from __future__ import annotations

from typing import Any, Optional

from .entities import Avatar, ContactLaw, Material, Model, VisibilityRule
from .types import AvatarOrigin, AvatarType, ContactLawType, MaterialType


def material(*, name: str, materialType: str, density: float, **properties) -> Material:
    return Material(
        name=name,
        material_type=MaterialType(materialType),
        density=float(density),
        properties=dict(properties),
    )


def model(*, name: str, physics: str, element: str, dimension: int, **options) -> Model:
    return Model(
        name=name,
        physics=physics,
        element=element,
        dimension=int(dimension),
        options=dict(options),
    )


def _avatar(atype: AvatarType, center, material, model, color, **kwargs) -> Avatar:
    return Avatar(
        avatar_type=atype,
        center=list(center),
        material_name=_name(material),
        model_name=_name(model),
        color=color,
        origin=AvatarOrigin.MANUAL,
        **kwargs,
    )


def _name(obj) -> str:
    return obj if isinstance(obj, str) else obj.name


def rigidDisk(*, r, center, model, material, color="BLUEx", is_Hollow=False) -> Avatar:
    return _avatar(
        AvatarType.RIGID_DISK, center, material, model, color,
        radius=float(r), is_hollow=bool(is_Hollow),
    )


def rigidSphere(*, r, center, model, material, color="BLUEx", is_Hollow=False) -> Avatar:
    return _avatar(
        AvatarType.RIGID_SPHERE, center, material, model, color,
        radius=float(r), is_hollow=bool(is_Hollow),
    )


def rigidJonc(*, axe1, axe2, center, model, material, color="BLUEx") -> Avatar:
    return _avatar(
        AvatarType.RIGID_JONC, center, material, model, color,
        axis={"axe1": float(axe1), "axe2": float(axe2)},
    )


def rigidPolygon(*, center, model, material, color="BLUEx",
                 generation_type="regular", nb_vertices=None, radius=None,
                 vertices=None) -> Avatar:
    return _avatar(
        AvatarType.RIGID_POLYGON, center, material, model, color,
        generation_type=generation_type,
        nb_vertices=nb_vertices,
        radius=radius,
        vertices=vertices,
    )


def rigidCluster(*, r, center, model, material, color="BLUEx", nb_disk=3) -> Avatar:
    return _avatar(
        AvatarType.RIGID_CLUSTER, center, material, model, color,
        radius=float(r), nb_vertices=int(nb_disk),
    )


def rigidCylinder(*, r, h, center, model, material, color="BLUEx", is_Hollow=False) -> Avatar:
    return _avatar(
        AvatarType.RIGID_CYLINDER, center, material, model, color,
        radius=float(r), wall_params={"h": float(h)}, is_hollow=bool(is_Hollow),
    )


def rigidPlan(*, center, model, material, color="BLUEx", axe1, axe2, axe3) -> Avatar:
    return _avatar(
        AvatarType.RIGID_PLAN, center, material, model, color,
        axis={"axe1": float(axe1), "axe2": float(axe2), "axe3": float(axe3)},
    )


def smoothWall(*, l, h, center, model, material, color="BLUEx", nb_polyg=10) -> Avatar:
    return _avatar(
        AvatarType.SMOOTH_WALL, center, material, model, color,
        wall_params={"l": float(l), "h": float(h), "nb_polyg": int(nb_polyg)},
    )


def roughWall(*, l, r, center, model, material, color="BLUEx", nb_vertex=10) -> Avatar:
    return _avatar(
        AvatarType.ROUGH_WALL, center, material, model, color,
        wall_params={"l": float(l), "r": float(r), "nb_vertex": int(nb_vertex)},
    )


def fineWall(*, l, r, center, model, material, color="BLUEx", nb_vertex=10) -> Avatar:
    return _avatar(
        AvatarType.FINE_WALL, center, material, model, color,
        wall_params={"l": float(l), "r": float(r), "nb_vertex": int(nb_vertex)},
    )


def meshed_rectangle(*, lx, ly, nx, ny, center, model, material, color="CYANx",
                     mesh_type="2T3", contactors=None) -> Avatar:
    cx, cy = center[0], center[1]
    mp = {
        "geom": "Rectangle", "dim": 2, "lx": lx, "ly": ly, "nx": nx, "ny": ny,
        "mesh_type": mesh_type, "cx": cx, "cy": cy,
        "contactors": list(contactors or []),
    }
    return _avatar(
        AvatarType.MESH_DEFORMABLE, list(center), material, model, color,
        mesh_params=mp, contactors=list(contactors or []),
    )


def tact_behav(*, name: str, law: str, fric: Optional[float] = None, **properties) -> ContactLaw:
    return ContactLaw(
        name=name,
        law_type=ContactLawType(law),
        friction=fric,
        properties=dict(properties),
    )


def see_table(*, CorpsCandidat, candidat, colorCandidat,
              CorpsAntagoniste, antagoniste, colorAntagoniste,
              behav, alert=0.1) -> VisibilityRule:
    return VisibilityRule(
        candidate_body=CorpsCandidat,
        candidate_contactor=candidat,
        candidate_color=colorCandidat,
        antagonist_body=CorpsAntagoniste,
        antagonist_contactor=antagoniste,
        antagonist_color=colorAntagoniste,
        behavior_name=behav,
        alert=float(alert),
    )


def rigidDiscreteDisk(*, r, center, model, material, color="BLUEx") -> Avatar:
    return _avatar(
        AvatarType.RIGID_DISCRETE, center, material, model, color,
        radius=float(r),
    )


def rigidPolyhedron(*, center, model, material, color="BLUEx",
                    generation_type="regular", nb_vertices=None, radius=None,
                    vertices=None) -> Avatar:
    return _avatar(
        AvatarType.RIGID_POLYHEDRON, center, material, model, color,
        generation_type=generation_type, nb_vertices=nb_vertices,
        radius=radius, vertices=vertices,
    )


def rigidOvoidPolygon(*, center, model, material, color="BLUEx",
                      radius=None, vertices=None) -> Avatar:
    return _avatar(
        AvatarType.RIGID_OVOID, center, material, model, color,
        radius=radius, vertices=vertices,
    )


def granuloRoughWall(*, l, rmin, rmax, center, model, material, color="BLUEx",
                     nb_vertex=10) -> Avatar:
    return _avatar(
        AvatarType.GRANULO_WALL, center, material, model, color,
        wall_params={"l": float(l), "rmin": float(rmin), "rmax": float(rmax),
                     "nb_vertex": int(nb_vertex)},
    )


def roughWall3D(*, lx, ly, lz, center, model, material, color="BLUEx") -> Avatar:
    return _avatar(
        AvatarType.ROUGH_WALL_3D, center, material, model, color,
        wall_params={"lx": float(lx), "ly": float(ly), "lz": float(lz)},
    )


def granuloRoughWall3D(*, lx, ly, lz, rmin, rmax, center, model, material,
                       color="BLUEx") -> Avatar:
    return _avatar(
        AvatarType.GRANULO_ROUGH_WALL_3D, center, material, model, color,
        wall_params={"lx": float(lx), "ly": float(ly), "lz": float(lz),
                     "rmin": float(rmin), "rmax": float(rmax)},
    )


def emptyAvatar(*, center, model, material, color="BLUEx") -> Avatar:
    return _avatar(AvatarType.EMPTY_AVATAR, center, material, model, color)


def deformable_defaults(*, dimension: int = 2) -> dict:
    """Recommended material / model / law names for a simple deformable scene."""
    return {
        "material": {
            "name": "ELAS1",
            "materialType": "ELAS",
            "density": 2500.0,
            "young": 7.0e10,
            "nu": 0.3,
            "elas": "standard",
            "anisotropy": "isotropic",
        },
        "model": {
            "name": "femxx",
            "physics": "MECAx",
            "element": "T3xxx" if dimension == 2 else "TE4xx",
            "dimension": dimension,
        },
        "mesh": {
            "lx": 1.0, "ly": 0.4, "nx": 6, "ny": 3,
            "mesh_type": "2T3",
            "color": "CYANx",
        },
        "law": {
            "name": "gap",
            "law": "GAP_SGR_CLB",
            "fric": 0.3,
        },
        "floor": {
            "l": 2.0, "h": 0.08, "color": "GRAYx",
        },
        "contactor": {"shape": "CLxxx", "color": "CYANx"},
    }
