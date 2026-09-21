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
        from lmgc90_core.numpy_compat import patch_numpy_cross
        patch_numpy_cross()
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
            kwargs = dict(
                r=float(av.radius), center=center, model=mod, material=mat, color=color,
            )
            import inspect
            try:
                if "is_Hollow" in inspect.signature(pre.rigidDisk).parameters:
                    kwargs["is_Hollow"] = bool(av.is_hollow)
            except (TypeError, ValueError):
                pass
            body = pre.rigidDisk(**kwargs)
        elif t == AvatarType.RIGID_SPHERE:
            # pylmgc90.pre.rigidSphere does not accept is_Hollow
            body = pre.rigidSphere(
                r=float(av.radius), center=center, model=mod, material=mat,
                color=color,
            )
        elif t == AvatarType.RIGID_JONC:
            ax = av.axis or {}
            body = pre.rigidJonc(
                axe1=float(ax["axe1"]), axe2=float(ax["axe2"]),
                center=center, model=mod, material=mat, color=color,
            )
        elif t == AvatarType.RIGID_POLYGON:
            import numpy as np
            kwargs: dict[str, Any] = dict(
                center=center, model=mod, material=mat, color=color,
            )
            if av.vertices is not None:
                verts = np.asarray(av.vertices, dtype=float)
                # Custom outline: do NOT pass generation_type="vertices" (invalid in pylmgc)
                try:
                    body = pre.rigidPolygon(vertices=verts, **kwargs)
                except TypeError:
                    try:
                        body = pre.rigidPolygon(
                            generation_type="full", vertices=verts, **kwargs
                        )
                    except Exception:
                        # last resort: regular with radius from bbox
                        xs, ys = verts[:, 0], verts[:, 1]
                        r = 0.5 * max(xs.max() - xs.min(), ys.max() - ys.min())
                        body = pre.rigidPolygon(
                            generation_type="regular",
                            nb_vertices=max(3, len(verts)),
                            radius=float(r),
                            **kwargs,
                        )
            else:
                kwargs["generation_type"] = av.generation_type or "regular"
                kwargs["nb_vertices"] = int(av.nb_vertices or 6)
                kwargs["radius"] = float(av.radius or 0.1)
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
            kwargs = dict(
                r=float(av.radius), h=float(h), center=center,
                model=mod, material=mat, color=color,
            )
            import inspect
            try:
                if "is_Hollow" in inspect.signature(pre.rigidCylinder).parameters:
                    kwargs["is_Hollow"] = bool(av.is_hollow)
            except (TypeError, ValueError):
                pass
            body = pre.rigidCylinder(**kwargs)
        elif t == AvatarType.RIGID_PLAN:
            ax = av.axis or av.wall_params or {}
            body = pre.rigidPlan(
                axe1=float(ax.get("axe1", 1.0)),
                axe2=float(ax.get("axe2", 1.0)),
                axe3=float(ax.get("axe3", 0.05)),
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
            body = _build_empty_or_brick(pre, av, mat, mod)
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


def _build_empty_or_brick(pre, av: Avatar, mat, mod) -> Any:
    """Brick via ``pre.brick2D(...).rigidBrick`` (MVC), never bare emptyAvatar.

    ``pylmgc90.pre`` often has **no** ``emptyAvatar`` attribute — bricks must go
    through brick2D. Falls back to a rectangular ``rigidPolygon`` if brick2D
    is unavailable.
    """
    import numpy as np

    wp = av.wall_params or {}
    lx = wp.get("l") if wp.get("l") is not None else wp.get("lx")
    ly = wp.get("h") if wp.get("h") is not None else wp.get("ly")
    brick_name = str(wp.get("brick_name", "std"))
    center = list(av.center)
    color = av.color

    def _resolve_brick2d():
        for obj in (pre, getattr(pre, "avatars", None), getattr(pre, "rigid", None)):
            if obj is None:
                continue
            fn = getattr(obj, "brick2D", None)
            if callable(fn):
                return fn
        # some installs export brick2D at package root
        try:
            import pylmgc90.pre as pre_mod  # type: ignore
            fn = getattr(pre_mod, "brick2D", None)
            if callable(fn):
                return fn
        except Exception:
            pass
        return None

    if lx is not None and ly is not None:
        lx, ly = float(lx), float(ly)
        brick2d = _resolve_brick2d()
        if brick2d is not None:
            brick = brick2d(brick_name, lx, ly)
            rigid = getattr(brick, "rigidBrick", None)
            if rigid is None:
                raise MaterializationError(
                    "brick2D object has no rigidBrick() — check pylmgc90 version"
                )
            try:
                return rigid(center=center, model=mod, material=mat, color=color)
            except TypeError:
                return rigid(center, mod, mat, color)

        # Fallback: rectangular polygon (still POLYG-capable)
        hx, hy = lx / 2.0, ly / 2.0
        cx, cy = float(center[0]), float(center[1])
        verts = np.array([
            [cx - hx, cy - hy],
            [cx + hx, cy - hy],
            [cx + hx, cy + hy],
            [cx - hx, cy + hy],
        ], dtype=float)
        try:
            return pre.rigidPolygon(
                center=center, model=mod, material=mat, color=color, vertices=verts,
            )
        except TypeError:
            return pre.rigidPolygon(
                center=center, model=mod, material=mat, color=color,
                generation_type="full", vertices=verts,
            )

    # Generic empty body if API exists
    for name in ("emptyAvatar", "EmptyAvatar", "avatar"):
        fn = getattr(pre, name, None)
        if callable(fn):
            try:
                return fn(model=mod, material=mat)
            except TypeError:
                try:
                    return fn(mod, mat)
                except Exception:
                    continue
    raise MaterializationError(
        "cannot build EMPTY_AVATAR: no brick2D/rigidBrick and no emptyAvatar in pylmgc90.pre; "
        "set wall_params l/h (brick size) for masonry bricks"
    )



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
        # pylmgc90 / core pre.roughWall(l, r, center, ...): r = thickness
        return pre.roughWall(
            l=float(wp.get("l", 1.0)),
            r=float(wp.get("r", wp.get("h", 0.03))),
            nb_vertex=int(wp.get("nb_vertex", 10)),
            **common,
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
    """Build deformable body the pylmgc90 way: buildMesh2D → buildMeshedAvatar.

    Official pattern (same as ``pre_script`` and MVC examples)::

        mesh = pre.buildMesh2D("2T3", x0, y0, lx, ly, nx, ny)
        body = pre.buildMeshedAvatar(mesh=mesh, model=mod, material=mat)
    """
    mp = av.mesh_params or {}
    geom = mp.get("geom") or ("Rectangle" if "lx" in mp else None)
    build_mesh = getattr(pre, "buildMesh2D", None)
    build_avatar = getattr(pre, "buildMeshedAvatar", None)
    if build_mesh is None or build_avatar is None:
        raise MaterializationError(
            "pylmgc90.pre needs buildMesh2D and buildMeshedAvatar for MESH_DEFORMABLE"
        )

    if geom in (None, "Rectangle") and "lx" in mp:
        lx = float(mp["lx"])
        ly = float(mp["ly"])
        nx = int(mp.get("nx", 2))
        ny = int(mp.get("ny", 2))
        mesh_type = mp.get("mesh_type", "2T3")
        # prefer explicit cx/cy from mesh_params, else avatar centre
        cx = float(mp["cx"]) if "cx" in mp else float(av.center[0])
        cy = float(mp["cy"]) if "cy" in mp else float(av.center[1])
        x0 = cx - lx / 2.0
        y0 = cy - ly / 2.0
        mesh = build_mesh(mesh_type, x0, y0, lx, ly, nx, ny)
        try:
            body = build_avatar(mesh=mesh, model=mod, material=mat)
        except TypeError:
            body = build_avatar(mesh, mod, mat)
        return body

    if geom in ("Boîte (H8)", "Box3D", "H8") or ("lz" in mp and "lx" in mp):
        build_h8 = getattr(pre, "buildMeshH8", None)
        if build_h8 is None:
            raise MaterializationError("pylmgc90.pre has no buildMeshH8")
        lx, ly, lz = float(mp["lx"]), float(mp["ly"]), float(mp["lz"])
        nx, ny, nz = int(mp.get("nx", 2)), int(mp.get("ny", 2)), int(mp.get("nz", 2))
        cx = float(mp.get("cx", av.center[0]))
        cy = float(mp.get("cy", av.center[1] if len(av.center) > 1 else 0.0))
        cz = float(mp.get("cz", av.center[2] if len(av.center) > 2 else 0.0))
        mesh = build_h8(cx - lx / 2, cy - ly / 2, cz - lz / 2, lx, ly, lz, nx, ny, nz)
        try:
            return build_avatar(mesh=mesh, model=mod, material=mat)
        except TypeError:
            return build_avatar(mesh, mod, mat)

    if geom in ("Fichier externe", "file") or mp.get("filepath"):
        read_mesh = getattr(pre, "readMesh", None)
        if read_mesh is None:
            raise MaterializationError("pylmgc90.pre has no readMesh")
        mesh = read_mesh(mp.get("filepath"), int(mp.get("dim", 2)))
        try:
            return build_avatar(mesh=mesh, model=mod, material=mat)
        except TypeError:
            return build_avatar(mesh, mod, mat)

    raise MaterializationError(
        f"MESH_DEFORMABLE avatar_id={av.avatar_id}: unsupported mesh_params keys {list(mp)}"
    )


def _apply_contactors(body: Any, av: Avatar) -> None:
    """Attach contactors listed on the core Avatar.

    Skip incomplete POLYG (needs nb_vertices/vertices): brick2D.rigidBrick and
    rigidPolygon already register a full POLYG contactor on the live body.
    Re-adding a bare ``{'shape': 'POLYG'}`` triggers pylmgc
    "Incomplete contactor".
    """
    for c in av.contactors or []:
        shape = c.get("shape")
        if not shape:
            continue
        if str(shape).upper() in ("POLYG", "POLYGX", "POLY"):
            params = c.get("params") or {}
            has_verts = (
                c.get("vertices") is not None
                or params.get("vertices") is not None
                or c.get("nb_vertices") is not None
                or params.get("nb_vertices") is not None
            )
            if not has_verts:
                continue  # geometry already on body (brick / polygon)
        kwargs = {k: v for k, v in c.items() if k not in ("shape", "params")}
        if isinstance(c.get("params"), dict):
            kwargs.update(c["params"])
        try:
            body.addContactors(shape=shape, **kwargs)
        except TypeError:
            try:
                body.addContactors(shape, **kwargs)
            except Exception:
                # do not abort materialize for optional contactor glue
                pass


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
