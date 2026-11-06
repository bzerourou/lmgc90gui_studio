"""Pure-Python / numpy generators. No pylmgc90.depositInXxx."""
from __future__ import annotations

import math
from itertools import product
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


def _safe_condition(expr: str, env: dict) -> bool:
    """Evaluate arithmetic comparisons and boolean operators without eval()."""
    import ast
    import operator

    compare_ops = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
    }

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                for value in node.values:
                    if not bool(evaluate(value)):
                        return False
                return True
            if isinstance(node.op, ast.Or):
                for value in node.values:
                    if bool(evaluate(value)):
                        return True
                return False
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not bool(evaluate(node.operand))
        if isinstance(node, ast.Compare):
            left = evaluate(node.left)
            for operation, comparator in zip(node.ops, node.comparators):
                operation_fn = compare_ops.get(type(operation))
                if operation_fn is None:
                    raise ValueError("unsupported comparison in ForLoop condition")
                right = evaluate(comparator)
                if not operation_fn(left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Name):
            if node.id not in env:
                raise ValueError(f"unknown name {node.id!r} in ForLoop condition")
            return env[node.id]
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, bool)):
                return node.value
            raise ValueError("only numeric constants are allowed in ForLoop condition")
        if isinstance(node, (ast.BinOp, ast.Call)):
            return _safe_arith(ast.unparse(node), env)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return _safe_arith(ast.unparse(node), env)
        raise ValueError(
            f"disallowed expression node {type(node).__name__} in ForLoop condition"
        )

    return bool(evaluate(ast.parse(expr, mode="eval")))


def for_loop_values(for_loop) -> list[float]:
    if for_loop.step == 0:
        raise ValueError("ForLoop step cannot be 0")
    vals: list[float] = []
    v = float(for_loop.start)
    guard = 0
    if for_loop.step > 0:
        while v < for_loop.stop - 1e-12:
            vals.append(v)
            v += for_loop.step
            guard += 1
            if guard > 100_000:
                raise ValueError("ForLoop too many iterations")
    else:
        while v > for_loop.stop + 1e-12:
            vals.append(v)
            v += for_loop.step
            guard += 1
            if guard > 100_000:
                raise ValueError("ForLoop too many iterations")
    return vals


def _lmgc5_name(base: str, i: float, prefix: str = "x") -> str:
    s = (base or prefix).strip()[:5]
    idx = abs(int(round(i))) % 1000
    if len(s) < 5:
        s = (s + f"{idx:03d}")[:5]
    if len(s) < 5:
        s = s + ("x" * (5 - len(s)))
    return s[:5]


def expand_for_loop(for_loop, template: Avatar, dimension: int = 2) -> list[Avatar]:

    """Expand a ForLoop with safe arithmetic expressions for centre / radius."""
    import math

    from .entities import ForLoop

    if not isinstance(for_loop, ForLoop):
        raise TypeError("expand_for_loop expects a ForLoop")
    if for_loop.step == 0:
        raise ValueError("ForLoop step cannot be 0")

    values = for_loop_values(for_loop)

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
        if for_loop.condition:
            condition_env = {
                **env,
                "x": x,
                "y": y,
                "z": center[2] if dimension == 3 else 0.0,
                "r": float(clone.radius or 0.0),
                "radius": float(clone.radius or 0.0),
            }
            if not _safe_condition(for_loop.condition, condition_env):
                continue
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


def sample_radii(
    config: GranuloConfig,
    *,
    count: Optional[int] = None,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """Sample radii using the selected pylmgc-compatible distribution."""
    n = int(config.nb_particles if count is None else count)
    if n <= 0:
        raise ValueError("nb_particles must be > 0")
    if rng is None:
        rng = np.random.default_rng(config.seed)
    dist = getattr(config, "distribution_type", "granulo_Random") or "granulo_Random"
    params = dict(getattr(config, "distribution_params", None) or {})

    if dist == "granulo_ReadFromFile":
        path = getattr(config, "distribution_file", None)
        if not path:
            raise ValueError("distribution_file is required for granulo_ReadFromFile")
        try:
            radii = np.atleast_1d(np.loadtxt(path, dtype=np.float64)).reshape(-1)
        except (OSError, ValueError) as exc:
            raise ValueError(f"cannot read granulometry file {path!r}: {exc}") from exc
        if len(radii) < n:
            raise ValueError(
                f"granulometry file contains {len(radii)} radii, but {n} are required"
            )
        radii = radii[:n]
    else:
        rmin, rmax = float(config.radius_min), float(config.radius_max)
        if rmin <= 0 or rmax < rmin:
            raise ValueError("invalid radius range")
        if dist == "granulo_Random":
            radii = rng.uniform(rmin, rmax, n)
        elif dist == "granulo_Uniform":
            draw = rng.uniform(rmin, rmax, n)
            radii = rmax * rmin / (rmin + rmax - draw)
        elif dist in ("granulo_TwoSizesNumber", "granulo_TwoSizesVolume"):
            p_min = float(params.get("p_min", 0.5))
            if not 0.0 <= p_min <= 1.0:
                raise ValueError("p_min must be between 0 and 1")
            p_number = p_min
            if dist == "granulo_TwoSizesVolume":
                if p_min == 0.0:
                    p_number = 0.0
                elif p_min == 1.0:
                    p_number = 1.0
                else:
                    p_number = 1.0 / (
                        1.0 + (1.0 - p_min) * rmin**2 / (p_min * rmax**2)
                    )
            radii = np.where(rng.random(n) < p_number, rmin, rmax)
        elif dist == "granulo_BetaDistribution":
            try:
                from scipy.special import betainc
            except ImportError as exc:
                raise ValueError(
                    "granulo_BetaDistribution requires scipy for the Numpy backend"
                ) from exc
            nb_t = int(params.get("nb_t", 10))
            volume = float(params.get("vol", 0.0))
            alpha = float(params.get("a", 0.0))
            beta = float(params.get("b", 0.0))
            if nb_t <= 0 or volume <= 0 or alpha <= 0 or beta <= 0:
                raise ValueError("Beta distribution requires nb_t, vol, a and b > 0")
            radius_step = (rmax - rmin) / nb_t
            volume_scale = 3.0 * volume / (4.0 * math.pi)
            previous_mass = 0.0
            parts = []
            for index in range(1, nb_t + 1):
                mass = float(betainc(alpha, beta, index / nb_t))
                lower = rmin + (index - 1) * radius_step
                midpoint = lower + 0.5 * radius_step
                number = int((mass - previous_mass) * volume_scale / midpoint**3)
                if number > 0:
                    parts.append(rng.uniform(lower, lower + radius_step, number))
                previous_mass = mass
            radii = np.concatenate(parts) if parts else np.empty(0, dtype=np.float64)
            rng.shuffle(radii)
        else:
            raise ValueError(f"unknown radius distribution: {dist!r}")

    if not np.isfinite(radii).all() or (radii <= 0).any():
        raise ValueError("radius distribution must contain finite positive values")
    return np.asarray(radii, dtype=np.float64)


class NumpyGranulo:
    """Rejection packing. Replaces pre.granulo_Random + depositInXxx for core."""

    MAX_ATTEMPTS_FACTOR = 25
    CANDIDATE_BATCH = 512

    def deposit(self, config: GranuloConfig) -> GranuloResult:
        if (
            config.distribution_type != "granulo_ReadFromFile"
            and (config.radius_min <= 0 or config.radius_max < config.radius_min)
        ):
            raise ValueError("invalid radius range")
        if config.nb_particles <= 0:
            raise ValueError("nb_particles must be > 0")

        rng = np.random.default_rng(config.seed)
        dim = config.dimension
        n = int(config.nb_particles)
        attempts = 0
        max_attempts = n * self.MAX_ATTEMPTS_FACTOR
        pre_sampled_radii = None
        if config.distribution_type in (
            "granulo_ReadFromFile", "granulo_BetaDistribution",
        ):
            pre_sampled_radii = sample_radii(config, rng=rng)
            if config.distribution_type == "granulo_BetaDistribution":
                n = len(pre_sampled_radii)
                if n == 0:
                    raise ValueError("Beta distribution produced no particles")

        centers = np.empty((n, dim), dtype=np.float64)
        radii = np.empty(n, dtype=np.float64)
        placed = 0
        max_radius = (
            float(np.max(pre_sampled_radii))
            if pre_sampled_radii is not None
            else float(config.radius_max)
        )
        cell_size = 2.0 * max_radius
        neighbor_offsets = tuple(product((-1, 0, 1), repeat=dim))
        spatial_grid: dict[tuple[int, ...], list[int]] = {}

        while placed < n and attempts < max_attempts:
            remaining = n - placed
            batch = min(self.CANDIDATE_BATCH, remaining * 4)
            if pre_sampled_radii is None:
                cand_r = sample_radii(config, count=batch, rng=rng)
            else:
                cand_r = pre_sampled_radii[attempts:attempts + batch]
                if len(cand_r) == 0:
                    break
            batch_count = len(cand_r)
            cand_c = self._sample(rng, batch_count, config, cand_r)
            mask = self._inside(cand_c, cand_r, config)
            cand_c, cand_r = cand_c[mask], cand_r[mask]
            for i in range(len(cand_c)):
                if placed >= n:
                    break
                c, r = cand_c[i], float(cand_r[i])
                cell = tuple(
                    math.floor(float(c[axis]) / cell_size)
                    for axis in range(dim)
                )
                if not self._no_hit_spatial(
                    c, r, centers, radii, spatial_grid, cell, neighbor_offsets,
                ):
                    continue
                centers[placed] = c
                radii[placed] = r
                spatial_grid.setdefault(cell, []).append(placed)
                placed += 1
            attempts += batch_count

        atype = AvatarType(config.avatar_type)
        pop = ParticlePopulation.create(
            avatar_type=atype,
            material_name=config.material_name,
            model_name=config.model_name,
            color=config.color,
            origin=AvatarOrigin.GRANULO,
            centers=centers[:placed],
            radii=radii[:placed],
            group_name=config.group_name,
        )
        config.population_id = pop.population_id
        return GranuloResult(pop, n, placed, attempts)

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
        if kind == "Cylinder3D":
            R = float(p.get("r", p.get("R", 1.0)))
            lz = float(p.get("lz", 1.0))
            theta = rng.uniform(0, 2 * math.pi, n)
            rr = R * np.sqrt(rng.uniform(0, 1, n))
            z = rng.uniform(0.0, lz, n)
            return np.column_stack([
                rr * np.cos(theta),
                rr * np.sin(theta),
                z,
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
        if kind == "Cylinder3D":
            R = float(p.get("r", p.get("R", 1.0)))
            lz = float(p.get("lz", 1.0))
            radial = np.linalg.norm(centers[:, :2], axis=1)
            return (radial + r <= R) & (centers[:, 2] - r >= 0.0) & (centers[:, 2] + r <= lz)
        return np.ones(len(centers), dtype=bool)

    @staticmethod
    def _no_hit_spatial(
        center,
        radius,
        centers,
        radii,
        grid: dict[tuple[int, ...], list[int]],
        cell: tuple[int, ...],
        neighbor_offsets: tuple[tuple[int, ...], ...],
    ) -> bool:
        for offset in neighbor_offsets:
            neighbor = tuple(
                coordinate + delta
                for coordinate, delta in zip(cell, offset)
            )
            for index in grid.get(neighbor, ()):
                min_distance = radius + radii[index]
                distance_squared = sum(
                    (float(center[axis]) - centers[index, axis]) ** 2
                    for axis in range(len(center))
                )
                if distance_squared < min_distance * min_distance:
                    return False
        return True
