"""Read-only comparison between live pylmgc90 catalogs and core catalogs."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .introspection import inspect_runtime


def _mapping_paths(value: Any, prefix: tuple[str, ...] = ()) -> set[str]:
    if isinstance(value, Mapping):
        result: set[str] = set()
        for key, item in value.items():
            result.update(_mapping_paths(item, prefix + (str(key),)))
        return result
    if isinstance(value, (list, tuple, set, frozenset)):
        result: set[str] = set()
        for item in value:
            result.update(_mapping_paths(item, prefix))
        return result
    if isinstance(value, str):
        return {":".join(prefix + (value,))}
    return set()


def _compare_domain(core_value: Any, runtime_value: Any) -> dict[str, Any]:
    core_values = _mapping_paths(core_value)
    runtime_values = _mapping_paths(runtime_value)
    return {
        "core_count": len(core_values),
        "runtime_count": len(runtime_values),
        "common_count": len(core_values & runtime_values),
        "core_only": sorted(core_values - runtime_values),
        "runtime_only": sorted(runtime_values - core_values),
    }


def _contactor_pairs(value: Mapping[str, Any]) -> set[str]:
    aliases = {
        "CSpxx": "CSxxx",
        "CSxx3": "CSxxx",
        "CSxx4": "CSxxx",
        "ASpx3": "ASpxx",
        "ASpx4": "ASpxx",
        "POLYD": "POLYR",
        "POLYF": "POLYR",
        "POLYO": "POLYR",
    }
    pairs = set()
    for body, contactors in value.items():
        if body not in ("RBDY2", "RBDY3", "MAILx"):
            continue
        for contactor in contactors or ():
            pairs.add(f"{body}:{aliases.get(str(contactor), str(contactor))}")
    return pairs


def _law_categories(core: Mapping, runtime: Mapping) -> dict[str, Any]:
    category_sources = {
        "rigid/rigid": ("rigid/rigid",),
        "any/defo": ("rigid/deformable", "deformable/deformable"),
        "point/point": ("point/point",),
        "any/any": ("any/any",),
    }
    report = {}
    for category, core_keys in category_sources.items():
        core_laws = {
            law for key in core_keys for law in core.get(key, ())
        }
        runtime_laws = set(runtime.get(category, ()))
        report[category] = {
            "core_only": sorted(core_laws - runtime_laws),
            "runtime_only": sorted(runtime_laws - core_laws),
        }
    return report


def audit_core_catalogs(snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    """Report fallback/runtime catalog drift without changing application behavior."""
    from lmgc90_core import lmgc_dicts
    from lmgc90_core import types as core_types

    snapshot = snapshot or inspect_runtime()
    runtime = snapshot.get("catalogs", {}) if snapshot.get("available") else {}
    runtime_contacts = runtime.get("bodyType2contactor", {})
    core_contactors = lmgc_dicts.CONTACTORS
    runtime_material_options = next((
        runtime[name] for name in (
            "materialTypeOptions", "materialOptions", "bulkBehavOptions",
            "bulk_behav_options", "material_type_options",
        ) if name in runtime
    ), {})

    domains = {
        "geometry_elements": _compare_domain(
            lmgc_dicts.GEO2ELEMENT, runtime.get("geo2element", {}),
        ),
        "contactors": {
            "core_only": sorted(
                _contactor_pairs(core_contactors)
                - _contactor_pairs(runtime_contacts)
            ),
            "runtime_only": sorted(
                _contactor_pairs(runtime_contacts)
                - _contactor_pairs(core_contactors)
            ),
        },
        "law_parameters": _compare_domain(
            core_types._FALLBACK_CONTACT_LAW_OPTIONS,
            runtime.get("tactBehavOptions", {}),
        ),
        "material_parameters": _compare_domain(
            core_types._FALLBACK_MATERIAL_OPTIONS,
            runtime_material_options,
        ),
        "compatible_laws": _law_categories(
            core_types._FALLBACK_CONTACT_LAW_CATEGORIES,
            runtime.get("contactorPair2TactBehav", {}),
        ),
    }
    return {
        "comparison": "core fallbacks vs installed pylmgc90; read-only",
        "runtime_available": bool(snapshot.get("available")),
        "runtime_version": snapshot.get("version"),
        "core_fallback_catalog_sources": dict(lmgc_dicts.SOURCES),
        "runtime_dicts_loaded": bool(runtime),
        "runtime_dict_names": sorted(runtime),
        "domains": domains,
    }