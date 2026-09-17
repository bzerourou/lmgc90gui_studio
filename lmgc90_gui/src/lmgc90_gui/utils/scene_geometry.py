"""Extract displayable geometry from a Project — pure numpy, no Qt/pyvista.

Used by the 2D schematic viewer and by the optional PyVista 3D viewer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from lmgc90_core import Avatar, ParticlePopulation, Project
from lmgc90_core.types import AvatarType


# crude colour map (LMGC90-ish names → RGB 0-255)
_COLORS = {
    "BLUEx": (66, 135, 245),
    "REEDx": (220, 60, 60),
    "GRAYx": (140, 140, 140),
    "CYANx": (40, 200, 200),
    "GREENx": (60, 180, 80),
    "YELLO": (230, 200, 40),
    "ORANG": (240, 140, 40),
    "WHITEx": (230, 230, 230),
    "BLACKx": (30, 30, 30),
}


@dataclass
class DiscGeom:
    center: Tuple[float, ...]
    radius: float
    color: Tuple[int, int, int]
    label: str
    source: str  # "avatar" | "population"
    avatar_id: str = ""


@dataclass
class SegmentGeom:
    p0: Tuple[float, ...]
    p1: Tuple[float, ...]
    color: Tuple[int, int, int]
    label: str
    avatar_id: str = ""


@dataclass
class PolygonGeom:
    points: List[Tuple[float, ...]]
    color: Tuple[int, int, int]
    label: str
    avatar_id: str = ""
    filled: bool = True


@dataclass
class SceneGeometry:
    discs: List[DiscGeom] = field(default_factory=list)
    segments: List[SegmentGeom] = field(default_factory=list)
    polygons: List[PolygonGeom] = field(default_factory=list)
    dimension: int = 2
    bounds: Optional[Tuple[np.ndarray, np.ndarray]] = None
    n_avatars: int = 0
    n_population_particles: int = 0

    @property
    def n_items(self) -> int:
        return len(self.discs) + len(self.segments) + len(self.polygons)


def color_rgb(name: str) -> Tuple[int, int, int]:
    if not name:
        return (66, 135, 245)
    key = name.strip()
    if key in _COLORS:
        return _COLORS[key]
    # partial match
    for k, v in _COLORS.items():
        if k.startswith(key[:4]):
            return v
    return (66, 135, 245)


def _as_tuple(center: Sequence[float], dim: int) -> Tuple[float, ...]:
    c = list(center)
    while len(c) < dim:
        c.append(0.0)
    return tuple(float(x) for x in c[:dim])


def avatar_to_geoms(
    av: Avatar, dim: int,
) -> Tuple[List[DiscGeom], List[SegmentGeom], List["PolygonGeom"]]:
    discs: List[DiscGeom] = []
    segs: List[SegmentGeom] = []
    polys: List[PolygonGeom] = []
    col = color_rgb(av.color)
    label = f"{av.avatar_type.value}"
    aid = av.avatar_id
    c = _as_tuple(av.center, dim)
    at = av.avatar_type
    r = float(av.radius or 0.0)

    if at in (
        AvatarType.RIGID_DISK, AvatarType.RIGID_SPHERE, AvatarType.RIGID_DISCRETE,
        AvatarType.RIGID_CLUSTER, AvatarType.RIGID_CYLINDER,
    ):
        if r <= 0:
            r = 0.05
        discs.append(DiscGeom(c, r, col, label, "avatar", aid))
    elif at in (AvatarType.RIGID_POLYGON, AvatarType.RIGID_OVOID, AvatarType.RIGID_POLYHEDRON):
        if r > 0:
            discs.append(DiscGeom(c, r, col, label, "avatar", aid))
        elif av.vertices and len(av.vertices) >= 2:
            verts = [_as_tuple(v, dim) for v in av.vertices]
            for i in range(len(verts)):
                segs.append(SegmentGeom(verts[i], verts[(i + 1) % len(verts)], col, label, aid))
        else:
            discs.append(DiscGeom(c, 0.05, col, label, "avatar", aid))
    elif at == AvatarType.RIGID_JONC:
        # JONCx = rectangle 2*axe1 × 2*axe2 (LMGC90 convention), centered
        ax = av.axis or {}
        a1 = float(ax.get("axe1", 0.1) or 0.1)
        a2 = float(ax.get("axe2", 0.02) or 0.02)
        if a1 <= 0:
            a1 = 0.1
        if a2 <= 0:
            a2 = 0.02
        z = (c[2],) if dim >= 3 and len(c) > 2 else ()
        corners = [
            (c[0] - a1, c[1] - a2) + z,
            (c[0] + a1, c[1] - a2) + z,
            (c[0] + a1, c[1] + a2) + z,
            (c[0] - a1, c[1] + a2) + z,
        ]
        polys.append(PolygonGeom([_as_tuple(p, dim) for p in corners], col, label, aid, True))
        for i in range(4):
            segs.append(SegmentGeom(
                _as_tuple(corners[i], dim),
                _as_tuple(corners[(i + 1) % 4], dim),
                col, label, aid,
            ))
    elif at in (
        AvatarType.SMOOTH_WALL, AvatarType.ROUGH_WALL, AvatarType.FINE_WALL,
        AvatarType.GRANULO_WALL,
    ):
        wp = av.wall_params or {}
        L = float(wp.get("l", 1.0))
        h = float(wp.get("h", wp.get("r", 0.05)))
        p0 = list(c); p1 = list(c)
        p0[0] -= L / 2; p1[0] += L / 2
        segs.append(SegmentGeom(tuple(p0), tuple(p1), col, label, aid))
        # thickness markers
        discs.append(DiscGeom(c, max(h, 0.01), col, label, "avatar", aid))
    elif at in (AvatarType.ROUGH_WALL_3D, AvatarType.GRANULO_ROUGH_WALL_3D, AvatarType.RIGID_PLAN):
        discs.append(DiscGeom(c, 0.1, col, label, "avatar", aid))
    elif at == AvatarType.MESH_DEFORMABLE:
        mp = av.mesh_params or {}
        lx = float(mp.get("lx", 0.1)); ly = float(mp.get("ly", 0.1))
        x0, y0 = c[0] - lx / 2, c[1] - ly / 2
        corners = [
            (x0, y0) + ((c[2],) if dim == 3 else ()),
            (x0 + lx, y0) + ((c[2],) if dim == 3 else ()),
            (x0 + lx, y0 + ly) + ((c[2],) if dim == 3 else ()),
            (x0, y0 + ly) + ((c[2],) if dim == 3 else ()),
        ]
        for i in range(4):
            segs.append(SegmentGeom(
                _as_tuple(corners[i], dim),
                _as_tuple(corners[(i + 1) % 4], dim),
                col, label, aid,
            ))
    elif at == AvatarType.EMPTY_AVATAR:
        # Marker cross + optional contactor shapes
        mark = max(r, 0.03)
        segs.append(SegmentGeom(
            _as_tuple([c[0] - mark, c[1]], dim),
            _as_tuple([c[0] + mark, c[1]], dim),
            col, label, aid,
        ))
        segs.append(SegmentGeom(
            _as_tuple([c[0], c[1] - mark], dim),
            _as_tuple([c[0], c[1] + mark], dim),
            col, label, aid,
        ))
        discs.append(DiscGeom(c, mark * 0.35, col, label, "avatar", aid))
        for ct in (av.contactors or []):
            shape = (ct.get("shape") or ct.get("type") or "").upper()
            params = ct.get("params") or ct
            ccol = color_rgb(ct.get("color") or av.color)
            if shape in ("DISKX", "DISKx", "SPHER"):
                rr = float(params.get("r") or params.get("radius") or 0.05)
                discs.append(DiscGeom(c, rr, ccol, f"{label}/{shape}", "avatar", aid))
            elif shape in ("JONCX", "JONCx"):
                a1 = float(params.get("axe1") or 0.1)
                a2 = float(params.get("axe2") or 0.02)
                z = (c[2],) if dim >= 3 and len(c) > 2 else ()
                corners = [
                    (c[0] - a1, c[1] - a2) + z,
                    (c[0] + a1, c[1] - a2) + z,
                    (c[0] + a1, c[1] + a2) + z,
                    (c[0] - a1, c[1] + a2) + z,
                ]
                polys.append(PolygonGeom(
                    [_as_tuple(p, dim) for p in corners], ccol, f"{label}/{shape}", aid, False,
                ))
    else:
        discs.append(DiscGeom(c, max(r, 0.02), col, label, "avatar", aid))
    return discs, segs, polys


def build_scene_geometry(
    project: Project,
    *,
    max_population_preview: int = 5000,
) -> SceneGeometry:
    dim = int(project.dimension)
    discs: List[DiscGeom] = []
    segs: List[SegmentGeom] = []
    polys: List[PolygonGeom] = []
    n_pop = 0

    for av in project.avatars:
        d, s, p = avatar_to_geoms(av, dim)
        discs.extend(d)
        segs.extend(s)
        polys.extend(p)

    for pop in project.populations:
        n = len(pop)
        n_pop += n
        col = color_rgb(pop.color)
        # subsample for display if huge
        if n > max_population_preview:
            idx = np.linspace(0, n - 1, max_population_preview, dtype=int)
        else:
            idx = np.arange(n)
        for i in idx:
            c = _as_tuple(pop.centers[i].tolist(), dim)
            r = float(pop.radii[i])
            discs.append(DiscGeom(
                c, r, col, f"pop:{pop.population_id[:8]}", "population",
                pop.population_id,
            ))

    scene = SceneGeometry(
        discs=discs, segments=segs, polygons=polys, dimension=dim,
        n_avatars=len(project.avatars),
        n_population_particles=n_pop,
    )
    scene.bounds = _compute_bounds(scene)
    return scene


def _compute_bounds(scene: SceneGeometry) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    pts: List[List[float]] = []
    for d in scene.discs:
        c = list(d.center)
        r = d.radius
        pts.append([c[0] - r, c[1] - r] + (c[2:] if len(c) > 2 else []))
        pts.append([c[0] + r, c[1] + r] + (c[2:] if len(c) > 2 else []))
    for s in scene.segments:
        pts.append(list(s.p0))
        pts.append(list(s.p1))
    for poly in getattr(scene, "polygons", []) or []:
        for pt in poly.points:
            pts.append(list(pt))
    if not pts:
        return None
    arr = np.array(pts, dtype=np.float64)
    return arr.min(axis=0), arr.max(axis=0)
