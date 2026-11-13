from types import SimpleNamespace

import pytest

from lmgc90_engine.schema import introspection, snapshot
<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> 10e38cb (fix some bugs)
from lmgc90_engine.schema.materials import material_schema_catalog


@pytest.fixture(autouse=True)
def clear_catalog_cache():
    introspection.clear_compatibility_catalog_cache()
    yield
    introspection.clear_compatibility_catalog_cache()
<<<<<<< HEAD
>>>>>>> 634bb2a (new version 0.7.6)
=======
>>>>>>> 10e38cb (fix some bugs)


def test_inspect_runtime_does_not_use_compatibility_snapshot(monkeypatch):
    modules = {
        "pylmgc90": SimpleNamespace(__version__="2026.1"),
        "pylmgc90.pre": SimpleNamespace(),
        "pylmgc90.chipy": SimpleNamespace(),
    }
    monkeypatch.setattr(
        introspection.importlib, "import_module", lambda name: modules[name],
    )
    monkeypatch.setattr(
        introspection.importlib.metadata, "version", lambda _: "2026.1",
    )
    monkeypatch.setattr(introspection, "_runtime_catalogs", lambda: {})
    monkeypatch.setattr(
        introspection, "load_compatibility_catalogs",
        lambda: pytest.fail("runtime inspection must not use snapshot fallback"),
    )

    result = introspection.inspect_runtime()

    assert result["available"] is True
    assert result["catalogs"] == {}
    assert result["catalog_source"] == "UNAVAILABLE"


<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> 10e38cb (fix some bugs)
def test_runtime_catalogs_include_all_public_data_structures(monkeypatch):
    tree = SimpleNamespace(
        root="kinematic",
        childs=[SimpleNamespace(root="small", childs=[])],
    )
    module = SimpleNamespace(
        bodyType2contactor={"RBDY2": ["DISKx"]},
        geo2contactor={"Point": ["DISKx"]},
        checkBulkBehavOptions={"ELAS": tree},
        commandOptions={"NEW MECAx SETS": ["mecax_sets"]},
        _private_catalog={"hidden": True},
        helper=lambda: None,
        stop_mode="t",
    )
    monkeypatch.setattr(introspection.importlib, "import_module", lambda _: module)

    catalogs = introspection._runtime_catalogs()

    assert catalogs == {
        "bodyType2contactor": {"RBDY2": ["DISKx"]},
        "checkBulkBehavOptions": {
            "ELAS": {
                "root": "kinematic",
                "children": [{"root": "small", "children": []}],
            },
        },
        "commandOptions": {"NEW MECAx SETS": ["mecax_sets"]},
        "geo2contactor": {"Point": ["DISKx"]},
    }


def test_missing_snapshot_index_uses_core_fallback(monkeypatch):
    def missing_snapshot(_version=None):
        raise FileNotFoundError("bundled pylmgc90 capability index is missing")

    monkeypatch.setattr(introspection, "_runtime_catalogs", lambda: {})
    monkeypatch.setattr(introspection, "_installed_runtime_version", lambda: None)
    monkeypatch.setattr(introspection, "load_capability_snapshot", missing_snapshot)
    introspection.clear_compatibility_catalog_cache()

    try:
        assert introspection.load_compatibility_catalogs() == {}
        assert introspection.compatibility_catalog_source() == "FALLBACK"
        assert material_schema_catalog()["source"] == "FALLBACK"
    finally:
        introspection.clear_compatibility_catalog_cache()


def test_snapshot_catalogs_take_precedence_over_runtime(monkeypatch):
    monkeypatch.setattr(introspection, "_installed_runtime_version", lambda: "2026.1")
    monkeypatch.setattr(
        introspection, "_snapshot_catalogs", lambda _version: {"value": "snapshot"},
    )
    monkeypatch.setattr(
        introspection, "_runtime_catalogs", lambda: {"value": "introspection"},
    )
    introspection.clear_compatibility_catalog_cache()

    try:
        assert introspection.compatibility_catalog_source() == "SNAPSHOT"
        assert introspection.load_compatibility_catalogs() == {"value": "snapshot"}
    finally:
        introspection.clear_compatibility_catalog_cache()


<<<<<<< HEAD
>>>>>>> 634bb2a (new version 0.7.6)
=======
>>>>>>> 10e38cb (fix some bugs)
def test_build_snapshot_rejects_missing_runtime_catalogs(monkeypatch):
    monkeypatch.setattr(snapshot, "inspect_runtime", lambda: {
        "available": True,
        "version": "2026.1",
        "apis": {},
        "catalogs": {},
        "catalog_source": "UNAVAILABLE",
    })

    with pytest.raises(RuntimeError, match="refusing to copy compatibility snapshot"):
        snapshot.build_capability_snapshot()


def test_write_snapshot_invalidates_compatibility_catalog_cache(
    tmp_path, monkeypatch,
):
    loads = []

    def snapshot_catalogs(version=None):
        loads.append(version)
        return {"value": "cached" if len(loads) == 1 else "refreshed"}

    monkeypatch.setattr(introspection, "_runtime_catalogs", lambda: {})
    monkeypatch.setattr(
        introspection, "_installed_runtime_version", lambda: "2026.1",
    )
    monkeypatch.setattr(
        introspection,
        "_snapshot_catalogs",
        snapshot_catalogs,
    )
    introspection.clear_compatibility_catalog_cache()
    assert introspection.load_compatibility_catalogs() == {"value": "cached"}

    monkeypatch.setattr(snapshot, "build_capability_snapshot", lambda: {
        "schema_version": snapshot.SNAPSHOT_SCHEMA_VERSION,
        "runtime": {"name": "pylmgc90", "version": "2026.1"},
        "apis": {},
        "catalogs": {"value": "new-runtime-data"},
    })

    snapshot.write_capability_snapshot(tmp_path)

    assert introspection.compatibility_catalog_source() == "SNAPSHOT"
    assert introspection.load_compatibility_catalogs() == {"value": "refreshed"}
    assert loads == ["2026.1", "2026.1"]
