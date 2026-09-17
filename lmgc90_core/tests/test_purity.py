"""The core must import with nothing but the stdlib and numpy."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "lmgc90_core"
FORBIDDEN = {"pylmgc90", "PyQt6", "PyQt5", "pyvista", "pyvistaqt", "gmsh", "vtk"}


def test_no_forbidden_imports():
    hits = []
    for path in ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            for n in names:
                if n in FORBIDDEN:
                    hits.append(f"{path.name}: import {n}")
    assert hits == [], "lmgc90_core is not headless:\n" + "\n".join(hits)


def test_package_imports_without_qt():
    import lmgc90_core
    assert isinstance(lmgc90_core.__version__, str) and lmgc90_core.__version__
