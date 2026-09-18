"""Emit chipy ``command.py`` — full generator (see ``compute_script``).

Architecture: pure core. No Qt. No pylmgc90.
"""
from __future__ import annotations

from typing import Any, Optional

from .compute_script import generate_command_script
from .project import Project

# Backward-compatible defaults (subset); full defaults live in ComputeScriptGenerator
_DEFAULTS: dict[str, Any] = {
    "dt": 1e-3,
    "nb_steps": 1000,
    "theta": 0.5,
    "tol": 1.666e-4,
    "relax": 1.0,
    "norm": "Quad ",
    "gs_it1": 50,
    "gs_it2": 1000,
    "solver_type": "Stored_Delassus_Loops         ",
    "freq_write": 50,
    "freq_display": 50,
    "dimension": None,
    "deformable": False,
    "disable_log": True,
}


def emit_chipy(project: Project, **params: Any) -> str:
    """Generate full ``command.py`` text for *project*.

    Accepts all ChipyRoutines / Compute-tab keys (``use_DKDKx``,
    ``vis_entries``, ``use_restart``, …). Unknown keys are ignored by the
    generator defaults merge.
    """
    p = dict(_DEFAULTS)
    p.update({k: v for k, v in params.items() if v is not None})
    if p.get("dimension") is None:
        p["dimension"] = project.dimension
    return generate_command_script(project, p)
