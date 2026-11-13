"""Runtime-backed contactor catalogs with snapshot-compatible fallbacks."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .introspection import compatibility_catalog_source, load_compatibility_catalogs


def _name_lists(raw: object) -> dict[str, tuple[str, ...]]:
    if not isinstance(raw, Mapping):
        return {}
    result: dict[str, tuple[str, ...]] = {}
    for name, values in raw.items():
        if isinstance(values, Mapping):
            entries = values.keys()
        elif isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
            entries = values
        else:
            continue
        result[str(name)] = tuple(dict.fromkeys(str(entry) for entry in entries))
    return result


def contactor_schema_catalog(
    fallback_options: Mapping[str, Sequence[str]] | None = None,
    fallback_optional_options: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, Any]:
    """Return contactor availability and accepted option names by type."""
    catalogs = load_compatibility_catalogs()
    runtime_options = _name_lists(catalogs.get("contactorOptions"))
    runtime_optional_options = _name_lists(
        catalogs.get("contactorOptionalOptions"),
    )
    dimension_contactors = _name_lists(catalogs.get("dimension2contactor"))
    body_type_contactors = _name_lists(catalogs.get("bodyType2contactor"))
    geometry_contactors = _name_lists(catalogs.get("geo2contactor"))

    options = _name_lists(fallback_options or {})
    options.update(runtime_options)
    optional_options = _name_lists(fallback_optional_options or {})
    optional_options.update(runtime_optional_options)
    has_runtime_catalog = any((
        dimension_contactors,
        body_type_contactors,
        runtime_options,
        runtime_optional_options,
        geometry_contactors,
    ))

    return {
        "source": (
            compatibility_catalog_source()
            if has_runtime_catalog else "FALLBACK"
        ),
        "dimension_contactors": dimension_contactors,
        "body_type_contactors": body_type_contactors,
        "geometry_contactors": geometry_contactors,
        "options": options,
        "optional_options": optional_options,
    }


def contactors_for_body_type(
    catalog: Mapping[str, Any],
    body_type: str,
    dimension: int,
    fallback: Sequence[str] = (),
) -> tuple[str, ...]:
    """Return contactors for a body/dimension pair from runtime mappings."""
    dimension_catalog = catalog.get("dimension_contactors", {})
    body_catalog = catalog.get("body_type_contactors", {})
    dimension_key = str(dimension)
    if (
        not isinstance(dimension_catalog, Mapping)
        or not isinstance(body_catalog, Mapping)
        or dimension_key not in dimension_catalog
        or body_type not in body_catalog
    ):
        return tuple(fallback)

    dimension_shapes = tuple(dimension_catalog[dimension_key])
    body_shapes = tuple(body_catalog[body_type])
    if body_type != "MAILx":
        body_set = set(body_shapes)
        return tuple(shape for shape in dimension_shapes if shape in body_set)

    dimension_set = set(dimension_shapes)
    compatible = {
        shape for shape in body_shapes if shape in dimension_set
    }
    if "CSxxx" in body_shapes and any(
        shape.startswith("CS") for shape in dimension_shapes
    ):
        compatible.add("CSxxx")
    return tuple(shape for shape in body_shapes if shape in compatible)
