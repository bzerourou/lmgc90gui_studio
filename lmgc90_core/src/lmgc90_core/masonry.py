"""Masonry wall layout — pure geometry, no pylmgc90.

Patterns mirror the legacy masonery_wizard / masonry_tab:
  Standard, Running Bond, Stack Bond, Flemish Bond,
  Paneresse simple, Paneresse double (3D-oriented; pure layout for Studio).

Each brick is a rigidPolygon (4 vertices) so it serialises and appears in pre.py.
Paneresse options are stored in wall_params for engine / pre.paneresse_* rebuild.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .entities import Avatar
from .pre import rigidPolygon, rigidPolyhedron
from .types import AvatarOrigin


@dataclass
class MasonryConfig:
    n_courses: int = 8
    n_columns: int = 5
    brick_lx: float = 0.20
    brick_ly: float = 0.065
    brick_lz: float = 0.10  # depth (3D / paneresse)
    joint: float = 0.010
    bond: str = "standard"  # standard | stack | running | flemish | paneresse_simple | paneresse_double
    origin_x: float = 0.0
    origin_y: float = 0.0
    origin_z: float = 0.0
    material_name: str = "brick"
    model_name: str = "rigid"
    color: str = "REEDx"
    group_name: Optional[str] = "mason"
    brick_name: str = "std"
    fill_ends: bool = False
    # paneresse (legacy masonry_tab — 3D)
    disposition: str = "paneresse"  # paneresse | boutisse | chant
    first_brick_type: str = "full"  # full | half | …
    pan_use_length: bool = False
    pan_length: float = 1.0
    pan_no_half: bool = False
    dimension: int = 2
    # post transforms
    translate: Optional[tuple[float, float, float]] = None
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


def _box_vertices(
    cx: float, cy: float, cz: float, lx: float, ly: float, lz: float,
) -> list[list[float]]:
    """Axis-aligned brick as 8 corners (rigidPolyhedron)."""
    hx, hy, hz = lx / 2.0, ly / 2.0, max(lz, 1e-6) / 2.0
    corners = []
    for sx in (-hx, hx):
        for sy in (-hy, hy):
            for sz in (-hz, hz):
                corners.append([cx + sx, cy + sy, cz + sz])
    return corners


def _normalize_bond(bond: str) -> str:
    b = (bond or "standard").lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "standard": "standard",
        "stack": "stack",
        "stack_bond": "stack",
        "running": "running",
        "running_bond": "running",
        "flemish": "flemish",
        "flemish_bond": "flemish",
        "paneresse_simple": "paneresse_simple",
        "paneresse_simple_(pylmgc90)": "paneresse_simple",
        "paneresse_double": "paneresse_double",
        "paneresse_double_(pylmgc90)": "paneresse_double",
        "paneressesimple": "paneresse_simple",
        "paneressedouble": "paneresse_double",
    }
    # UI labels
    raw = (bond or "").strip()
    if "paneresse" in raw.lower() and "double" in raw.lower():
        return "paneresse_double"
    if "paneresse" in raw.lower() and "simple" in raw.lower():
        return "paneresse_simple"
    return aliases.get(b, b)


def brick_centers(config: MasonryConfig) -> list[tuple[float, float, float, float, float]]:
    """Return (cx, cy, cz, lx, ly) for each brick."""
    lx, ly, lz, j = config.brick_lx, config.brick_ly, config.brick_lz, config.joint
    ox, oy, oz = config.origin_x, config.origin_y, config.origin_z
    bond = _normalize_bond(config.bond)
    pitch = lx + j
    out: list[tuple[float, float, float, float, float]] = []

    def add_row_standard(row: int, z: float = 0.0) -> None:
        row_offset = (lx / 2.0) if (row % 2 == 1) else 0.0
        if config.fill_ends and row % 2 == 1:
            hx = lx / 2.0
            out.append((ox + hx / 2.0, oy + row * (ly + j) + ly / 2.0, z, hx, ly))
            for col in range(config.n_columns):
                cx = ox + hx + j + col * pitch + lx / 2.0
                cy = oy + row * (ly + j) + ly / 2.0
                out.append((cx, cy, z, lx, ly))
            right0 = ox + hx + j + config.n_columns * pitch
            out.append((right0 + hx / 2.0, oy + row * (ly + j) + ly / 2.0, z, hx, ly))
        else:
            for col in range(config.n_columns):
                cx = ox + col * pitch + row_offset + lx / 2.0
                cy = oy + row * (ly + j) + ly / 2.0
                out.append((cx, cy, z, lx, ly))

    def add_wythe(z: float) -> None:
        """One leaf of paneresse — running-style with optional length mode."""
        disp = (config.disposition or "paneresse").lower()
        # disposition changes which face is the length in-plane
        blx, bly = lx, ly
        if disp == "boutisse":
            blx, bly = ly, lx  # rotated footprint
        elif disp == "chant":
            blx, bly = lz if lz > 0 else lx / 2.0, ly

        if config.pan_use_length and config.pan_length > 0:
            # pack bricks along length
            cursor = ox
            target = ox + float(config.pan_length)
            col = 0
            while cursor + 1e-12 < target:
                use_half = False
                if config.first_brick_type.lower().startswith("half") and col == 0:
                    use_half = True
                if not config.pan_no_half and col == 0 and config.n_courses > 0:
                    pass
                w = blx / 2.0 if use_half else blx
                if cursor + w > target + 1e-12:
                    w = max(target - cursor, blx * 0.25)
                for row in range(config.n_courses):
                    row_off = (w / 2.0) if (row % 2 == 1 and not config.pan_no_half) else 0.0
                    cx = cursor + w / 2.0 + row_off
                    cy = oy + row * (bly + j) + bly / 2.0
                    out.append((cx, cy, z, w if row % 2 == 0 or config.pan_no_half else blx, bly))
                cursor += w + j
                col += 1
        else:
            first_half = config.first_brick_type.lower().startswith("half")
            for row in range(config.n_courses):
                row_off = 0.0
                if not config.pan_no_half and row % 2 == 1:
                    row_off = blx / 2.0
                n_col = config.n_columns
                for col in range(n_col):
                    w = blx
                    if first_half and col == 0 and row % 2 == 0:
                        w = blx / 2.0
                    cx = ox + col * (blx + j) + row_off + w / 2.0
                    cy = oy + row * (bly + j) + bly / 2.0
                    out.append((cx, cy, z, w, bly))

    if bond == "stack":
        for row in range(config.n_courses):
            for col in range(config.n_columns):
                cx = ox + col * pitch + lx / 2.0
                cy = oy + row * (ly + j) + ly / 2.0
                out.append((cx, cy, oz, lx, ly))

    elif bond == "running":
        for row in range(config.n_courses):
            row_offset = (lx / 3.0) * (row % 3)
            for col in range(config.n_columns):
                cx = ox + col * pitch + row_offset + lx / 2.0
                cy = oy + row * (ly + j) + ly / 2.0
                out.append((cx, cy, oz, lx, ly))

    elif bond == "flemish":
        for row in range(config.n_courses):
            x_cursor = ox
            for col in range(config.n_columns):
                brick_lx = lx if (row + col) % 2 == 0 else lx / 2.0
                cx = x_cursor + brick_lx / 2.0
                cy = oy + row * (ly + j) + ly / 2.0
                out.append((cx, cy, oz, brick_lx, ly))
                x_cursor += brick_lx + j

    elif bond == "paneresse_simple":
        add_wythe(oz)

    elif bond == "paneresse_double":
        # two parallel leaves separated by depth + joint (legacy double thickness)
        depth = (lz if lz > 0 else lx) + j
        add_wythe(oz)
        add_wythe(oz + depth)

    else:  # standard
        for row in range(config.n_courses):
            add_row_standard(row, oz)

    return out


def expand_masonry(config: MasonryConfig) -> list[Avatar]:
    if config.n_courses < 1 or config.n_columns < 1:
        raise ValueError("n_courses and n_columns must be >= 1")
    if config.brick_lx <= 0 or config.brick_ly <= 0:
        raise ValueError("brick sizes must be positive")

    bond = _normalize_bond(config.bond)
    if bond in ("paneresse_simple", "paneresse_double") and int(config.dimension) != 3:
        raise ValueError(
            "Les appareils paneresse simple / double nécessitent un projet 3D "
            "(comme l'ancien assistant)."
        )

    centers = brick_centers(config)
    copies = [(0.0, 0.0, 0.0)]
    if config.copy_offset and config.n_copies > 0:
        dx, dy, dz = (
            float(config.copy_offset[0]),
            float(config.copy_offset[1]),
            float(config.copy_offset[2]) if len(config.copy_offset) > 2 else 0.0,
        )
        copies = [(i * dx, i * dy, i * dz) for i in range(config.n_copies + 1)]

    tx = ty = tz = 0.0
    if config.translate:
        tx = float(config.translate[0])
        ty = float(config.translate[1])
        tz = float(config.translate[2]) if len(config.translate) > 2 else 0.0

    avatars: list[Avatar] = []
    for off_x, off_y, off_z in copies:
        for cx, cy, cz, blx, bly in centers:
            x = cx + tx + off_x
            y = cy + ty + off_y
            z = cz + tz + off_z
            if int(config.dimension) == 3:
                lz = float(config.brick_lz) if config.brick_lz > 0 else blx * 0.5
                center = [x, y, z]
                box = _box_vertices(x, y, z, blx, bly, lz)
                av = rigidPolyhedron(
                    center=center,
                    model=config.model_name,
                    material=config.material_name,
                    color=config.color,
                    generation_type="vertices",
                    vertices=box,
                    nb_vertices=len(box),
                )
            else:
                center = [x, y]
                av = rigidPolygon(
                    center=center,
                    model=config.model_name,
                    material=config.material_name,
                    color=config.color,
                    generation_type="vertices",
                    vertices=_rect_vertices(x, y, blx, bly),
                )
            av.origin = AvatarOrigin.FACTORY
            av.wall_params = {
                "l": blx,
                "h": bly,
                "lz": config.brick_lz,
                "brick_name": config.brick_name,
                "masonry": True,
                "bond": bond,
                "disposition": config.disposition,
                "first_brick_type": config.first_brick_type,
                "pan_use_length": config.pan_use_length,
                "pan_length": config.pan_length,
                "pan_no_half": config.pan_no_half,
                "engine_layout": bond if bond.startswith("paneresse") else bond,
            }
            avatars.append(av)
    return avatars
