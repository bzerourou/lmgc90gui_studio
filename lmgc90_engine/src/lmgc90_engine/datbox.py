"""Write a real DATBOX from a MaterializedScene (or fall back to script emission)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

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

    Parameters
    ----------
    scene : MaterializedScene
        Result of materialize_project.
    path : path-like
        Destination directory (LMGC90 convention: folder containing DATBOX files).
    dimension : optional override; defaults to scene.dimension.
    """
    try:
        from pylmgc90 import pre
    except ImportError as exc:
        raise PylmgcNotAvailable("pylmgc90 required for write_datbox") from exc

    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    dim = dimension if dimension is not None else scene.dimension

    try:
        pre.writeDatbox(
            dim=dim,
            mats=scene.materials_container,
            mods=scene.models_container,
            tacts=scene.tacts_container,
            sees=scene.sees_container,
            bodies=scene.bodies_container,
            post=scene.posts_container,
            # some versions accept a path / datbox_path keyword
        )
    except TypeError:
        # older signature without explicit path — DATBOX is written CWD-relative
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
