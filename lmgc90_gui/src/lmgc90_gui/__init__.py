"""lmgc90_gui — PyQt6 client of lmgc90_core + lmgc90_engine."""
from __future__ import annotations

__version__ = "0.7.3"

from .controller.project_controller import ProjectController

__all__ = ["ProjectController", "__version__"]
