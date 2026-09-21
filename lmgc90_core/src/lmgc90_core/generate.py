"""Pure-Python / numpy generators. No pylmgc90.depositInXxx."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

from .entities import Avatar, GranuloConfig, Loop
from .ids import new_avatar_id
from .population import ParticlePopulation
from .types import LOOP_ALIASES, AvatarOrigin, AvatarType


def loop_positions(loop: Loop, dimension: int = 2) -> list[list[float]]:
    kind = LOOP_ALIASES.get(loop.loop_type, loop.loop_type)
    n = loop.count
    ox, oy, oz = loop.offset_x, loop.offset_y, loop.offset_z
    if kind == "circle":
        return [
            [ox + loop.radius * math.cos(2 * math.pi * i / n),
             oy + loop.radius * math.sin(2 * math.pi * i / n)]
            + ([oz] if dimension == 3 else [])
            for i in range(n)
        ]
    if kind == "grid":
        side = max(1, int(math.ceil(math.sqrt(n))))
        pts = []
        for i in range(n):
            p = [ox + (i % side) * loop.step, oy + (i // side) * loop.step]
            if dimension == 3:
                p.append(oz)
            pts.append(p)
        return pts
    if kind == "line":
        pts = []
        for i in range(n):
            if loop.invert_axis:
                p = [ox, oy + i * loop.step]
            else:
                p = [ox + i * loop.step, oy]
            if dimension == 3:
                p.append(oz)
            pts.append(p)
        return pts
    if kind == "spiral":
        pts = []
        for i in range(n):
            angle = 2 * math.pi * i / max(1, n // 5)
            r = loop.radius + i * loop.spiral_factor
            p = [ox + r * math.cos(angle), oy + r * math.sin(angle)]
            if dimension == 3:
                p.append(oz)
            pts.append(p)
        return pts
    raise ValueError(f"unknown loop type {loop.loop_type!r}")


def expand_loop(loop: Loop, template: Avatar, dimension: int = 2) -> list[Avatar]:
    positions = loop_positions(loop, dimension=dimension)
    generated: list[Avatar] = []
    ids: list[str] = []
    for pos in positions:
        clone = template.copy()
        clone.avatar_id = new_avatar_id()
        clone.center = list(pos)
        clone.origin = AvatarOrigin.LOOP
        generated.append(clone)
        ids.append(clone.avatar_id)
    loop.generated_ids = ids
    return generated


def _safe_arith(expr: str, env: dict) -> float:
    """Minimal arithmetic eval — no attributes, no calls except math names in env."""
    import ast
    import operator as op

    ops = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg, ast.UAdd: op.pos,
        ast.Mod: op.mod, ast.FloorDiv: op.floordiv,
    }

    def _ev(node):
        if isinstance(node, ast.Expression):
            return _ev(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in env:
                raise ValueError(f"unknown name {node.id!r} in expression")
            return env[node.id]
        if isinstance(node, ast.BinOp):
            return ops[type(node.op)](_ev(node.left), _ev(node.right))
        if isinstance(node, ast.UnaryOp):
            return ops[type(node.op)](_ev(node.operand))
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in env:
                raise ValueError("only simple math calls allowed")
            return env[node.func.id](*[_ev(a) for a in node.args])
        raise ValueError(f"disallowed expression node {type(node).__name__}")

    return float(_ev(ast.parse(expr, mode="eval")))


def expand_for_loop(for_loop, template: Avatar, dimension: int = 2) -> list[Avatar]:
    """Expand a ForLoop with safe arithmetic expressions for centre / radius."""
    import math

    from .entities import ForLoop

    if not isinstance(for_loop, ForLoop):
        raise TypeError("expand_for_loop expects a ForLoop")
    if for_loop.step == 0:
        raise ValueError("ForLoop step cannot be 0")

    values: list[float] = []
    v = float(for_loop.start)
    # inclusive start, exclusive stop — same as range() semantics for floats
    if for_loop.step > 0:
        while v < for_loop.stop - 1e-12:
            values.append(v)
            v += for_loop.step
    else:
        while v > for_loop.stop + 1e-12:
            values.append(v)
            v += for_loop.step

    base_env = {
        "pi": math.pi, "e": math.e,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "sqrt": math.sqrt, "abs": abs, "min": min, "max": max,
    }
    generated: list[Avatar] = []
    ids: list[str] = []
    for val in values:
        env = {**base_env, for_loop.var_name: val, "i": val}
        x = _safe_arith(for_loop.expr_x, env)
        y = _safe_arith(for_loop.expr_y, env)
        center = [x, y]
        if dimension == 3:
            center.append(_safe_arith(for_loop.expr_z, env))
        clone = template.copy()
        clone.avatar_id = new_avatar_id()
        clone.center = center
        clone.origin = AvatarOrigin.LOOP
        if for_loop.expr_radius:
            clone.radius = _safe_arith(for_loop.expr_radius, env)
        generated.append(clone)
        ids.append(clone.avatar_id)
    for_loop.generated_ids = ids
    return generated


@dataclass
class GranuloResult:
    population: ParticlePopulation
    nb_requested: int
    nb_placed: int
    attempts: int

    @property
    def fill_ratio(self) -> float:
        if self.nb_requested == 0:
            return 0.0
        return self.nb_placed / self.nb_requested


class NumpyGranulo:
    """Rejection packing. Replaces pre.granulo_Random + depositInXxx for core."""

    MAX_ATTEMPTS_FACTOR = 25
    CANDIDATE_BATCH = 512

    def deposit(self, config: GranuloConfig) -> GranuloResult:
        if config.radius_min <= 0 or config.radius_max < config.radius_min:
            raise ValueError("invalid radius range")
        if config.nb_particles <= 0:
            raise ValueError("nb_particles must be > 0")

        rng = np.random.default_rng(config.seed)
        dim = config.dimension
        n = config.nb_particles
        centers = np.empty((0, dim), dtype=np.float64)
        radii = np.empty(0, dtype=np.float64)
        attempts = 0
        max_attempts = n * self.MAX_ATTEMPTS_FACTOR

        while len(radii) < n and attempts < max_attempts:
            remaining = n - len(radii)
            batch = min(self.CANDIDATE_BATCH, remaining * 4)
            cand_r = rng.uniform(config.radius_min, config.radius_max, batch)
            cand_c = self._sample(rng, batch, config, cand_r)
            mask = self._inside(cand_c, cand_r, config)
            cand_c, cand_r = cand_c[mask], cand_r[mask]
            if len(centers) > 0 and len(cand_c) > 0:
                free = self._no_hit_batch(cand_c, cand_r, centers, radii)
                cand_c, cand_r = cand_c[free], cand_r[free]
            for i in range(len(cand_c)):
                if len(radii) >= n:
                    break
                c, r = cand_c[i], float(cand_r[i])
                if len(centers) > 0 and not self._no_hit_one(c, r, centers, radii):
                    continue
                centers = np.vstack([centers, c]) if len(centers) else c.reshape(1, dim)
                radii = np.append(radii, r)
            attempts += batch

        atype = AvatarType(config.avatar_type)
        pop = ParticlePopulation.create(
            avatar_type=atype,
            material_name=config.material_name,
            model_name=config.model_name,
            color=config.color,
            origin=AvatarOrigin.GRANULO,
            centers=centers,
            radii=radii,
            group_name=config.group_name,
        )
        config.population_id = pop.population_id
        return GranuloResult(pop, n, len(pop), attempts)

    def _sample(self, rng, n, cfg: GranuloConfig, radii) -> np.ndarray:
        p = cfg.container_params
        kind = cfg.container_type
        if kind == "Box2D":
            # Match pylmgc90 depositInBox2D: particles in [0, lx] × [0, ly]
            lx, ly = p["lx"], p["ly"]
            return np.column_stack([
                rng.uniform(0.0, lx, n),
                rng.uniform(0.0, ly, n),
            ])
        if kind in ("Disk2D", "Drum2D"):
            r = p["r"]
            theta = rng.uniform(0, 2 * math.pi, n)
            rr = r * np.sqrt(rng.uniform(0, 1, n))
            return np.column_stack([rr * np.cos(theta), rr * np.sin(theta)])
        if kind == "Couette2D":
            rint, rext = p["rint"], p["rext"]
            theta = rng.uniform(0, 2 * math.pi, n)
            rr = np.sqrt(rng.uniform(rint ** 2, rext ** 2, n))
            return np.column_stack([rr * np.cos(theta), rr * np.sin(theta)])
        if kind == "Box3D":
            lx, ly, lz = p["lx"], p["ly"], p["lz"]
            return np.column_stack([
                rng.uniform(0.0, lx, n),
                rng.uniform(0.0, ly, n),
                rng.uniform(0.0, lz, n),
            ])
        if kind == "Sphere3D":
            r = p["r"]
            phi = rng.uniform(0, 2 * math.pi, n)
            costh = rng.uniform(-1, 1, n)
            sinth = np.sqrt(1 - costh ** 2)
            rr = r * (rng.uniform(0, 1, n) ** (1 / 3))
            return np.column_stack([
                rr * sinth * np.cos(phi),
                rr * sinth * np.sin(phi),
                rr * costh,
            ])
        raise ValueError(f"unsupported container {kind!r}")

    def _inside(self, centers, radii, cfg: GranuloConfig) -> np.ndarray:
        p = cfg.container_params
        kind = cfg.container_type
        r = radii
        if kind == "Box2D":
            lx, ly = p["lx"], p["ly"]
            return (
                (centers[:, 0] - r >= 0.0) & (centers[:, 0] + r <= lx)
                & (centers[:, 1] - r >= 0.0) & (centers[:, 1] + r <= ly)
            )
        if kind in ("Disk2D", "Drum2D"):
            return np.linalg.norm(centers, axis=1) + r <= p["r"]
        if kind == "Couette2D":
            dist = np.linalg.norm(centers, axis=1)
            return (dist - r >= p["rint"]) & (dist + r <= p["rext"])
        if kind == "Box3D":
            lx, ly, lz = p["lx"], p["ly"], p["lz"]
            return (
                (centers[:, 0] - r >= 0.0) & (centers[:, 0] + r <= lx)
                & (centers[:, 1] - r >= 0.0) & (centers[:, 1] + r <= ly)
                & (centers[:, 2] - r >= 0.0) & (centers[:, 2] + r <= lz)
            )
        if kind == "Sphere3D":
            return np.linalg.norm(centers, axis=1) + r <= p["r"]
        return np.ones(len(centers), dtype=bool)

    @staticmethod
    def _no_hit_batch(cand, cand_r, placed, placed_r) -> np.ndarray:
        diff = cand[:, None, :] - placed[None, :, :]
        dist2 = np.sum(diff ** 2, axis=2)
        min2 = (cand_r[:, None] + placed_r[None, :]) ** 2
        return ~np.any(dist2 < min2, axis=1)

    @staticmethod
    def _no_hit_one(center, radius, placed, placed_r) -> bool:
        dist2 = np.sum((placed - center) ** 2, axis=1)
        return not bool(np.any(dist2 < (placed_r + radius) ** 2))
