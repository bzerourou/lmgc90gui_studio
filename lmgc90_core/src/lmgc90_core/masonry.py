"""Masonry wall layout — pure geometry, no pylmgc90.

Patterns mirror the legacy masonery_wizard:
  Standard, Running Bond, Stack Bond, Flemish Bond.

Each brick is a rigidPolygon (4 vertices) so it serialises and appears in pre.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .entities import Avatar
from .pre import rigidPolygon
from .types import AvatarOrigin


@dataclass
class MasonryConfig:
    n_courses: int = 8
    n_columns: int = 5
    brick_lx: float = 0.20
    brick_ly: float = 0.065
    brick_lz: float = 0.10  # depth for 3D metadata only
    joint: float = 0.010
    bond: str = "standard"  # standard | stack | running | flemish
    origin_x: float = 0.0
    origin_y: float = 0.0
    origin_z: float = 0.0
    material_name: str = "brick"
    model_name: str = "rigid"
    color: str = "REEDx"
    group_name: Optional[str] = "mason"
    brick_name: str = "std"
    fill_ends: bool = False  # legacy Standard did NOT always fill ends
    # post transforms
    translate: Optional[tuple[float, float, float]] = None
    # rotate not applied in pure expand (kept for metadata)
    rotate_deg: float = 0.0
    rotate_axis: str = "Z"
    rotate_center: Optional[tuple[float, float, float]] = None
    copy_offset: Optional[tuple[float, float, float]] = None
    n_copies: int = 0

    def to_dict(self) -> dict:
        d = {}
        for k in self.__dataclass_fields__:  # type: ignore
            v = getattr(self, k)
            if v is not None:
                d[k] = v
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "MasonryConfig":
        fields = set(cls.__dataclass_fields__)  # type: ignore
        return cls(**{k: data[k] for k in fields if k in data})


def _rect_vertices(cx: float, cy: float, lx: float, ly: float) -> list[list[float]]:
    hx, hy = lx / 2.0, ly / 2.0
    return [
        [cx - hx, cy - hy],
        [cx + hx, cy - hy],
        [cx + hx, cy + hy],
        [cx - hx, cy + hy],
    ]


def brick_centers(config: MasonryConfig) -> list[tuple[float, float, float, float]]:
    """Return (cx, cy, lx, ly) for each brick — same conventions as masonery_wizard."""
    lx, ly, j = config.brick_lx, config.brick_ly, config.joint
    ox, oy = config.origin_x, config.origin_y
    bond = (config.bond or "standard").lower().replace(" ", "_")
    # accept aliases from the UI
    aliases = {
        "standard": "standard",
        "stack": "stack",
        "stack_bond": "stack",
        "running": "running",
        "running_bond": "running",
        "flemish": "flemish",
        "flemish_bond": "flemish",
    }
    bond = aliases.get(bond, bond)
    out: list[tuple[float, float, float, float]] = []
    pitch = lx + j

    if bond == "stack":
        for row in range(config.n_courses):
            for col in range(config.n_columns):
                cx = ox + col * pitch + lx / 2.0
                cy = oy + row * (ly + j) + ly / 2.0
                out.append((cx, cy, lx, ly))

    elif bond == "running":
        for row in range(config.n_courses):
            row_offset = (row % 3) * (lx / 3.0)
            for col in range(config.n_columns):
                cx = ox + col * pitch + row_offset + lx / 2.0
                cy = oy + row * (ly + j) + ly / 2.0
                out.append((cx, cy, lx, ly))

    elif bond == "flemish":
        for row in range(config.n_courses):
            x_cursor = ox
            for col in range(config.n_columns):
                brick_lx = lx if (row + col) % 2 == 0 else lx / 2.0
                cx = x_cursor + brick_lx / 2.0
                cy = oy + row * (ly + j) + ly / 2.0
                out.append((cx, cy, brick_lx, ly))
                x_cursor += brick_lx + j

    else:  # standard — half-brick offset on odd rows (legacy masonery_wizard)
        for row in range(config.n_courses):
            row_offset = (lx / 2.0) if (row % 2 == 1) else 0.0
            if config.fill_ends and row % 2 == 1:
                hx = lx / 2.0
                out.append((ox + hx / 2.0, oy + row * (ly + j) + ly / 2.0, hx, ly))
                for col in range(config.n_columns):
                    cx = ox + hx + j + col * pitch + lx / 2.0
                    cy = oy + row * (ly + j) + ly / 2.0
                    out.append((cx, cy, lx, ly))
                right0 = ox + hx + j + config.n_columns * pitch
                out.append((right0 + hx / 2.0, oy + row * (ly + j) + ly / 2.0, hx, ly))
            else:
                for col in range(config.n_columns):
                    cx = ox + col * pitch + row_offset + lx / 2.0
                    cy = oy + row * (ly + j) + ly / 2.0
                    out.append((cx, cy, lx, ly))
    return out


def expand_masonry(config: MasonryConfig) -> list[Avatar]:
    if config.n_courses < 1 or config.n_columns < 1:
        raise ValueError("n_courses and n_columns must be >= 1")
    if config.brick_lx <= 0 or config.brick_ly <= 0:
        raise ValueError("brick sizes must be positive")

    centers = brick_centers(config)
    # optional copies
    copies = [ (0.0, 0.0) ]
    if config.copy_offset and config.n_copies > 0:
        dx, dy = config.copy_offset[0], config.copy_offset[1]
        copies = [(i * dx, i * dy) for i in range(config.n_copies + 1)]

    tx = ty = 0.0
    if config.translate:
        tx, ty = config.translate[0], config.translate[1]

    avatars: list[Avatar] = []
    for off_x, off_y in copies:
        for cx, cy, blx, bly in centers:
            x = cx + tx + off_x
            y = cy + ty + off_y
            av = rigidPolygon(
                center=[x, y],
                model=config.model_name,
                material=config.material_name,
                color=config.color,
                generation_type="vertices",
                vertices=_rect_vertices(x, y, blx, bly),
            )
            av.origin = AvatarOrigin.FACTORY
            av.wall_params = {
                "l": blx, "h": bly, "lz": config.brick_lz,
                "brick_name": config.brick_name,
                "masonry": True,
                "bond": config.bond,
            }
            avatars.append(av)
    return avatars
