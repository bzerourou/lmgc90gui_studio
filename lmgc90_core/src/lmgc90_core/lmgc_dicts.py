"""Compatibility catalogs loaded from bundled, pure-JSON pylmgc90 snapshots."""
from __future__ import annotations

import json
import re
from importlib.resources import files
from typing import Any
import warnings


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


_FALLBACK_ELEMENTS_BY_PHYSICS: dict[str, dict[int, tuple[str, ...]]] = {
    "MECAx": {
        2: (
            "Rxx2D", "T3xxx", "T3Lxx", "T33xx", "T6xxx", "T63xx",
            "Q4xxx", "Q4P0x", "Q44xx", "Q8xxx", "Q8Rxx", "Q84xx",
            "Q9xxx", "DKTxx", "BARxx", "SPRG2", "S2xth",
        ),
        3: (
            "Rxx3D", "TE4xx", "TE4Lx", "TE44x", "TE10x", "TE104",
            "H8xxx", "H88xx", "H20xx", "H20Rx", "H208x", "PRI6x",
            "SHB6x", "PRI15", "BARxx", "SPRG3",
        ),
    },
    "THERx": {
        2: (
            "Rxx2D", "T3xxx", "T6xxx", "DKTxx", "Q4xxx", "Q4P0x",
            "Q8xxx", "Q8Rxx", "SPRG2", "S2xth",
        ),
        3: (
            "Rxx3D", "TE4xx", "TE10x", "H8xxx", "H20xx", "H20Rx",
            "PRI6x", "PRI15", "SPRG3",
        ),
    },
    "POROx": {
        2: ("T33xx", "T63xx", "Q44xx", "Q84xx"),
        3: ("TE44x", "TE104", "H88xx", "H208x"),
    },
    "MULTI": {
        2: ("T33xx", "T63xx", "Q44xx", "Q84xx"),
        3: ("TE44x", "TE104", "H8xxx", "H88xx", "H208x"),
    },
}

_FALLBACK_DIMENSION_ELEMENTS = {
    str(dimension): list(dict.fromkeys(
        element
        for dimensions in _FALLBACK_ELEMENTS_BY_PHYSICS.values()
        for element in dimensions.get(dimension, ())
    ))
    for dimension in (2, 3)
}
_FALLBACK_ELEMENT_PHYSICS: dict[str, dict[str, int]] = {}
for _physics, _dimensions in _FALLBACK_ELEMENTS_BY_PHYSICS.items():
    for _dimension, _elements in _dimensions.items():
        for _element in _elements:
            _FALLBACK_ELEMENT_PHYSICS.setdefault(_element, {})[_physics] = 1

FALLBACK_CONTACTORS = {
    "RBDY2": ["DISKx", "xKSID", "JONCx", "POLYG", "PT2Dx"],
    "RBDY3": ["CYLND", "DNLYC", "PLANx", "POLYR", "PT3Dx", "SPHER"],
    "MAILx": ["ALpxx", "PT2DL", "PT2TL", "CLxxx", "DISKL", "POLYR", "CSxxx", "ASpxx"],
    "MBS2D": ["DISKx", "xKSID", "JONCx", "POLYG", "PT2Dx"],
    "MBS3D": ["CYLND", "DNLYC", "PLANx", "POLYR", "PT3Dx", "SPHER"],
}
FALLBACK_CONTACT_LAW_CATEGORIES = {
    "rigid/rigid": (
        "IQS_CLB", "IQS_CLB_g0", "IQS_DS_CLB", "RST_CLB",
        "IQS_WET_DS_CLB", "IQS_MOHR_DS_CLB", "IQS_MAC_CZM",
        "IQS_MAL_CZM", "IQS_TH_CZM",
    ),
    "deformable/deformable": (
        "GAP_SGR_CLB", "GAP_SGR_CLB_g0", "VEL_SGR_CLB",
        "GAP_MOHR_DS_CLB", "MAC_CZM", "MP_CZM", "MP3_CZM",
        "MAL_CZM", "TH_CZM",
    ),
    "rigid/deformable": (
        "IQS_CLB", "IQS_CLB_g0", "IQS_DS_CLB", "RST_CLB",
        "GAP_SGR_CLB", "GAP_SGR_CLB_g0", "VEL_SGR_CLB",
    ),
    "point/point": (
        "COUPLED_DOF", "NORMAL_COUPLED_DOF", "ELASTIC_REPELL_CLB",
        "ELASTIC_ROD", "ELASTIC_WIRE", "BRITTLE_ELASTIC_WIRE",
    ),
    "any/any": (
        "COUPLED_DOF", "NORMAL_COUPLED_DOF", "ELASTIC_REPELL_CLB",
    ),
}
FALLBACK_CONTACT_LAW_OPTIONS = {
    "IQS_CLB": ("fric",),
    "IQS_CLB_g0": ("fric",),
    "IQS_DS_CLB": ("dyfr", "stfr"),
    "IQS_WET_DS_CLB": ("cohn", "coht", "Wthk", "dyfr", "stfr"),
    "IQS_MOHR_DS_CLB": ("cohn", "coht", "dyfr", "stfr"),
    "RST_CLB": ("rstn", "rstt", "fric"),
    "GAP_SGR_CLB": ("fric",),
    "GAP_SGR_CLB_g0": ("fric",),
    "VEL_SGR_CLB": ("fric",),
    "GAP_MOHR_DS_CLB": ("cohn", "coht", "dyfr", "stfr"),
    "COUPLED_DOF": (),
    "NORMAL_COUPLED_DOF": (),
    "ELASTIC_REPELL_CLB": ("stiffness", "fric"),
    "ELASTIC_ROD": ("stiffness", "prestrain"),
    "ELASTIC_WIRE": ("stiffness", "prestrain"),
    "BRITTLE_ELASTIC_WIRE": ("stiffness", "prestrain", "Fmax"),
    "MAC_CZM": ("dyfr", "stfr", "cn", "ct", "b", "w"),
    "IQS_MAC_CZM": ("dyfr", "stfr", "cn", "ct", "b", "w"),
    "MP_CZM": ("dyfr", "stfr", "cn", "ct", "w"),
    "MP3_CZM": ("dyfr", "stfr", "cn", "ct", "smax", "w"),
    "MAL_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2"),
    "IQS_MAL_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2"),
    "TH_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "dp1", "dp2"),
    "IQS_TH_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "dp1", "dp2"),
}
FALLBACK_MATERIAL_OPTIONS = {
    "RIGID": ("density",),
    "ELAS": ("density", "elas", "anisotropy", "young", "nu", "G"),
    "ELAS_DILA": (
        "density", "elas", "anisotropy", "young", "nu", "dilatation", "T_ref_meca",
    ),
    "VISCO_ELAS": (
        "density", "elas", "anisotropy", "young", "nu",
        "viscous_model", "viscous_young", "viscous_nu",
    ),
    "ELAS_PLAS": (
        "density", "elas", "anisotropy", "young", "nu",
        "critere", "isoh", "iso_hard", "isoh_coeff", "cinh", "visc",
    ),
    "THERMO_ELAS": (
        "density", "elas", "anisotropy", "young", "nu",
        "dilatation", "T_ref_meca", "conductivity", "specific_capacity", "therm_cpl",
    ),
    "PORO_ELAS": (
        "density", "elas", "anisotropy", "young", "nu",
        "hydro_cpl", "conductivity", "specific_capacity",
    ),
    "DISCRETE": ("masses", "stiffnesses", "viscosities"),
    "USER_MAT": ("density", "file_mat"),
    "EXTERNAL": (),
}
FALLBACK_MODEL_OPTIONS = {
    "MECAx": {
        "kinematic": ("small", "large"),
        "formulation": ("UpdtL", "TotaL"),
        "mass_storage": ("lump_", "coher"),
    },
    "THERx": {
        "capacity_storage": ("lump_", "coher"),
        "formulation": ("UpdtL", "TotaL"),
        "convection_type": ("supg_", "char_", "center"),
    },
    "POROx": {
        "kinematic": ("small", "large"),
        "mass_storage": ("lump_", "coher"),
        "capacity_storage": ("lump_", "coher"),
    },
    "MULTI": {
        "kinematic": ("small", "large"),
        "mass_storage": ("lump_", "coher"),
        "formulation": ("UpdtL", "TotaL"),
    },
}

_FALLBACK_CATALOGS: dict[str, Any] = {
    "geo2element": {
        "Point": ["Rxx2D", "Rxx3D"],
        "S2xxx": ["SPRG2", "SPRG3", "BARxx", "S2xth"],
        "Q4xxx": ["Q4xxx", "Q4P0x", "Q44xx"],
        "T3xxx": ["T3xxx", "T3Lxx", "DKTxx", "T33xx"],
        "Q8xxx": ["Q8xxx", "Q8Rxx", "Q84xx"],
        "Q9xxx": ["Q9xxx"],
        "T6xxx": ["T6xxx", "T63xx"],
        "TE4xx": ["TE4xx", "TE4Lx", "TE44x"],
        "TE10x": ["TE10x", "TE104"],
        "H8xxx": ["H8xxx", "H88xx"],
        "H20xx": ["H20xx", "H20Rx", "H208x"],
        "PRI6x": ["PRI6x", "SHB6x"],
        "PRI15": ["PRI15"],
    },
    "dimension2element": _FALLBACK_DIMENSION_ELEMENTS,
    "element2ddl": _FALLBACK_ELEMENT_PHYSICS,
    "rigidElements": ["Rxx2D", "Rxx3D"],
    "bodyType2contactor": FALLBACK_CONTACTORS,
    "dimension2contactor": {
        "2": ["DISKx", "xKSID", "JONCx", "POLYG", "PT2Dx", "CLxxx", "ALpxx", "PT2DL", "PT2TL", "DISKL"],
        "3": ["SPHER", "CYLND", "DNLYC", "PLANx", "POLYR", "PT3Dx", "POLYF", "POLYO", "CSpxx", "ASpxx"],
    },
    "contactorPair2TactBehav": {
        key: list(values) for key, values in FALLBACK_CONTACT_LAW_CATEGORIES.items()
    },
    "tactBehavOptions": {
        key: list(values) for key, values in FALLBACK_CONTACT_LAW_OPTIONS.items()
    },
    "bulkBehavOptions": {
        key: list(values) for key, values in FALLBACK_MATERIAL_OPTIONS.items()
    },
    "modelOptions": {
        physics: {
            option: list(values) for option, values in options.items()
        }
        for physics, options in FALLBACK_MODEL_OPTIONS.items()
    },
}

try:
    CAPABILITY_SNAPSHOT = load_capability_snapshot()
    CAPABILITY_SNAPSHOT_ERROR: str | None = None
except (OSError, ValueError, LookupError) as error:
    CAPABILITY_SNAPSHOT = {"runtime": {}, "catalogs": {}}
    CAPABILITY_SNAPSHOT_ERROR = str(error)
    warnings.warn(
        "bundled pylmgc90 capability snapshot unavailable; using built-in "
        f"compatibility catalogs ({error})",
        RuntimeWarning,
        stacklevel=2,
    )
CAPABILITY_VERSION = CAPABILITY_SNAPSHOT.get("runtime", {}).get("version", "fallback")
CAPABILITY_CATALOGS: dict[str, Any] = CAPABILITY_SNAPSHOT["catalogs"]
SOURCES: dict[str, str] = {}


def _catalog(name: str) -> Any:
    value = CAPABILITY_CATALOGS.get(name, {})
    if value:
        SOURCES[name] = f"snapshot:{CAPABILITY_VERSION}"
        return value
    fallback = _FALLBACK_CATALOGS.get(name, {})
    if fallback:
        SOURCES[name] = "manuel"
        return fallback
    SOURCES[name] = "indisponible"
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
    "manuel" if "manuel" in (SOURCES.get("dimension2element"), SOURCES.get("element2ddl"))
    else f"snapshot:{CAPABILITY_VERSION}" if ELEMENTS_BY_PHYSICS
    else "indisponible"
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

for _name, _catalog_name in (
    ("GEO2ELEMENT", "geo2element"),
    ("CONTACTORS", "bodyType2contactor"),
    ("CONTACT_LAW_CATEGORIES", "contactorPair2TactBehav"),
    ("CONTACT_LAW_OPTIONS", "tactBehavOptions"),
    ("MATERIAL_OPTIONS", "bulkBehavOptions"),
):
    SOURCES[_name] = SOURCES[_catalog_name]
SOURCES["PHYSICS"] = SOURCES["ELEMENTS_BY_PHYSICS"]
SOURCES["OPTION_VALUES"] = SOURCES["modelOptions"]
SOURCES["MODEL_OPTIONS_BY_PHYSICS"] = (
    "manuel" if (
        SOURCES["modelOptions"] == "manuel"
        or SOURCES["ELEMENTS_BY_PHYSICS"] == "manuel"
    )
    else SOURCES["modelOptions"]
)
