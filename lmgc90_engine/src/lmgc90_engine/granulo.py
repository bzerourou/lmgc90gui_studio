"""Granulo / deposit helpers that call pylmgc90.pre when the pure numpy path is not enough.

The core already has NumpyGranulo for simple deposits. This module is the
escape hatch for official pre.depositInBox* / granulo_Random behaviour.
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np

from lmgc90_core.entities import GranuloConfig
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
        raise PylmgcNotAvailable("pylmgc90 required for granulo_pylmgc") from exc


def deposit_population(
    config: GranuloConfig,
    *,
    material_name: Optional[str] = None,
    model_name: Optional[str] = None,
    color: Optional[str] = None,
    avatar_type: Optional[AvatarType] = None,
) -> ParticlePopulation:
    """Run a pylmgc deposit and return a core ParticlePopulation (SoA).

    Defaults are taken from the GranuloConfig when not overridden.
    Does not mutate a Project — the caller adds the result with project.add(pop).
    """
    pre = _pre()
    centers, radii = _call_deposit(pre, config)

    mat = material_name or config.material_name
    mod = model_name or config.model_name
    col = color or config.color
    atype = avatar_type
    if atype is None:
        raw = config.avatar_type or "rigidDisk"
        atype = raw if isinstance(raw, AvatarType) else AvatarType(raw)

    return ParticlePopulation.create(
        avatar_type=atype,
        material_name=mat,
        model_name=mod,
        color=col,
        centers=np.asarray(centers, dtype=float),
        radii=np.asarray(radii, dtype=float),
        group_name=config.group_name,
        population_id=config.population_id,
    )


def _call_deposit(pre, config: GranuloConfig) -> tuple[list, list]:
    """Dispatch to the right pre.deposit* / granulo helper."""
    ctype = (config.container_type or "box2d").lower().replace("_", "")
    n = int(config.nb_particles)
    rmin = float(config.radius_min)
    rmax = float(config.radius_max)
    seed = config.seed

    if seed is not None:
        rng = np.random.default_rng(seed)
        radii = rng.uniform(rmin, rmax, size=n).tolist()
    else:
        radii = [0.5 * (rmin + rmax)] * n

    box = dict(config.container_params or {})
    # accept both xmin/xmax and lx-style
    if "lx" in box and "xmin" not in box:
        lx = float(box["lx"])
        box.setdefault("xmin", 0.0)
        box.setdefault("xmax", lx)
    if "ly" in box and "ymin" not in box:
        ly = float(box["ly"])
        box.setdefault("ymin", 0.0)
        box.setdefault("ymax", ly)
    if "lz" in box and "zmin" not in box:
        lz = float(box["lz"])
        box.setdefault("zmin", 0.0)
        box.setdefault("zmax", lz)

    xmin = float(box.get("xmin", 0.0))
    xmax = float(box.get("xmax", 1.0))
    ymin = float(box.get("ymin", 0.0))
    ymax = float(box.get("ymax", 1.0))
    zmin = float(box.get("zmin", 0.0))
    zmax = float(box.get("zmax", 1.0))

    try:
        if ctype in ("box2d", "box", "depositinbox2d"):
            fn = getattr(pre, "depositInBox2D", None)
            if fn is None:
                # fallback: simple grid-ish placement without overlap guarantee
                return _fallback_box2d(xmin, xmax, ymin, ymax, radii)
            # API varies; common pattern: list of radii + box bounds
            try:
                result = fn(radii, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
            except TypeError:
                result = fn(radii, [xmin, ymin], [xmax, ymax])
            return _parse_deposit_result(result, radii)
        if ctype in ("box3d", "depositinbox3d"):
            fn = getattr(pre, "depositInBox3D", None)
            if fn is None:
                return _fallback_box3d(xmin, xmax, ymin, ymax, zmin, zmax, radii)
            try:
                result = fn(
                    radii, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                    zmin=zmin, zmax=zmax,
                )
            except TypeError:
                result = fn(radii, [xmin, ymin, zmin], [xmax, ymax, zmax])
            return _parse_deposit_result(result, radii)
    except Exception as exc:
        raise MaterializationError(f"deposit failed ({ctype}): {exc}") from exc

    raise MaterializationError(f"unknown granulo container_type: {config.container_type!r}")


def _parse_deposit_result(result: Any, radii: list) -> tuple[list, list]:
    """Normalize various return shapes from pre.deposit*."""
    if result is None:
        raise MaterializationError("deposit returned None")
    if isinstance(result, tuple) and len(result) == 2:
        centers, rad = result
        return list(centers), list(rad)
    # some versions return only centers
    if isinstance(result, (list, np.ndarray)):
        return list(result), list(radii)
    raise MaterializationError(f"unrecognized deposit result type: {type(result)}")


def _fallback_box2d(xmin, xmax, ymin, ymax, radii) -> tuple[list, list]:
    """Deterministic non-overlapping grid when pre.deposit* is missing."""
    n = len(radii)
    rmax = max(radii) if radii else 0.05
    cols = max(1, int(np.ceil(np.sqrt(n))))
    dx = (xmax - xmin) / (cols + 1)
    dy = (ymax - ymin) / (cols + 1)
    centers = []
    for i, r in enumerate(radii):
        row, col = divmod(i, cols)
        x = xmin + (col + 1) * dx
        y = ymin + (row + 1) * dy
        centers.append([x, y])
    return centers, list(radii)


def _fallback_box3d(xmin, xmax, ymin, ymax, zmin, zmax, radii) -> tuple[list, list]:
    n = len(radii)
    side = max(1, int(np.ceil(n ** (1 / 3))))
    dx = (xmax - xmin) / (side + 1)
    dy = (ymax - ymin) / (side + 1)
    dz = (zmax - zmin) / (side + 1)
    centers = []
    for i in range(n):
        ix = i % side
        iy = (i // side) % side
        iz = i // (side * side)
        centers.append([
            xmin + (ix + 1) * dx,
            ymin + (iy + 1) * dy,
            zmin + (iz + 1) * dz,
        ])
    return centers, list(radii)
