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
assert types.MATERIAL_OPTIONS
assert types._FALLBACK_MATERIAL_OPTIONS
assert all(source != "snapshot:unavailable" for source in lmgc_dicts.SOURCES.values())
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


def test_core_falls_back_when_snapshot_is_missing_or_empty():
    code = """
import importlib
import warnings

import lmgc90_core
import lmgc90_core.lmgc_dicts as dictionaries
import lmgc90_core.types as types
import lmgc90_core.validate as validation
from lmgc90_core import Model, ValidationError, pre

for loader in (
    lambda: (_ for _ in ()).throw(FileNotFoundError("missing snapshot")),
    lambda: {
        "runtime": {"version": "test"},
        "catalogs": {
            "rigidElements": [],
            "dimension2contactor": {},
            "element2ddl": {},
            "dimension2element": {},
            "bodyType2contactor": {},
            "contactorPair2TactBehav": {},
            "tactBehavOptions": {},
            "bulkBehavOptions": {},
            "modelOptions": {},
        },
    },
):
    dictionaries.load_capability_snapshot = loader
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        importlib.reload(dictionaries)
    importlib.reload(types)
    importlib.reload(validation)

    assert types.RIGID_ELEMENTS_2D == ("Rxx2D",)
    assert types.CONTACTORS_RIGID_2D
    assert validation.compatible_contactors(types.AvatarType.RIGID_DISK, 2)
    assert dictionaries.ELEMENTS_BY_PHYSICS["MECAx"][2]

    model = Model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2)
    validation.validate_model(model)
    avatar = pre.rigidDisk(r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL")
    validation.validate_avatar(avatar, model)

    bad_model = Model(name="bad", physics="MECAx", element="Rxx3D", dimension=2)
    try:
        validation.validate_model(bad_model)
        raise AssertionError("invalid fallback model was accepted")
    except ValidationError:
        pass
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
