"""The core must import with nothing but the stdlib and numpy."""
from __future__ import annotations

import ast
import os
from pathlib import Path
import subprocess
import sys

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


def test_core_dictionary_modules_do_not_probe_pylmgc90():
    code = """
import sys

class BlockPylmgc:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "pylmgc90" or fullname.startswith("pylmgc90."):
            raise AssertionError(f"core attempted pylmgc90 import: {fullname}")

sys.meta_path.insert(0, BlockPylmgc())
import lmgc90_core
from lmgc90_core import lmgc_dicts, types
assert types.MATERIAL_OPTIONS == types._FALLBACK_MATERIAL_OPTIONS
assert all(source == "manuel" for source in lmgc_dicts.SOURCES.values())
"""
    env = os.environ.copy()
    source_path = str(ROOT.parent)
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in (source_path, env.get("PYTHONPATH", "")) if part
    )
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT.parents[2],
        env=env,
        check=True,
    )
