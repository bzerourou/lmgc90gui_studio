"""Write a real DATBOX from a MaterializedScene (or fall back to script emission)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from lmgc90_core.numpy_compat import patch_numpy_cross
from lmgc90_core.pre_script import emit_pre
from lmgc90_core.project import Project

from .errors import DatboxError, PylmgcNotAvailable
from .materialize import MaterializedScene


def write_datbox(
    scene: MaterializedScene,
    path: Union[str, Path],
    *,
    dimension: Optional[int] = None,
) -> Path:
    """Call pre.writeDatbox on the live containers.

    Applies NumPy 2 / 2D ``np.cross`` compatibility patch before writing.
    """
    try:
        from pylmgc90 import pre
    except ImportError as exc:
        raise PylmgcNotAvailable(
            "pylmgc90 is required for live DATBOX. "
            "Use export_pre_script() or emit_pre_script() instead."
        ) from exc

    patch_numpy_cross()

    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    dim = int(dimension if dimension is not None else scene.dimension)

    try:
        pre.writeDatbox(
            dim=dim,
            mats=scene.materials_container,
            mods=scene.models_container,
            tacts=scene.tacts_container,
            sees=scene.sees_container,
            bodies=scene.bodies_container,
            post=scene.posts_container,
            datbox_path=str(out),
        )
    except TypeError:
        import os
        cwd = Path.cwd()
        try:
            os.chdir(out)
            pre.writeDatbox(
                dim=dim,
                mats=scene.materials_container,
                mods=scene.models_container,
                tacts=scene.tacts_container,
                sees=scene.sees_container,
                bodies=scene.bodies_container,
                post=scene.posts_container,
            )
        finally:
            os.chdir(cwd)
    except Exception as exc:
        raise DatboxError(f"writeDatbox failed: {exc}") from exc

    return out


def export_pre_script(project: Project, path: Union[str, Path]) -> Path:
    """Always available: write the auditable pre.py from core (no pylmgc needed)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(emit_pre(project), encoding="utf-8")
    return out


def _parse_cell_phases(project: Project) -> dict:
    """Parse ``project.dynamic_vars['cell_phases']`` (dict or repr-string)."""
    raw = (project.dynamic_vars or {}).get("cell_phases")
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        import ast as _ast
        try:
            val = _ast.literal_eval(raw)
            return val if isinstance(val, dict) else {}
        except Exception:
            return {}
    return {}


def write_cell_dual_datbox(
    scene: MaterializedScene,
    project: Project,
    base_path: Union[str, Path],
) -> dict[str, Path]:
    """Write DATBOX_SPRD and DATBOX_STBL under *base_path* (cell adhesion).

    Both folders receive the current materialized scene (geometry + DOF as built).
    Phase stiffness tables and timing are written to ``PHASES.json`` for the
    solver / chipy scripts. Full law re-materialization per phase can be added
    later without changing this layout.
    """
    import json

    base = Path(base_path)
    base.mkdir(parents=True, exist_ok=True)
    phases = _parse_cell_phases(project)
    sprd_name = (phases.get("sprd") or {}).get("path", "DATBOX_SPRD")
    stbl_name = (phases.get("stbl") or {}).get("path", "DATBOX_STBL")
    if isinstance(sprd_name, str) and "/" not in sprd_name:
        sprd_path = base / sprd_name
    else:
        sprd_path = base / "DATBOX_SPRD"
    if isinstance(stbl_name, str) and "/" not in stbl_name:
        stbl_path = base / stbl_name
    else:
        stbl_path = base / "DATBOX_STBL"

    dim = int(getattr(project, "dimension", scene.dimension) or scene.dimension)
    p1 = write_datbox(scene, sprd_path, dimension=dim)
    p2 = write_datbox(scene, stbl_path, dimension=dim)

    meta_path = base / "PHASES.json"
    meta = {
        "wave": 5,
        "phases": phases,
        "datbox_sprd": str(p1),
        "datbox_stbl": str(p2),
        "note": (
            "Geometry/DOF written to both DATBOX; stiff_pen/pstr_pen in phases "
            "are for command.py / recalibration of tact_behav before each run."
        ),
    }
    meta_path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    # also emit pre scripts for audit
    export_pre_script(project, base / "pre_cell.py")
    return {"DATBOX_SPRD": p1, "DATBOX_STBL": p2, "PHASES": meta_path}
