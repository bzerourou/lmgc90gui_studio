"""Compatibility catalogs loaded from bundled, pure-JSON pylmgc90 snapshots."""
from __future__ import annotations

import json
import re
from importlib.resources import files
from typing import Any


SNAPSHOT_SCHEMA_VERSION = 1


def _version_numbers(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version))


def _closest_snapshot_version(
    requested: str,
    available: list[str],
) -> str:
    requested_parts = _version_numbers(requested)
    if not requested_parts:
        return available[-1]

    def distance(candidate: str) -> tuple[int, tuple[int, ...]]:
        candidate_parts = _version_numbers(candidate)
        width = max(len(requested_parts), len(candidate_parts), 1)
        left = requested_parts + (0,) * (width - len(requested_parts))
        right = candidate_parts + (0,) * (width - len(candidate_parts))
        weighted_distance = sum(
            abs(a - b) * 1000 ** (width - index - 1)
            for index, (a, b) in enumerate(zip(left, right))
        )
        return weighted_distance, tuple(-part for part in candidate_parts)

    return min(available, key=distance)


def load_capability_snapshot(version: str | None = None) -> dict[str, Any]:
    """Load the selected bundled snapshot without importing pylmgc90."""
    capability_dir = files("lmgc90_core").joinpath("capabilities")
    index_path = capability_dir.joinpath("index.json")
    if not index_path.is_file():
        raise FileNotFoundError("bundled pylmgc90 capability index is missing")

    index = json.loads(index_path.read_text(encoding="utf-8"))
    if index.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError(
            "unsupported pylmgc90 capability index schema: "
            f"{index.get('schema_version')!r}"
        )
    snapshots = index.get("snapshots", {})
    if not isinstance(snapshots, dict):
        raise ValueError("invalid snapshots mapping in capability index")

    selected_version = None
    if version is None:
        filename = index.get("latest")
    else:
        selected_version = (
            version if version in snapshots
            else _closest_snapshot_version(version, list(snapshots))
            if snapshots else None
        )
        filename = snapshots.get(selected_version) if selected_version else None
        if filename is None:
            raise LookupError("no bundled pylmgc90 capability snapshots are available")
    if (
        not isinstance(filename, str)
        or not filename.startswith("pylmgc90-")
        or not filename.endswith(".json")
        or "/" in filename
        or "\\" in filename
    ):
        raise ValueError("invalid snapshot filename in capability index")

    snapshot_path = capability_dir.joinpath(filename)
    if not snapshot_path.is_file():
        raise FileNotFoundError(f"bundled pylmgc90 snapshot is missing: {filename}")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError(
            "unsupported pylmgc90 capability snapshot schema: "
            f"{snapshot.get('schema_version')!r}"
        )
    runtime = snapshot.get("runtime")
    if not isinstance(runtime, dict) or not isinstance(runtime.get("version"), str):
        raise ValueError(f"invalid runtime metadata in capability snapshot {filename}")
    if selected_version is not None and runtime["version"] != selected_version:
        raise ValueError(
            f"capability index maps {selected_version!r} to snapshot for "
            f"{runtime['version']!r}"
        )
    if not isinstance(snapshot.get("catalogs"), dict):
        raise ValueError(f"invalid catalogs in capability snapshot {filename}")
    return snapshot


def _as_name_lists(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): [str(item) for item in items]
        for key, items in value.items()
        if isinstance(items, (list, tuple))
    }


CAPABILITY_SNAPSHOT = load_capability_snapshot()
CAPABILITY_VERSION = CAPABILITY_SNAPSHOT["runtime"]["version"]
CAPABILITY_CATALOGS: dict[str, Any] = CAPABILITY_SNAPSHOT["catalogs"]
SOURCES: dict[str, str] = {}


def _catalog(name: str) -> Any:
    value = CAPABILITY_CATALOGS.get(name, {})
    if value:
        SOURCES[name] = f"snapshot:{CAPABILITY_VERSION}"
    else:
        SOURCES[name] = "snapshot:unavailable"
    return value


GEO2ELEMENT: dict[str, tuple[str, ...]] = {
    str(geometry): tuple(str(element) for element in elements)
    for geometry, elements in _as_name_lists(_catalog("geo2element")).items()
}

_DIMENSION_ELEMENTS = _as_name_lists(_catalog("dimension2element"))
_ELEMENT_PHYSICS = _catalog("element2ddl")
ELEMENTS_BY_PHYSICS: dict[str, dict[int, list[str]]] = {}
for _element, _physics_map in _ELEMENT_PHYSICS.items():
    if not isinstance(_physics_map, dict):
        continue
    for _physics in _physics_map:
        for _dimension, _elements in _DIMENSION_ELEMENTS.items():
            if _element in _elements:
                ELEMENTS_BY_PHYSICS.setdefault(_physics, {}).setdefault(
                    int(_dimension), []
                ).append(_element)
SOURCES["ELEMENTS_BY_PHYSICS"] = (
    f"snapshot:{CAPABILITY_VERSION}"
    if ELEMENTS_BY_PHYSICS else "snapshot:unavailable"
)
PHYSICS = list(ELEMENTS_BY_PHYSICS)

CONTACTORS = _as_name_lists(_catalog("bodyType2contactor"))
CONTACT_LAW_CATEGORIES = _as_name_lists(_catalog("contactorPair2TactBehav"))
CONTACT_LAW_OPTIONS = _as_name_lists(_catalog("tactBehavOptions"))
MATERIAL_OPTIONS = _as_name_lists(_catalog("bulkBehavOptions"))
MODEL_OPTIONS_BY_PHYSICS = {
    str(physics): _as_name_lists(options)
    for physics, options in _catalog("modelOptions").items()
    if isinstance(options, dict)
}

_DIMENSION_CONTACTORS = _as_name_lists(_catalog("dimension2contactor"))
_MESH_CONTACTORS = set(CONTACTORS.get("MAILx", ()))

CONTACTORS_RIGID_2D = tuple(
    item for item in _DIMENSION_CONTACTORS.get("2", ())
    if item in CONTACTORS.get("RBDY2", ())
)
CONTACTORS_RIGID_3D = tuple(
    item for item in _DIMENSION_CONTACTORS.get("3", ())
    if item in CONTACTORS.get("RBDY3", ())
)
CONTACTORS_MESH_2D = tuple(
    item for item in _DIMENSION_CONTACTORS.get("2", ())
    if item in _MESH_CONTACTORS
)
CONTACTORS_MESH_3D = tuple(
    item for item in _DIMENSION_CONTACTORS.get("3", ())
    if item in _MESH_CONTACTORS
)

_RIGID_ELEMENTS = set(_as_name_lists({"rigidElements": _catalog("rigidElements")})
                      .get("rigidElements", ()))
RIGID_ELEMENTS_BY_DIMENSION = {
    int(dimension): tuple(
        element for element in elements if element in _RIGID_ELEMENTS
    )
    for dimension, elements in _DIMENSION_ELEMENTS.items()
}

OPTION_VALUES: dict[str, list[str]] = {}
for _options in MODEL_OPTIONS_BY_PHYSICS.values():
    for _option, _values in _options.items():
        _choices = OPTION_VALUES.setdefault(_option, [])
        for _value in _values:
            if _value not in _choices:
                _choices.append(_value)

for _name, _value in (
    ("GEO2ELEMENT", GEO2ELEMENT),
    ("PHYSICS", PHYSICS),
    ("OPTION_VALUES", OPTION_VALUES),
    ("CONTACTORS", CONTACTORS),
    ("CONTACT_LAW_CATEGORIES", CONTACT_LAW_CATEGORIES),
    ("CONTACT_LAW_OPTIONS", CONTACT_LAW_OPTIONS),
    ("MATERIAL_OPTIONS", MATERIAL_OPTIONS),
    ("MODEL_OPTIONS_BY_PHYSICS", MODEL_OPTIONS_BY_PHYSICS),
):
    SOURCES[_name] = (
        f"snapshot:{CAPABILITY_VERSION}" if _value else "snapshot:unavailable"
    )
