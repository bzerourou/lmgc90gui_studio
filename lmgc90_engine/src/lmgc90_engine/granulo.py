"""Granulo deposit via pylmgc90.pre when available — engine layer only.

Official pylmgc90 API (2025)::

    nb_laid, coors, radii = pre.depositInBox2D(radii, lx, ly)

Falls back to a dense grid if ``depositIn*`` is missing (should not happen
when pylmgc90 is installed correctly).
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np

from lmgc90_core.entities import GranuloConfig
from lmgc90_core.population import ParticlePopulation
from lmgc90_core.types import AvatarOrigin, AvatarType

from .errors import MaterializationError, PylmgcNotAvailable


def deposit_population(
    config: GranuloConfig,
    *,
    material_name: Optional[str] = None,
    model_name: Optional[str] = None,
    color: Optional[str] = None,
    avatar_type: Optional[AvatarType] = None,
) -> ParticlePopulation:
    """Run a pylmgc deposit and return a core ParticlePopulation (SoA)."""
    try:
        from pylmgc90 import pre  # type: ignore
    except ImportError as exc:
        raise PylmgcNotAvailable(
            "pylmgc90 is required for engine granulo deposit"
        ) from exc

    centers, radii = _call_deposit(pre, config)
    centers_a = np.asarray(centers, dtype=np.float64)
    radii_a = np.asarray(radii, dtype=np.float64)
    if centers_a.ndim == 1:
        dim = 3 if config.dimension == 3 else 2
        centers_a = centers_a.reshape(-1, dim)
    atype = avatar_type or AvatarType(config.avatar_type)
    pop = ParticlePopulation.create(
        avatar_type=atype,
        material_name=material_name or config.material_name,
        model_name=model_name or config.model_name,
        centers=centers_a,
        radii=radii_a,
        color=color or config.color,
        origin=AvatarOrigin.GRANULO,
        group_name=config.group_name,
        population_id=config.population_id,
    )
    config.population_id = pop.population_id
    return pop


def _safe_copy(arr, dtype=np.float64) -> np.ndarray:
    if arr is None:
        return np.array([], dtype=dtype)
    return np.array(arr, dtype=dtype, copy=True, order="C")


def _normalize_coords(coor, nb: int, dim: int) -> np.ndarray:
    coor = _safe_copy(coor)
    if coor.size == 0:
        return np.zeros((0, dim), dtype=np.float64)
    if coor.ndim == 1:
        if coor.size % dim != 0:
            raise MaterializationError(
                f"coords size {coor.size} not multiple of dim={dim}"
            )
        coor = coor.reshape(-1, dim)
    elif coor.ndim == 2:
        if coor.shape[1] != dim and coor.shape[0] == dim:
            coor = coor.T
    else:
        raise MaterializationError(f"unexpected coords shape {coor.shape}")
    if nb is not None and nb >= 0:
        coor = coor[:nb]
    return np.ascontiguousarray(coor, dtype=np.float64)


def _call_deposit(pre, config: GranuloConfig) -> tuple[np.ndarray, np.ndarray]:
    n = int(config.nb_particles)
    rmin = float(config.radius_min)
    rmax = float(config.radius_max)
    seed = config.seed
    rng = np.random.default_rng(seed)
    radii_in = _safe_copy(rng.uniform(rmin, rmax, size=n))

    ctype = (config.container_type or "Box2D").lower().replace("_", "")
    p = dict(config.container_params or {})
    dim = int(config.dimension or 2)

    try:
        if ctype in ("box2d", "box", "depositinbox2d"):
            fn = getattr(pre, "depositInBox2D", None)
            if fn is None:
                raise MaterializationError("pylmgc90.pre has no depositInBox2D")
            lx = float(p.get("lx", p.get("xmax", 1.0) - p.get("xmin", 0.0)))
            ly = float(p.get("ly", p.get("ymax", 1.0) - p.get("ymin", 0.0)))
            # Official API: depositInBox2D(radii, lx, ly)
            result = fn(radii_in, lx, ly)
            return _parse_result(result, radii_in, dim=2)

        if ctype in ("box3d", "depositinbox3d"):
            fn = getattr(pre, "depositInBox3D", None)
            if fn is None:
                raise MaterializationError("pylmgc90.pre has no depositInBox3D")
            lx = float(p.get("lx", 1.0))
            ly = float(p.get("ly", 1.0))
            lz = float(p.get("lz", 1.0))
            try:
                result = fn(radii_in, lx, ly, lz)
            except TypeError:
                result = fn(radii_in, [0.0, 0.0, 0.0], [lx, ly, lz])
            return _parse_result(result, radii_in, dim=3)

        if ctype in ("disk2d", "drum2d"):
            # Official-style: depositInDrum2D(radii, R) or depositInDisk2D(radii, R)
            fn = getattr(pre, "depositInDrum2D", None) or getattr(pre, "depositInDisk2D", None)
            if fn is None:
                raise MaterializationError(f"no deposit for {config.container_type}")
            r = float(p.get("r", 1.0))
            try:
                result = fn(radii_in, r)
            except TypeError:
                result = fn(radii_in, radius=r)
            return _parse_result(result, radii_in, dim=2)
    except MaterializationError:
        raise
    except Exception as exc:
        raise MaterializationError(f"deposit failed ({config.container_type}): {exc}") from exc

    raise MaterializationError(f"unknown granulo container_type: {config.container_type!r}")


def _parse_result(result: Any, radii_in: np.ndarray, *, dim: int) -> tuple[np.ndarray, np.ndarray]:
    if result is None:
        raise MaterializationError("deposit returned None")
    if not isinstance(result, (tuple, list)):
        raise MaterializationError(f"unexpected deposit return type {type(result)}")
    if len(result) == 3:
        nb_laid, coors, radii_out = result
        nb = int(nb_laid)
        centers = _normalize_coords(coors, nb, dim)
        radii = _safe_copy(radii_out)[: len(centers)]
        if radii.size != len(centers):
            radii = _safe_copy(radii_in)[: len(centers)]
        return centers, radii
    if len(result) == 2:
        coors, radii_out = result
        centers = _normalize_coords(coors, -1, dim)
        radii = _safe_copy(radii_out)[: len(centers)]
        return centers, radii
    raise MaterializationError(f"deposit returned {len(result)} values, expected 2 or 3")
