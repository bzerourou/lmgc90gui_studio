from types import SimpleNamespace

import pytest

from lmgc90_engine.schema import introspection, snapshot
from lmgc90_engine.schema.materials import material_schema_catalog


@pytest.fixture(autouse=True)
def clear_catalog_cache():
    introspection.clear_compatibility_catalog_cache()
    yield
    introspection.clear_compatibility_catalog_cache()


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