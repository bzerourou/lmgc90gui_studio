# ============================================================================
# compute_script.py — lmgc90_core
# ============================================================================
"""Full chipy ``command.py`` generator (no Qt, no engine).

Pure function of ``Project`` + parameter dict (Compute / ChipyRoutines options).
GUI and engine call this via ``emit_chipy`` / ``generate_command_script``.
"""
from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any, Dict, Optional, Protocol

from .project import Project


class _JournalLike(Protocol):
    def warning(self, msg: str) -> None: ...
