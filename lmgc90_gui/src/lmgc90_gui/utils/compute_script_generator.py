"""Deprecated shim — generator lives in ``lmgc90_core.compute_script``.

Architecture: GUI must not own script generation. Prefer::

    from lmgc90_core import emit_chipy, generate_command_script
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from lmgc90_core.compute_script import (
    ComputeScriptGenerator as _CoreGen,
    generate_command_script,
    write_command_script,
)


class ComputeScriptGenerator(_CoreGen):
    """Compatibility wrapper accepting legacy ``controller=``."""

    def __init__(self, controller=None, project=None, **kw):
        if project is None and controller is not None:
            project = getattr(controller, "project", None)
        journal = None
        if controller is not None:
            journal = getattr(controller, "journal", None)
        super().__init__(project, journal=journal, **kw)


__all__ = [
    "ComputeScriptGenerator",
    "generate_command_script",
    "write_command_script",
]
