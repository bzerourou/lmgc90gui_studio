"""Dynamic form helpers shared by rich tabs (material / law / avatar params)."""
from __future__ import annotations

from typing import Any, Callable, Optional


def build_schema_widgets(parent_layout, schema: tuple, *, make_line, make_spin, make_combo=None):
    """Create widgets for a schema list of (name, default, kind).

    Returns dict name → widget.
    """
    widgets: dict[str, Any] = {}
    for name, default, kind in schema:
        if kind == "float":
            w = make_spin(float(default) if default is not None else 0.0)
        elif kind == "int":
            w = make_spin(int(default) if default is not None else 0, integer=True)
        elif kind == "choice" and make_combo is not None:
            w = make_combo(list(default) if isinstance(default, (list, tuple)) else [default])
        else:
            w = make_line(str(default) if default is not None else "")
        parent_layout.addRow(name, w)
        widgets[name] = w
    return widgets


def read_schema_values(widgets: dict[str, Any], schema: tuple) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, default, kind in schema:
        w = widgets.get(name)
        if w is None:
            continue
        if kind == "float":
            out[name] = float(w.value()) if hasattr(w, "value") else float(w.text())
        elif kind == "int":
            out[name] = int(w.value()) if hasattr(w, "value") else int(w.text())
        elif hasattr(w, "currentText"):
            out[name] = w.currentText()
        elif hasattr(w, "text"):
            out[name] = w.text().strip()
        elif hasattr(w, "isChecked"):
            out[name] = bool(w.isChecked())
    return out


def clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.deleteLater()
        child = item.layout()
        if child is not None:
            clear_layout(child)


# Avatar-type → ordered param fields (beyond center / material / model / color)
# kind: float | int | bool | str | vertices
AVATAR_PARAM_SCHEMA: dict[str, tuple[tuple[str, object, str], ...]] = {
    "rigidDisk": (("r", 0.1, "float"), ("is_Hollow", False, "bool")),
    "rigidSphere": (("r", 0.1, "float"), ("is_Hollow", False, "bool")),
    "rigidDiscreteDisk": (("r", 0.1, "float"),),
    "rigidJonc": (("axe1", 0.2, "float"), ("axe2", 0.05, "float")),
    "rigidPolygon": (
        ("generation_type", "regular", "str"),
        ("nb_vertices", 6, "int"),
        ("radius", 0.1, "float"),
        ("vertices", "", "str"),  # "x1,y1; x2,y2; ..."
    ),
    "rigidOvoidPolygon": (("radius", 0.1, "float"), ("vertices", "", "str")),
    "rigidCluster": (("r", 0.05, "float"), ("nb_disk", 3, "int")),
    "rigidCylinder": (("r", 0.1, "float"), ("h", 0.3, "float"), ("is_Hollow", False, "bool")),
    "rigidPlan": (("axe1", 1.0, "float"), ("axe2", 1.0, "float"), ("axe3", 0.1, "float")),
    "rigidPolyhedron": (
        ("generation_type", "regular", "str"),
        ("nb_vertices", 8, "int"),
        ("radius", 0.1, "float"),
        ("vertices", "", "str"),
    ),
    "smoothWall": (("l", 1.0, "float"), ("h", 0.1, "float"), ("nb_polyg", 16, "int")),
    "roughWall": (("l", 1.0, "float"), ("r", 0.02, "float"), ("nb_vertex", 10, "int")),
    "fineWall": (("l", 1.0, "float"), ("r", 0.02, "float"), ("nb_vertex", 10, "int")),
    "granuloRoughWall": (
        ("l", 1.0, "float"), ("rmin", 0.01, "float"), ("rmax", 0.03, "float"),
        ("nb_vertex", 10, "int"),
    ),
    "roughWall3D": (("lx", 1.0, "float"), ("ly", 1.0, "float"), ("lz", 0.1, "float")),
    "granuloRoughWall3D": (
        ("lx", 1.0, "float"), ("ly", 1.0, "float"), ("lz", 0.1, "float"),
        ("rmin", 0.01, "float"), ("rmax", 0.03, "float"),
    ),
    "emptyAvatar": (),
    "mesh": (
        ("lx", 0.15, "float"), ("ly", 0.30, "float"),
        ("nx", 4, "int"), ("ny", 8, "int"),
        ("mesh_type", "2T3", "str"),
    ),
}

DOF_PARAM_SCHEMA: dict[str, tuple[tuple[str, object, str], ...]] = {
    "imposeDrivenDof": (
        ("component", "1,2", "str"),
        ("dofty", "vlocy", "str"),
        ("ct", 0.0, "float"),
        ("ramp", 0.0, "float"),
    ),
    "imposeInitValue": (
        ("component", "1,2", "str"),
        ("dofty", "vlocy", "str"),
        ("ct", 0.0, "float"),
    ),
    "translate": (("dx", 0.0, "float"), ("dy", 0.0, "float"), ("dz", 0.0, "float")),
    "rotate": (
        ("axis_x", 0.0, "float"), ("axis_y", 0.0, "float"), ("axis_z", 1.0, "float"),
        ("angle", 0.0, "float"),
    ),
    "addContactors": (
        ("shape", "DISKx", "str"),
        ("color", "BLUEx", "str"),
        ("group", "", "str"),
    ),
}


def parse_vertices(text: str) -> Optional[list[list[float]]]:
    text = (text or "").strip()
    if not text:
        return None
    pts = []
    for part in text.replace(";", "\n").split("\n"):
        part = part.strip()
        if not part:
            continue
        coords = [float(x) for x in part.replace(",", " ").split()]
        if len(coords) < 2:
            raise ValueError(f"bad vertex line: {part!r}")
        pts.append(coords)
    return pts or None


def parse_components(text: str):
    parts = [p.strip() for p in str(text).split(",") if p.strip()]
    vals = []
    for p in parts:
        vals.append(int(p) if p.lstrip("-").isdigit() else p)
    if len(vals) == 1:
        return vals[0]
    return vals
