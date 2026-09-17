"""LMGC90 constraints. Fail before a bad scene is serialised or scripted."""
from __future__ import annotations

from .entities import Avatar, ContactLaw, Material, Model, VisibilityRule
from .errors import ValidationError
from .types import (
    CONTACTORS_MESH_2D, CONTACTORS_MESH_3D,
    CONTACTORS_RIGID_2D, CONTACTORS_RIGID_3D,
    CONTACT_LAW_CATEGORIES, DEFORMABLE_2D, DEFORMABLE_3D,
    ELEMENTS_BY_PHYSICS, RIGID_AVATARS_2D, RIGID_AVATARS_3D,
    RIGID_ELEMENTS_2D, RIGID_ELEMENTS_3D, AvatarType,
)


def _ok_name(name: str, kind: str) -> None:
    if not name or not name.strip():
        raise ValidationError(f"{kind} name cannot be empty")
    if len(name) > 5:
        raise ValidationError(f"{kind} name {name!r} must be ≤ 5 characters (LMGC90)")


def validate_material(material: Material) -> None:
    _ok_name(material.name, "material")
    if material.density <= 0:
        raise ValidationError("density must be strictly positive")


def validate_model(model: Model) -> None:
    _ok_name(model.name, "model")
    if model.dimension not in (2, 3):
        raise ValidationError("dimension must be 2 or 3")
    physics = model.physics or "MECAx"
    table = ELEMENTS_BY_PHYSICS.get(physics)
    if table is None:
        return
    allowed = table.get(model.dimension)
    if allowed is None:
        raise ValidationError(f"no elements for {physics} in {model.dimension}D")
    if model.element not in allowed:
        raise ValidationError(
            f"element {model.element!r} invalid for {physics} in {model.dimension}D"
        )


def validate_avatar(avatar: Avatar, model: Model) -> None:
    dim = model.dimension
    if len(avatar.center) != dim:
        raise ValidationError(
            f"center has {len(avatar.center)} coords, model is {dim}D"
        )
    if not avatar.material_name or not avatar.model_name:
        raise ValidationError("material and model are required")

    atype = avatar.avatar_type
    if atype in RIGID_AVATARS_2D:
        if dim != 2:
            raise ValidationError(f"{atype.value} requires a 2D model")
        if model.element not in RIGID_ELEMENTS_2D:
            raise ValidationError(f"{atype.value} requires element Rxx2D, not {model.element}")
    if atype in RIGID_AVATARS_3D:
        if dim != 3:
            raise ValidationError(f"{atype.value} requires a 3D model")
        if model.element not in RIGID_ELEMENTS_3D:
            raise ValidationError(f"{atype.value} requires element Rxx3D, not {model.element}")
    if atype == AvatarType.MESH_DEFORMABLE:
        valid = DEFORMABLE_2D if dim == 2 else DEFORMABLE_3D
        if model.element not in valid:
            raise ValidationError(f"element {model.element} invalid for deformable mesh")

    _check_geometry(avatar, dim)


def _need_radius(avatar: Avatar, label: str) -> None:
    if avatar.radius is None or avatar.radius <= 0:
        raise ValidationError(f"positive radius required for {label}")


def _check_geometry(avatar: Avatar, dim: int) -> None:
    atype = avatar.avatar_type
    wp = avatar.wall_params or {}

    if atype == AvatarType.RIGID_DISK:
        _need_radius(avatar, "rigidDisk")
    elif atype == AvatarType.RIGID_SPHERE:
        _need_radius(avatar, "rigidSphere")
    elif atype == AvatarType.RIGID_DISCRETE:
        _need_radius(avatar, "rigidDiscreteDisk")
    elif atype == AvatarType.RIGID_JONC:
        if not avatar.axis or "axe1" not in avatar.axis or "axe2" not in avatar.axis:
            raise ValidationError("axe1 and axe2 required for rigidJonc")
        if avatar.axis["axe1"] <= 0 or avatar.axis["axe2"] <= 0:
            raise ValidationError("rigidJonc axes must be > 0")
        if avatar.axis["axe1"] <= avatar.axis["axe2"]:
            raise ValidationError("rigidJonc: axe1 must be > axe2")
    elif atype == AvatarType.RIGID_POLYGON:
        if avatar.generation_type == "regular":
            if not avatar.nb_vertices or avatar.nb_vertices < 3:
                raise ValidationError("nb_vertices >= 3 required for regular polygon")
            _need_radius(avatar, "regular polygon")
        elif not avatar.vertices or len(avatar.vertices) < 3:
            raise ValidationError("at least 3 vertices required for custom polygon")
    elif atype == AvatarType.RIGID_CLUSTER:
        _need_radius(avatar, "rigidCluster")
        if not avatar.nb_vertices or avatar.nb_vertices < 2:
            raise ValidationError("nb_disk >= 2 required for rigidCluster")
    elif atype in (AvatarType.ROUGH_WALL, AvatarType.FINE_WALL):
        if "l" not in wp or "r" not in wp:
            raise ValidationError(f"l and r required for {atype.value}")
        if wp["l"] <= 0 or wp["r"] <= 0:
            raise ValidationError("l and r must be positive")
    elif atype == AvatarType.SMOOTH_WALL:
        if "l" not in wp or "h" not in wp:
            raise ValidationError("l and h required for smoothWall")
        if wp["l"] <= 0 or wp["h"] <= 0:
            raise ValidationError("l and h must be positive")
    elif atype == AvatarType.GRANULO_WALL:
        for k in ("l", "rmin", "rmax"):
            if k not in wp:
                raise ValidationError(f"{k} required for granuloRoughWall")
        if wp["rmin"] > wp["rmax"]:
            raise ValidationError("rmin must be <= rmax")
    elif atype == AvatarType.RIGID_PLAN:
        if not avatar.axis or any(k not in avatar.axis for k in ("axe1", "axe2", "axe3")):
            raise ValidationError("axe1, axe2, axe3 required for rigidPlan")
    elif atype == AvatarType.RIGID_CYLINDER:
        _need_radius(avatar, "rigidCylinder")
        if "h" not in wp or wp["h"] <= 0:
            raise ValidationError("positive h required for rigidCylinder")
    elif atype == AvatarType.RIGID_POLYHEDRON:
        if avatar.generation_type == "regular":
            if not avatar.nb_vertices or avatar.nb_vertices < 4:
                raise ValidationError("nb_vertices >= 4 for regular polyhedron")
            _need_radius(avatar, "regular polyhedron")
        elif not avatar.vertices or len(avatar.vertices) < 4:
            raise ValidationError("at least 4 vertices for custom polyhedron")
    elif atype == AvatarType.ROUGH_WALL_3D:
        if any(k not in wp for k in ("lx", "ly")):
            raise ValidationError("lx and ly required for roughWall3D")
        _need_radius(avatar, "roughWall3D")
    elif atype == AvatarType.GRANULO_ROUGH_WALL_3D:
        if any(k not in wp for k in ("lx", "ly", "rmin", "rmax")):
            raise ValidationError("lx, ly, rmin, rmax required for granuloRoughWall3D")


def validate_contact_law(law: ContactLaw) -> None:
    _ok_name(law.name, "contact law")
    known = {v for values in CONTACT_LAW_CATEGORIES.values() for v in values}
    if law.law_type.value not in known:
        raise ValidationError(f"unknown contact law {law.law_type.value}")
    if law.friction is not None and law.friction < 0:
        raise ValidationError("friction cannot be negative")


def validate_visibility(rule: VisibilityRule, law_names: set[str]) -> None:
    if rule.behavior_name not in law_names:
        raise ValidationError(
            f"visibility refers to unknown law {rule.behavior_name!r}"
        )
    if rule.alert < 0:
        raise ValidationError("alert distance cannot be negative")
    for shape in (rule.candidate_contactor, rule.antagonist_contactor):
        if len(shape) != 5:
            raise ValidationError(
                f"contactor shape {shape!r} must be 5 characters (LMGC90 convention)"
            )


def compatible_contactors(avatar_type: AvatarType, dimension: int) -> tuple[str, ...]:
    if dimension not in (2, 3):
        raise ValidationError(f"invalid dimension {dimension}")
    if avatar_type == AvatarType.MESH_DEFORMABLE:
        return CONTACTORS_MESH_2D if dimension == 2 else CONTACTORS_MESH_3D
    return CONTACTORS_RIGID_2D if dimension == 2 else CONTACTORS_RIGID_3D


def is_shape_compatible(shape: str, avatar_type: AvatarType, dimension: int) -> bool:
    return shape in compatible_contactors(avatar_type, dimension)
