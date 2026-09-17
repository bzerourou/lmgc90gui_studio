"""Build a single pylmgc90.pre body from a core Avatar or ParticlePopulation row.

Identity stays on the core side (avatar_id). The returned object is the Fortran
body; the EngineSession stores the mapping.
"""
from __future__ import annotations

from typing import Any, Optional

from lmgc90_core.entities import Avatar
from lmgc90_core.population import ParticlePopulation
from lmgc90_core.types import AvatarType

from .errors import MaterializationError, PylmgcNotAvailable


def _pre():
    try:
        from pylmgc90 import pre
        return pre
    except ImportError as exc:
        raise PylmgcNotAvailable(
            "pylmgc90 is required for materialization. "
            "Install it or use EngineSession.emit_pre_script() instead."
        ) from exc


def _resolve(name_or_obj, registry: dict[str, Any], kind: str):
    if isinstance(name_or_obj, str):
        if name_or_obj not in registry:
            raise MaterializationError(f"{kind} {name_or_obj!r} not materialized yet")
        return registry[name_or_obj]
    return name_or_obj


def build_avatar(
    av: Avatar,
    *,
    materials: dict[str, Any],
    models: dict[str, Any],
) -> Any:
    """Create one pre body from an AoS Avatar. Does not add it to a container."""
    pre = _pre()
    mat = _resolve(av.material_name, materials, "material")
    mod = _resolve(av.model_name, models, "model")
    center = list(av.center)
    color = av.color
    t = av.avatar_type

    try:
        if t == AvatarType.RIGID_DISK:
            body = pre.rigidDisk(
                r=float(av.radius), center=center, model=mod, material=mat,
                color=color, is_Hollow=bool(av.is_hollow),
            )
        elif t == AvatarType.RIGID_SPHERE:
            body = pre.rigidSphere(
                r=float(av.radius), center=center, model=mod, material=mat,
                color=color, is_Hollow=bool(av.is_hollow),
            )
        elif t == AvatarType.RIGID_JONC:
            ax = av.axis or {}
            body = pre.rigidJonc(
                axe1=float(ax["axe1"]), axe2=float(ax["axe2"]),
                center=center, model=mod, material=mat, color=color,
            )
        elif t == AvatarType.RIGID_POLYGON:
            kwargs: dict[str, Any] = dict(
                center=center, model=mod, material=mat, color=color,
            )
            if av.generation_type:
                kwargs["generation_type"] = av.generation_type
            if av.nb_vertices is not None:
                kwargs["nb_vertices"] = av.nb_vertices
            if av.radius is not None:
                kwargs["radius"] = float(av.radius)
            if av.vertices is not None:
                kwargs["vertices"] = av.vertices
            body = pre.rigidPolygon(**kwargs)
        elif t == AvatarType.RIGID_OVOID:
            # stored; constructor name may vary by pylmgc version
            fn = getattr(pre, "rigidOvoidPolygon", None) or getattr(pre, "rigidOvoid", None)
            if fn is None:
                raise MaterializationError("pylmgc90 has no rigidOvoid* constructor")
            kwargs = dict(center=center, model=mod, material=mat, color=color)
            if av.radius is not None:
                kwargs["radius"] = float(av.radius)
            if av.vertices is not None:
                kwargs["vertices"] = av.vertices
            body = fn(**kwargs)
        elif t == AvatarType.RIGID_DISCRETE:
            body = pre.rigidDiscreteDisk(
                r=float(av.radius), center=center, model=mod, material=mat, color=color,
            )
        elif t == AvatarType.RIGID_CLUSTER:
            nb = (av.wall_params or {}).get("nb_disk", 3)
            body = pre.rigidCluster(
                r=float(av.radius or 0.05), center=center, model=mod, material=mat,
                color=color, nb_disk=int(nb),
            )
        elif t == AvatarType.RIGID_CYLINDER:
            h = (av.wall_params or {}).get("h", 1.0)
            body = pre.rigidCylinder(
                r=float(av.radius), h=float(h), center=center,
                model=mod, material=mat, color=color,
            )
        elif t == AvatarType.RIGID_PLAN:
            ax = av.axis or av.wall_params or {}
            body = pre.rigidPlan(
                axe1=float(ax.get("axe1", 1.0)),
                axe2=float(ax.get("axe2", 1.0)),
                center=center, model=mod, material=mat, color=color,
            )
        elif t == AvatarType.RIGID_POLYHEDRON:
            kwargs = dict(center=center, model=mod, material=mat, color=color)
            if av.vertices is not None:
                kwargs["vertices"] = av.vertices
            if av.radius is not None:
                kwargs["radius"] = float(av.radius)
            body = pre.rigidPolyhedron(**kwargs)
        elif t in (
            AvatarType.SMOOTH_WALL, AvatarType.FINE_WALL, AvatarType.ROUGH_WALL,
            AvatarType.GRANULO_WALL,
        ):
            body = _build_wall_2d(pre, av, mat, mod)
        elif t in (AvatarType.ROUGH_WALL_3D, AvatarType.GRANULO_ROUGH_WALL_3D):
            body = _build_wall_3d(pre, av, mat, mod)
        elif t == AvatarType.MESH_DEFORMABLE:
            body = _build_mesh(pre, av, mat, mod)
        elif t == AvatarType.EMPTY_AVATAR:
            body = pre.emptyAvatar(model=mod, material=mat)
        else:
            raise MaterializationError(f"unsupported avatar type: {t}")
    except MaterializationError:
        raise
    except Exception as exc:
        raise MaterializationError(
            f"failed to build {t.value} avatar_id={av.avatar_id}: {exc}"
        ) from exc

    _apply_contactors(body, av)
    return body


def _build_wall_2d(pre, av: Avatar, mat, mod) -> Any:
    wp = av.wall_params or {}
    t = av.avatar_type
    center = list(av.center)
    color = av.color
    common = dict(center=center, model=mod, material=mat, color=color)

    if t == AvatarType.SMOOTH_WALL:
        return pre.smoothWall(
            l=float(wp.get("l", 1.0)), h=float(wp.get("h", 0.1)),
            nb_polyg=int(wp.get("nb_polyg", 24)), **common,
        )
    if t == AvatarType.FINE_WALL:
        return pre.fineWall(
            l=float(wp.get("l", 1.0)), h=float(wp.get("h", 0.1)),
            rmin=float(wp.get("rmin", 0.01)), rmax=float(wp.get("rmax", 0.02)),
            **common,
        )
    if t == AvatarType.ROUGH_WALL:
        return pre.roughWall(
            l=float(wp.get("l", 1.0)), h=float(wp.get("h", 0.1)),
            rmin=float(wp.get("rmin", 0.01)), rmax=float(wp.get("rmax", 0.02)),
            nb_vertex=int(wp.get("nb_vertex", 10)), **common,
        )
    # GRANULO_WALL
    fn = getattr(pre, "granuloRoughWall", None)
    if fn is None:
        raise MaterializationError("pylmgc90 has no granuloRoughWall")
    return fn(
        l=float(wp.get("l", 1.0)), h=float(wp.get("h", 0.1)),
        rmin=float(wp.get("rmin", 0.01)), rmax=float(wp.get("rmax", 0.02)),
        **common,
    )


def _build_wall_3d(pre, av: Avatar, mat, mod) -> Any:
    wp = av.wall_params or {}
    center = list(av.center)
    color = av.color
    common = dict(center=center, model=mod, material=mat, color=color)
    if av.avatar_type == AvatarType.ROUGH_WALL_3D:
        fn = getattr(pre, "roughWall3D", None)
        if fn is None:
            raise MaterializationError("pylmgc90 has no roughWall3D")
        return fn(
            lx=float(wp.get("lx", 1.0)), ly=float(wp.get("ly", 1.0)),
            lz=float(wp.get("lz", 0.1)), **common,
        )
    fn = getattr(pre, "granuloRoughWall3D", None)
    if fn is None:
        raise MaterializationError("pylmgc90 has no granuloRoughWall3D")
    return fn(
        lx=float(wp.get("lx", 1.0)), ly=float(wp.get("ly", 1.0)),
        lz=float(wp.get("lz", 0.1)),
        rmin=float(wp.get("rmin", 0.01)), rmax=float(wp.get("rmax", 0.02)),
        **common,
    )


def _build_mesh(pre, av: Avatar, mat, mod) -> Any:
    """Mesh / deformable — relies on mesh_params already filled by the caller."""
    mp = av.mesh_params or {}
    # Common path: pre.buildMeshedAvatar or equivalent depending on version.
    # We support the rectangle helper path used by core examples.
    if mp.get("kind") == "meshed_rectangle" or "lx" in mp:
        fn = getattr(pre, "meshed_rectangle", None) or getattr(pre, "buildMeshedAvatar", None)
        if fn is None:
            raise MaterializationError(
                "mesh avatar requires mesh_params with a supported builder; "
                "pylmgc90 has no meshed_rectangle/buildMeshedAvatar in this install"
            )
        kwargs = {
            "lx": float(mp.get("lx", 1.0)),
            "ly": float(mp.get("ly", 1.0)),
            "nx": int(mp.get("nx", 2)),
            "ny": int(mp.get("ny", 2)),
            "center": list(av.center),
            "model": mod,
            "material": mat,
            "color": av.color,
        }
        if "mesh_type" in mp:
            kwargs["mesh_type"] = mp["mesh_type"]
        return fn(**kwargs)
    raise MaterializationError(
        f"MESH_DEFORMABLE avatar_id={av.avatar_id}: unsupported mesh_params keys {list(mp)}"
    )


def _apply_contactors(body: Any, av: Avatar) -> None:
    for c in av.contactors or []:
        shape = c.get("shape")
        if not shape:
            continue
        kwargs = {k: v for k, v in c.items() if k != "shape"}
        try:
            body.addContactors(shape=shape, **kwargs)
        except TypeError:
            # older API: positional or different kw
            body.addContactors(shape, **kwargs)


def build_population_bodies(
    pop: ParticlePopulation,
    *,
    materials: dict[str, Any],
    models: dict[str, Any],
) -> list[Any]:
    """Expand a SoA population into a list of pre bodies (one per particle)."""
    pre = _pre()
    mat = _resolve(pop.material_name, materials, "material")
    mod = _resolve(pop.model_name, models, "model")
    color = pop.color
    t = pop.avatar_type
    extra = dict(pop.extra_params or {})

    fn_map = {
        AvatarType.RIGID_DISK: "rigidDisk",
        AvatarType.RIGID_SPHERE: "rigidSphere",
        AvatarType.RIGID_DISCRETE: "rigidDiscreteDisk",
        AvatarType.RIGID_CLUSTER: "rigidCluster",
        AvatarType.RIGID_CYLINDER: "rigidCylinder",
        AvatarType.RIGID_POLYGON: "rigidPolygon",
        AvatarType.RIGID_POLYHEDRON: "rigidPolyhedron",
    }
    fn_name = fn_map.get(t)
    if fn_name is None:
        raise MaterializationError(f"population type not supported: {t}")
    fn = getattr(pre, fn_name, None)
    if fn is None:
        raise MaterializationError(f"pylmgc90 has no {fn_name}")

    bodies: list[Any] = []
    n = len(pop)
    centers = pop.centers
    radii = pop.radii
    for i in range(n):
        center = centers[i].tolist() if hasattr(centers[i], "tolist") else list(centers[i])
        r = float(radii[i])
        kwargs: dict[str, Any] = dict(
            r=r, center=center, model=mod, material=mat, color=color,
        )
        if t == AvatarType.RIGID_CLUSTER:
            kwargs["nb_disk"] = int(extra.get("nb_disk", 3))
        if t == AvatarType.RIGID_CYLINDER:
            kwargs["h"] = float(extra.get("h", 1.0))
        if t in (AvatarType.RIGID_POLYGON, AvatarType.RIGID_POLYHEDRON):
            # radius already set; optional gen
            if "generation_type" in extra:
                kwargs["generation_type"] = extra["generation_type"]
            if "nb_vertices" in extra:
                kwargs["nb_vertices"] = int(extra["nb_vertices"])
        try:
            bodies.append(fn(**kwargs))
        except Exception as exc:
            raise MaterializationError(
                f"population {pop.population_id} particle {i}: {exc}"
            ) from exc
    return bodies
