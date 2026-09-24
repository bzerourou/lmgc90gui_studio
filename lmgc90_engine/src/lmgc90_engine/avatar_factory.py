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



def expand_rigids_from_mesh2d(
    av: Avatar,
    *,
    materials: dict[str, Any],
    models: dict[str, Any],
) -> list[Any]:
    """``pre.rigidsFromMesh2D`` — one rigid POLYG per surface element (gen_sample)."""
    pre = _pre()
    mp = av.mesh_params or {}
    raw = mp.get("filepath") or mp.get("file")
    if not raw:
        raise MaterializationError("rigidsFromMesh2D: filepath missing")
    dim = int(mp.get("dim", 2))
    path = resolve_mesh_filepath(str(raw), dim=dim, mesh_size=mp.get("mesh_size"))
    read_mesh = getattr(pre, "readMesh", None)
    expand = getattr(pre, "rigidsFromMesh2D", None)
    if read_mesh is None or expand is None:
        raise MaterializationError(
            "pylmgc90.pre needs readMesh and rigidsFromMesh2D"
        )
    mesh = read_mesh(path, dim)
    mat = _resolve(av.material_name, materials, "material")
    mod = _resolve(av.model_name, models, "model")
    color = av.color or "BLEUx"
    try:
        result = expand(surfacic_mesh=mesh, model=mod, material=mat, color=color)
    except TypeError:
        result = expand(mesh, mod, mat, color)
    # result may be avatars container or list
    out: list[Any] = []
    if result is None:
        return out
    if hasattr(result, "__iter__") and not hasattr(result, "contactors"):
        try:
            out = list(result)
        except TypeError:
            out = [result]
    else:
        out = [result]
    return out


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
            ax = dict(av.axis or {})
            if not ax and av.wall_params:
                ax = dict(av.wall_params)
            body = pre.rigidJonc(
                axe1=float(ax.get("axe1", 0.5)),
                axe2=float(ax.get("axe2", 0.05)),
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



def resolve_mesh_filepath(filepath: str, *, dim: int = 2, mesh_size: float | None = None) -> str:
    """Return a path readable by ``pre.readMesh``.

    * ``.msh`` / ``.vtk`` — used as-is
    * ``.brep`` / ``.step`` / ``.iges`` — meshed with **gmsh** (optional dep) to a
      sibling ``.msh`` file next to the CAD file
    """
    from pathlib import Path as _P
    p = _P(filepath).expanduser()
    if not p.is_file():
        raise MaterializationError(f"mesh file not found: {filepath}")
    suf = p.suffix.lower()
    if suf in (".msh", ".vtk", ".vtu", ".mesh"):
        return str(p.resolve())
    if suf in (".brep", ".brp", ".step", ".stp", ".iges", ".igs", ".geo"):
        out = p.with_suffix(".msh")
        # regenerate if missing or older than CAD
        need = (not out.is_file()) or (out.stat().st_mtime < p.stat().st_mtime)
        if need:
            try:
                import gmsh  # type: ignore
            except ImportError as exc:
                raise MaterializationError(
                    f"Import de {suf} nécessite le paquet Python « gmsh » "
                    f"(pip install gmsh). Fichier: {p.name}"
                ) from exc
            try:
                gmsh.initialize()
                gmsh.model.add("lmgc90_studio")
                try:
                    gmsh.model.occ.importShapes(str(p))
                    gmsh.model.occ.synchronize()
                except Exception:
                    # .geo or legacy
                    gmsh.open(str(p))
                if mesh_size is not None and float(mesh_size) > 0:
                    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", float(mesh_size))
                    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", float(mesh_size) * 0.2)
                # 2D surface mesh or 3D volume
                dim_gen = 2 if int(dim) == 2 else 3
                gmsh.model.mesh.generate(dim_gen)
                gmsh.write(str(out))
            except Exception as exc:
                try:
                    gmsh.finalize()
                except Exception:
                    pass
                raise MaterializationError(
                    f"gmsh a échoué sur {p.name}: {exc}"
                ) from exc
            try:
                gmsh.finalize()
            except Exception:
                pass
        if not out.is_file():
            raise MaterializationError(f"gmsh n'a pas produit {out.name}")
        return str(out.resolve())
    raise MaterializationError(
        f"format maillage non supporté: {suf} "
        f"(acceptés: .msh .vtk .brep .step .iges .geo)"
    )


def _build_mesh(pre, av: Avatar, mat, mod) -> Any:
    """Build deformable body the pylmgc90 way: buildMesh2D → buildMeshedAvatar.

    Official pattern (same as ``pre_script`` and MVC examples)::

        mesh = pre.buildMesh2D("2T3", x0, y0, lx, ly, nx, ny)
        body = pre.buildMeshedAvatar(mesh=mesh, model=mod, material=mat)
    """
    mp = av.mesh_params or {}

    # --- brick2D.deformableBrick (masonry gen_sample) ---
    if (
        str(mp.get("geom", "")).lower() in ("deformablebrick", "deformable_brick", "brick")
        or mp.get("source") == "deformableBrick"
        or "brick_lx" in mp
    ):
        brick2d = None
        for obj in (pre, getattr(pre, "avatars", None)):
            if obj is None:
                continue
            fn = getattr(obj, "brick2D", None)
            if callable(fn):
                brick2d = fn
                break
        if brick2d is None:
            raise MaterializationError("pylmgc90.pre has no brick2D for deformableBrick")
        blx = float(mp.get("brick_lx") or mp.get("lx") or 0.1)
        bly = float(mp.get("brick_ly") or mp.get("ly") or 0.05)
        bname = str(mp.get("brick_name", "brique"))
        brick = brick2d(bname, blx, bly)
        deform = getattr(brick, "deformableBrick", None)
        if deform is None:
            raise MaterializationError("brick2D has no deformableBrick()")
        center = list(av.center)
        nb_elem_x = int(mp.get("nb_elem_x", mp.get("nx", 2)))
        nb_elem_y = int(mp.get("nb_elem_y", mp.get("ny", 2)))
        mesh_type = str(mp.get("mesh_type", "Q4"))
        apabh = mp.get("apabh") or mp.get("apab_brick") or [0.25, 0.75]
        apabv = mp.get("apabv") or mp.get("apab_brick") or [0.25, 0.75]
        colors = mp.get("colors")  # optional face colors list
        kwargs = dict(
            center=center, material=mat, model=mod,
            mesh_type=mesh_type, nb_elem_x=nb_elem_x, nb_elem_y=nb_elem_y,
            apabh=apabh, apabv=apabv,
        )
        if colors is not None:
            kwargs["colors"] = colors
        try:
            body = deform(**kwargs)
        except TypeError:
            # older signature without colors
            kwargs.pop("colors", None)
            body = deform(**kwargs)
        return body

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
        raw_path = mp.get("filepath") or mp.get("file")
        if not raw_path:
            raise MaterializationError("MESH_DEFORMABLE: filepath manquant")
        dim_m = int(mp.get("dim", getattr(av, "dimension", None) or 2))
        # prefer project dimension if stored on mesh_params
        mesh_size = mp.get("mesh_size") or mp.get("lc")
        try:
            mesh_size_f = float(mesh_size) if mesh_size is not None else None
        except (TypeError, ValueError):
            mesh_size_f = None
        resolved = resolve_mesh_filepath(
            str(raw_path), dim=dim_m, mesh_size=mesh_size_f,
        )
        try:
            mesh = read_mesh(resolved, dim_m)
        except TypeError:
            mesh = read_mesh(resolved)
        try:
            return build_avatar(mesh=mesh, model=mod, material=mat)
        except TypeError:
            return build_avatar(mesh, mod, mat)

    raise MaterializationError(
        f"MESH_DEFORMABLE avatar_id={av.avatar_id}: unsupported mesh_params keys {list(mp)}"
    )


def _apply_contactors(body: Any, av: Avatar) -> None:
    """Attach contactors listed on the core Avatar.

    Skip incomplete POLYG / JONCx / DNLYC already created by constructors.
    Meshed contactors (CLxxx, ALpxx, …) need a coherent *group* of elements;
    failures are swallowed so materialize / visuAvatars still succeed.
    """
    _MESH_SHAPES = {
        "CLXXX", "ALPXX", "CSPXX", "ASPXX", "PT2DX", "PT3DX", "CL3xx", "AS3xx",
    }
    _ALLOWED_MESH_KW = {
        "group", "color", "weights", "reverse", "byrd", "shift", "quadrature",
    }
    _ALLOWED_RIGID_KW = {
        "color", "byrd", "shift", "axe1", "axe2", "axe3", "nb_vertices",
        "vertices", "r", "radius", "reverse",
    }

    for c in av.contactors or []:
        shape = c.get("shape")
        if not shape:
            continue
        sh = str(shape).upper()
        params = c.get("params") if isinstance(c.get("params"), dict) else {}

        if sh in ("POLYG", "POLYGX", "POLY"):
            has_verts = (
                c.get("vertices") is not None
                or params.get("vertices") is not None
                or c.get("nb_vertices") is not None
                or params.get("nb_vertices") is not None
            )
            if not has_verts:
                continue
        if sh in ("JONCX", "JONC"):
            has_axes = (
                c.get("axe1") is not None
                or params.get("axe1") is not None
                or c.get("axe2") is not None
                or params.get("axe2") is not None
            )
            if not has_axes:
                continue
        if sh in ("DNLYC", "CYLND") and set(c.keys()) <= {"shape", "color", "params"}:
            if not params:
                continue
        if sh in ("DISKX", "SPHER", "XKSID") and c.get("byrd") is None and params.get("byrd") is None:
            if set(c.keys()) <= {"shape", "color", "params"} and not params:
                continue

        raw = {k: v for k, v in c.items() if k not in ("shape", "params")}
        raw.update(params)

        is_mesh = sh in _MESH_SHAPES
        if is_mesh:
            # only keys understood by meshedContactor; drop junk that breaks element lists
            kwargs = {k: v for k, v in raw.items() if k in _ALLOWED_MESH_KW}
            # group required for CLxxx/ALpxx on meshed avatars
            if "group" not in kwargs or not kwargs.get("group"):
                # try common boundary names as last resort
                for gname in ("up", "down", "left", "right", "top", "bottom", "all"):
                    try:
                        body.addContactors(shape=shape, group=gname, **{
                            k: v for k, v in kwargs.items() if k != "group"
                        })
                        break
                    except Exception:
                        continue
                continue
        else:
            kwargs = {k: v for k, v in raw.items() if k in _ALLOWED_RIGID_KW or k in raw}

        try:
            body.addContactors(shape=shape, **kwargs)
        except Exception:
            try:
                body.addContactors(shape=shape, **{
                    k: v for k, v in kwargs.items() if k in ("group", "color")
                })
            except Exception:
                # never abort materialize for contactor glue
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
