"""Emit chipy ``command.py`` — full generator (see ``compute_script``).

Architecture: pure core. No Qt. No pylmgc90.
"""
from __future__ import annotations

from typing import Any

from .project import Project
from .compute_script import generate_command_script


def emit_chipy(project: Project, **params: Any) -> str:
    """Generate full ``command.py`` text for *project*.

    Accepts all ChipyRoutines / Compute-tab keys (``use_DKDKx``,
    ``vis_entries``, ``use_restart``, …). Unknown keys are ignored by the
    generator defaults merge.
    """
    p = {k: v for k, v in params.items() if v is not None}
    if p.get("dimension") is None:
        p["dimension"] = project.dimension

    return generate_command_script(project, p)