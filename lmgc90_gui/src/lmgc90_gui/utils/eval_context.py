"""Build a SafeEvaluator context from a Project — mirrors legacy build_eval_context."""
from __future__ import annotations

import math
from typing import Any, Iterable, List, Optional

import numpy as np

from lmgc90_core import Project


class _NodeProxy:
    def __init__(self, coor: list):
        self.coor = list(coor)


class _NodesView:
    """pylmgc90-style 1-based nodes; nodes[0] == nodes[1] == center / first vertex."""

    def __init__(self, avatar):
        self._av = avatar

    def __getitem__(self, k: int) -> _NodeProxy:
        verts = self._av.vertices or []
        if not verts:
            return _NodeProxy(list(self._av.center))
        # map 0 and 1 → first point / center
        if k in (0, 1):
            return _NodeProxy(list(self._av.center) if not verts else list(verts[0]))
        idx = k - 1 if k >= 1 else k
        if idx < 0 or idx >= len(verts):
            raise IndexError(f"node index {k} out of range")
        return _NodeProxy(list(verts[idx]))


class AvatarProxy:
    def __init__(self, avatar, index: int):
        self._av = avatar
        self.index = index

    @property
    def center(self) -> list:
        return list(self._av.center)

    @property
    def x(self) -> float:
        return float(self._av.center[0])

    @property
    def y(self) -> float:
        return float(self._av.center[1]) if len(self._av.center) > 1 else 0.0

    @property
    def z(self) -> Optional[float]:
        return float(self._av.center[2]) if len(self._av.center) > 2 else None

    @property
    def radius(self):
        return self._av.radius

    @property
    def color(self) -> str:
        return self._av.color

    @property
    def material_name(self) -> str:
        return self._av.material_name

    @property
    def model_name(self) -> str:
        return self._av.model_name

    @property
    def avatar_type(self) -> str:
        return self._av.avatar_type.value

    @property
    def origin(self) -> str:
        return self._av.origin.value

    @property
    def generation_type(self):
        return self._av.generation_type

    @property
    def is_hollow(self) -> bool:
        return bool(self._av.is_hollow)

    @property
    def nb_vertices(self):
        return self._av.nb_vertices

    @property
    def vertices(self):
        return self._av.vertices

    @property
    def axis(self):
        return self._av.axis

    @property
    def contactors(self) -> list:
        return list(self._av.contactors)

    @property
    def wall_params(self) -> dict:
        return dict(self._av.wall_params or {})

    @property
    def mesh_params(self):
        return self._av.mesh_params

    @property
    def brick_lx(self):
        return (self._av.wall_params or {}).get("l")

    @property
    def brick_ly(self):
        return (self._av.wall_params or {}).get("h")

    @property
    def brick_lz(self):
        return (self._av.wall_params or {}).get("lz")

    @property
    def nodes(self) -> _NodesView:
        return _NodesView(self._av)


class _AvatarList:
    def __init__(self, project: Project):
        self._p = project

    def __len__(self) -> int:
        return len(self._p.avatars)

    def __getitem__(self, i: int) -> AvatarProxy:
        if i < 0:
            i += len(self._p.avatars)
        if i < 0 or i >= len(self._p.avatars):
            raise IndexError(f"Avatar index {i} invalide")
        return AvatarProxy(self._p.avatars[i], i)

    def __iter__(self):
        for i, av in enumerate(self._p.avatars):
            yield AvatarProxy(av, i)


class _GroupMap:
    def __init__(self, project: Project):
        self._p = project

    def __contains__(self, name: str) -> bool:
        return name in self._p.avatar_groups

    def __getitem__(self, name: str) -> List[AvatarProxy]:
        if name not in self._p.avatar_groups:
            raise KeyError(f"Groupe {name!r} introuvable")
        ids = self._p.avatar_groups[name]
        by_id = {a.avatar_id: a for a in self._p.avatars}
        out = []
        for aid in ids:
            av = by_id.get(aid)
            if av is None:
                continue
            idx = self._p.avatars.index(av)
            out.append(AvatarProxy(av, idx))
        return out

    def __iter__(self):
        return iter(self._p.avatar_groups.keys())


class _MaterialProxy:
    def __init__(self, mat):
        self._m = mat

    @property
    def name(self) -> str:
        return self._m.name

    @property
    def density(self) -> float:
        return float(self._m.density)

    @property
    def material_type(self) -> str:
        return self._m.material_type.value

    def __getitem__(self, key: str):
        return self._m.properties[key]

    def __getattr__(self, key: str):
        if key.startswith("_"):
            raise AttributeError(key)
        if key in self._m.properties:
            return self._m.properties[key]
        raise AttributeError(key)


class _MaterialMap:
    def __init__(self, project: Project):
        self._p = project

    def __getitem__(self, name: str) -> _MaterialProxy:
        for m in self._p.materials:
            if m.name == name:
                return _MaterialProxy(m)
        raise KeyError(f"Matériau {name!r} introuvable")


class _ModelProxy:
    def __init__(self, mod):
        self._m = mod

    @property
    def name(self) -> str:
        return self._m.name

    @property
    def physics(self) -> str:
        return self._m.physics

    @property
    def element(self) -> str:
        return self._m.element

    @property
    def dimension(self) -> int:
        return int(self._m.dimension)

    def __getitem__(self, key: str):
        return (self._m.options or {})[key]


class _ModelMap:
    def __init__(self, project: Project):
        self._p = project

    def __getitem__(self, name: str) -> _ModelProxy:
        for m in self._p.models:
            if m.name == name:
                return _ModelProxy(m)
        raise KeyError(f"Modèle {name!r} introuvable")


def resolve_dynamic_vars(project: Project) -> dict[str, Any]:
    """Evaluate project.dynamic_vars expressions in definition order."""
    from .safe_eval import safe_eval

    base = _base_names(project)
    resolved: dict[str, Any] = {}
    # dynamic_vars values may be raw numbers or expression strings
    for name, expr in dict(project.dynamic_vars).items():
        ctx = {**base, **resolved}
        if isinstance(expr, (int, float, bool)):
            resolved[name] = expr
        else:
            try:
                resolved[name] = safe_eval(str(expr), ctx)
            except Exception:
                resolved[name] = expr  # keep string if not evaluable yet
    return resolved


def _base_names(project: Project) -> dict[str, Any]:
    avatars = _AvatarList(project)

    def avatars_by_color(color: str):
        return [a for a in avatars if a.color == color]

    def avatars_by_material(name: str):
        return [a for a in avatars if a.material_name == name]

    def avatars_by_type(typ: str):
        return [a for a in avatars if a.avatar_type == typ]

    def avatars_by_origin(origin: str):
        return [a for a in avatars if a.origin == origin]

    return {
        "pi": math.pi,
        "e": math.e,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "abs": abs,
        "min": min,
        "max": max,
        "round": round,
        "sum": sum,
        "len": len,
        "list": list,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "math": math,
        "np": np,
        "dimension": project.dimension,
        "n_bodies": project.n_bodies,
        "avatar": avatars,
        "group": _GroupMap(project),
        "material": _MaterialMap(project),
        "model": _ModelMap(project),
        "avatars_by_color": avatars_by_color,
        "avatars_by_material": avatars_by_material,
        "avatars_by_type": avatars_by_type,
        "avatars_by_origin": avatars_by_origin,
    }


def build_eval_context(project: Project) -> dict[str, Any]:
    ctx = _base_names(project)
    ctx.update(resolve_dynamic_vars(project))
    return ctx
