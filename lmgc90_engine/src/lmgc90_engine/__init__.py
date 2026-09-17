"""lmgc90_engine — materialize lmgc90_core.Project into pylmgc90.pre.

    from lmgc90_core import Project, pre
    from lmgc90_engine import EngineSession

    p = Project(name="demo", dimension=2)
    ...
    session = EngineSession(p)
    session.emit_pre_script("pre.py")       # always works
    if session.available():
        session.materialize()
        session.write_datbox("DATBOX")
"""
from __future__ import annotations

from .datbox import export_pre_script, write_datbox
from .errors import (
    DatboxError,
    EngineError,
    MaterializationError,
    PylmgcNotAvailable,
    UnknownBodyError,
)
from .granulo import deposit_population
from .materialize import MaterializedScene, materialize_project
from .session import EngineSession

__version__ = "0.1.0"
__all__ = [
    "EngineSession",
    "MaterializedScene",
    "materialize_project",
    "write_datbox",
    "export_pre_script",
    "deposit_population",
    "EngineError",
    "PylmgcNotAvailable",
    "MaterializationError",
    "UnknownBodyError",
    "DatboxError",
    "__version__",
]
