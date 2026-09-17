"""Engine may import pylmgc90 only behind try/except or in functions — never at module top
in a way that breaks import of the package without pylmgc."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "lmgc90_engine"


def test_package_imports_without_pylmgc():
    """Importing lmgc90_engine must succeed even if pylmgc90 is absent."""
    import lmgc90_engine  # noqa: F401
    from lmgc90_engine import EngineSession, materialize_project  # noqa: F401


def test_no_top_level_pylmgc_import():
    """No module may do `from pylmgc90 import ...` or `import pylmgc90` at top level."""
    hits = []
    for path in ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:  # only top-level statements
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "pylmgc90" or alias.name.startswith("pylmgc90."):
                        hits.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and (
                    node.module == "pylmgc90" or node.module.startswith("pylmgc90.")
                ):
                    hits.append(f"{path.name}: from {node.module}")
    assert hits == [], "top-level pylmgc90 imports forbidden:\n" + "\n".join(hits)
