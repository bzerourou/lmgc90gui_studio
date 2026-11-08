from lmgc90_core import lmgc_dicts
from lmgc90_engine.schema.audit import audit_core_catalogs


def test_core_catalog_audit_uses_snapshot_catalogs_without_runtime():
    report = audit_core_catalogs({
        "available": False,
        "version": None,
        "catalogs": {},
    })

    domains = report["domains"]
    assert report["runtime_available"] is False
    assert domains["geometry_elements"]["core_count"] > 0
    assert domains["contactors"]["core_only"]
    assert domains["geometry_elements"]["runtime_count"] == 0

    # Snapshot-derived core catalogs should be compared as exposed publicly.
    assert set(lmgc_dicts.GEO2ELEMENT)
    assert set(lmgc_dicts.CONTACTORS)
