"""LMGC90 vocabulary — names match pylmgc90.pre, not GUI labels.

Compatibility catalogs come from bundled JSON snapshots. Runtime introspection
belongs to lmgc90_engine, not this dependency-free core.
"""
from __future__ import annotations

from enum import Enum

from . import lmgc_dicts as _snapshot_catalogs
from .lmgc_dicts import (
    CONTACT_LAW_CATEGORIES as _SNAPSHOT_CONTACT_LAW_CATEGORIES,
    CONTACT_LAW_OPTIONS as _SNAPSHOT_CONTACT_LAW_OPTIONS,
    ELEMENTS_BY_PHYSICS as _SNAPSHOT_ELEMENTS_BY_PHYSICS,
    MATERIAL_OPTIONS as _SNAPSHOT_MATERIAL_OPTIONS,
    MODEL_OPTIONS_BY_PHYSICS as _SNAPSHOT_MODEL_OPTIONS_BY_PHYSICS,
    RIGID_ELEMENTS_BY_DIMENSION,
)

CONTACTORS_MESH_2D = _snapshot_catalogs.CONTACTORS_MESH_2D
CONTACTORS_MESH_3D = _snapshot_catalogs.CONTACTORS_MESH_3D
CONTACTORS_RIGID_2D = _snapshot_catalogs.CONTACTORS_RIGID_2D
CONTACTORS_RIGID_3D = _snapshot_catalogs.CONTACTORS_RIGID_3D

STUDIO_ONLY_KEYS = frozenset({"phase"})


class MaterialType(str, Enum):
    RIGID = "RIGID"
    ELAS = "ELAS"
    ELAS_DILA = "ELAS_DILA"
    VISCO_ELAS = "VISCO_ELAS"
    ELAS_PLAS = "ELAS_PLAS"
    THERMO_ELAS = "THERMO_ELAS"
    PORO_ELAS = "PORO_ELAS"
    DISCRETE = "DISCRETE"
    USER_MAT = "USER_MAT"
    EXTERNAL = "EXTERNAL"


def material_type_name(material_type: MaterialType | str) -> str:
    return (
        material_type.value
        if isinstance(material_type, MaterialType)
        else str(material_type)
    )


def coerce_material_type(material_type: MaterialType | str) -> MaterialType | str:
    if isinstance(material_type, MaterialType):
        return material_type
    try:
        return MaterialType(material_type)
    except ValueError:
        return material_type


class AvatarType(str, Enum):
    RIGID_DISK = "rigidDisk"
    RIGID_JONC = "rigidJonc"
    RIGID_POLYGON = "rigidPolygon"
    RIGID_OVOID = "rigidOvoidPolygon"
    RIGID_DISCRETE = "rigidDiscreteDisk"
    RIGID_CLUSTER = "rigidCluster"
    ROUGH_WALL = "roughWall"
    FINE_WALL = "fineWall"
    SMOOTH_WALL = "smoothWall"
    GRANULO_WALL = "granuloRoughWall"
    EMPTY_AVATAR = "emptyAvatar"
    MESH_DEFORMABLE = "mesh"
    RIGID_SPHERE = "rigidSphere"
    RIGID_PLAN = "rigidPlan"
    RIGID_CYLINDER = "rigidCylinder"
    RIGID_POLYHEDRON = "rigidPolyhedron"
    ROUGH_WALL_3D = "roughWall3D"
    GRANULO_ROUGH_WALL_3D = "granuloRoughWall3D"


class ContactLawType(str, Enum):
    IQS_CLB = "IQS_CLB"
    IQS_CLB_G0 = "IQS_CLB_g0"
    IQS_DS_CLB = "IQS_DS_CLB"
    IQS_CLB_RGR = "IQS_CLB_RGR"
    IQS_WET_DS_CLB = "IQS_WET_DS_CLB"
    XQS_WET_DS_CLB = "xQS_WET_DS_CLB"
    IQS_MOHR_DS_CLB = "IQS_MOHR_DS_CLB"
    IQS_STICK = "IQS_STICK"
    IQS_CLB_NOSLDT = "IQS_CLB_nosldt"
    IQS_MAC_CZM = "IQS_MAC_CZM"
    IQS_WET_CZM = "IQS_WET_CZM"
    IQS_MAL_CZM = "IQS_MAL_CZM"
    IQS_TH_CZM = "IQS_TH_CZM"
    IQS_ABP_CZM = "IQS_ABP_CZM"
    IQS_EXPO_CZM = "IQS_EXPO_CZM"
    IQS_EXPO_CZM_SPRING = "IQS_EXPO_CZM_SPRING"
    IQS_EXPO_CZM_P = "IQS_EXPO_CZM_P"
    IQS_EXPO_CZM_SPRING_P = "IQS_EXPO_CZM_SPRING_P"
    RST_CLB = "RST_CLB"
    GAP_SGR_CLB = "GAP_SGR_CLB"
    GAP_SGR_CLB_G0 = "GAP_SGR_CLB_g0"
    GAP_SGR_STICK = "GAP_SGR_STICK"
    GAP_SGR_CLB_NOSLDT = "GAP_SGR_CLB_nosldt"
    VEL_SGR_CLB = "VEL_SGR_CLB"
    PREGAP_SGR_CLB = "preGAP_SGR_CLB"
    GAP_MOHR_DS_CLB = "GAP_MOHR_DS_CLB"
    MAC_CZM = "MAC_CZM"
    MAL_CZM = "MAL_CZM"
    MP_CZM = "MP_CZM"
    MP3_CZM = "MP3_CZM"
    MP3_CZM_THER = "MP3_CZM_THER"
    TH_CZM = "TH_CZM"
    ABP_CZM = "ABP_CZM"
    EXPO_CZM = "EXPO_CZM"
    EXPO_CZM_SPRING = "EXPO_CZM_SPRING"
    EXPO_CZM_P = "EXPO_CZM_P"
    EXPO_CZM_SPRING_P = "EXPO_CZM_SPRING_P"
    GTN_CZM = "GTN_CZM"
    GTN2_CZM = "GTN2_CZM"
    TOSI_CZM = "TOSI_CZM"
    TOSI_CZM_INCRE = "TOSI_CZM_INCRE"
    BRITTLE_COATING_CLB = "BRITTLE_COATING_CLB"
    ELASTIC_WIRE = "ELASTIC_WIRE"
    BRITTLE_ELASTIC_WIRE = "BRITTLE_ELASTIC_WIRE"
    ELASTIC_ROD = "ELASTIC_ROD"
    VOIGT_ROD = "VOIGT_ROD"
    NARD_ROD = "NARD_ROD"
    COUPLED_DOF = "COUPLED_DOF"
    NORMAL_COUPLED_DOF = "NORMAL_COUPLED_DOF"
    ELASTIC_REPELL_CLB = "ELASTIC_REPELL_CLB"
    ELASTIC_REPELL_CLB_G0 = "ELASTIC_REPELL_CLB_g0"
    ELASTIC_REPELL_CLB_ADAPT = "ELASTIC_REPELL_CLB_adapt"
    VISCO_ELASTIC_REPELL_CLB = "VISCO_ELASTIC_REPELL_CLB"


class AvatarOrigin(str, Enum):
    MANUAL = "manual"
    LOOP = "loop"
    GRANULO = "granulo"
    FACTORY = "factory"


class UnitSystem(str, Enum):
    SI = "SI"
    CGS = "CGS"


# Keep the hand-maintained catalogs available independently of JSON snapshots.
_FALLBACK_CONTACT_LAW_OPTIONS = {
    name: tuple(options)
    for name, options in _snapshot_catalogs.FALLBACK_CONTACT_LAW_OPTIONS.items()
}
_FALLBACK_CONTACT_LAW_CATEGORIES = {
    name: tuple(laws)
    for name, laws in _snapshot_catalogs.FALLBACK_CONTACT_LAW_CATEGORIES.items()
}
_FALLBACK_MATERIAL_OPTIONS = {
    name: tuple(options)
    for name, options in _snapshot_catalogs.FALLBACK_MATERIAL_OPTIONS.items()
}
_CONTACT_LAW_OPTIONS = {
    name: tuple(options) for name, options in _SNAPSHOT_CONTACT_LAW_OPTIONS.items()
} or dict(_FALLBACK_CONTACT_LAW_OPTIONS)
CONTACT_LAW_CATEGORIES = {
    name: tuple(laws) for name, laws in _SNAPSHOT_CONTACT_LAW_CATEGORIES.items()
} or dict(_FALLBACK_CONTACT_LAW_CATEGORIES)
MATERIAL_OPTIONS = {
    name: tuple(options) for name, options in _SNAPSHOT_MATERIAL_OPTIONS.items()
} or dict(_FALLBACK_MATERIAL_OPTIONS)
CONTACTOR_PAIR_TO_LAWS = CONTACT_LAW_CATEGORIES


# Convenience aliases (GUI / filters) derived from categories
def _laws_in(*keys: str) -> tuple[str, ...]:
    seen: list[str] = []
    for k in keys:
        for law in CONTACT_LAW_CATEGORIES.get(k, ()):
            if law not in seen:
                seen.append(law)
    return tuple(seen)


LAWS_RIGID_RIGID = _laws_in("rigid/rigid")
LAWS_ANY_DEFORMABLE = _laws_in("deformable/deformable", "any/defo")
LAWS_RIGID_DEFORMABLE = _laws_in("rigid/deformable", "any/defo")
LAWS_POINT_POINT = _laws_in("point/point")
LAWS_ANY_ANY = _laws_in("any/any")

# If the snapshot uses different category keys, still expose something useful.
if not LAWS_RIGID_RIGID and CONTACT_LAW_CATEGORIES:
    _all: list[str] = []
    for vals in CONTACT_LAW_CATEGORIES.values():
        for law in vals:
            if law not in _all:
                _all.append(law)
    LAWS_RIGID_RIGID = tuple(_all)


# Material-type → extra property fields (name, default, kind)
# Base isotropic elastic keys + orthotropic extras (shown dynamically in GUI).
# When anisotropy == "orthotropic", materialize packs young/nu/G as lists for pylmgc90.
MATERIAL_PROPERTY_SCHEMA: dict[str, tuple[tuple[str, object, str], ...]] = {
    "RIGID": (),
    "ELAS": (
        ("elas", "standard", "str"),
        ("anisotropy", "isotropic", "str"),
        ("young", 2.1e11, "float"),
        ("nu", 0.3, "float"),
        ("G", 8.076923e10, "float"),
        ("young1", 2.1e11, "float"),
        ("young2", 2.1e11, "float"),
        ("young3", 2.1e11, "float"),
        ("nu12", 0.3, "float"),
        ("nu13", 0.3, "float"),
        ("nu23", 0.3, "float"),
        ("G12", 8.076923e10, "float"),
        ("G13", 8.076923e10, "float"),
        ("G23", 8.076923e10, "float"),
    ),
    "ELAS_DILA": (
        ("elas", "standard", "str"),
        ("anisotropy", "isotropic", "str"),
        ("young", 2.1e11, "float"),
        ("nu", 0.3, "float"),
        ("dilatation", 1e-5, "float"),
        ("T_ref_meca", 20.0, "float"),
    ),
    "VISCO_ELAS": (
        ("elas", "standard", "str"),
        ("anisotropy", "isotropic", "str"),
        ("young", 2.1e11, "float"),
        ("nu", 0.3, "float"),
        ("viscous_model", "KelvinVoigt", "str"),
        ("viscous_young", 1e6, "float"),
        ("viscous_nu", 0.3, "float"),
    ),
    "ELAS_PLAS": (
        ("elas", "standard", "str"),
        ("anisotropy", "isotropic", "str"),
        ("young", 2.1e11, "float"),
        ("nu", 0.3, "float"),
        ("critere", "Von-Mises", "str"),
        ("isoh", "linear", "str"),
        ("iso_hard", 2.5e8, "float"),
        ("isoh_coeff", 1e9, "float"),
        ("cinh", "none", "str"),
        ("visc", "none", "str"),
    ),
    "THERMO_ELAS": (
        ("elas", "standard", "str"),
        ("anisotropy", "isotropic", "str"),
        ("young", 2.1e11, "float"),
        ("nu", 0.3, "float"),
        ("dilatation", 1e-5, "float"),
        ("T_ref_meca", 20.0, "float"),
        ("conductivity", 50.0, "float"),
        ("specific_capacity", 500.0, "float_or_field"),
    ),
    "PORO_ELAS": (
        ("elas", "standard", "str"),
        ("anisotropy", "isotropic", "str"),
        ("young", 2.1e11, "float"),
        ("nu", 0.3, "float"),
        ("hydro_cpl", 0.8, "float"),
        ("conductivity", 1e-8, "float_or_field"),
        ("specific_capacity", 1e-10, "float_or_field"),
    ),
    "DISCRETE": (
        ("masses", (1.0, 1.0, 1.0), "vector"),
        ("stiffnesses", (1e5, 1e5, 1e5), "vector"),
        ("viscosities", (0.0, 0.0, 0.0), "vector"),
    ),
    "USER_MAT": (("file_mat", "", "str"),),
    "EXTERNAL": (),
}

MATERIAL_PROPERTY_CHOICES: dict[str, tuple[str, ...]] = {
    "elas": ("standard",),
    "anisotropy": ("isotropic", "orthotropic"),
    "viscous_model": ("none", "KelvinVoigt"),
    "critere": ("Von-Mises", "none"),
    "isoh": ("none", "Swift", "Hollomon", "linear"),
    "cinh": ("none", "linear"),
    "visc": ("none", "power_law"),
}

# Fields only relevant when anisotropy is orthotropic
ORTHOTROPIC_FIELDS_2D = ("young1", "young2", "nu12", "G12")
ORTHOTROPIC_FIELDS_3D = (
    "young1", "young2", "young3",
    "nu12", "nu13", "nu23",
    "G12", "G13", "G23",
)
ISOTROPIC_FIELDS = ("young", "nu", "G")


# Defaults are GUI-side only (pylmgc90 does not publish them in lmgc90dicts).
_CONTACT_LAW_DEFAULTS: dict[str, object] = {
    "fric": 0.3,
    "dyfr": 0.3,
    "stfr": 0.3,
    "cn": 1e10,
    "ct": 1e10,
    "stiffness": 1e5,
    "Fmax": 1e3,
    "E": 1e9,
    "nu": 0.3,
}

CONTACT_LAW_PROPERTY_SCHEMA: dict[str, tuple[tuple[str, object, str], ...]] = {
    law: tuple(
        (name, _CONTACT_LAW_DEFAULTS.get(name, 0.0), "float")
        for name in options
    )
    for law, options in _CONTACT_LAW_OPTIONS.items()
}

# Model option fields common in pylmgc90.pre.model
MODEL_OPTION_SCHEMA: tuple[tuple[str, object, str], ...] = (
    ("anisotropy", "iso__", "str"),
    ("kinematic", "small", "str"),
    ("formulation", "UpdtL", "str"),
    ("mass_storage", "lump_", "str"),
    ("material", "elas_", "str"),
    ("external_model", "no___", "str"),
)

MODEL_OPTION_CHOICES_BY_PHYSICS = {
    physics: {
        option: tuple(values) for option, values in options.items()
    }
    for physics, options in _SNAPSHOT_MODEL_OPTIONS_BY_PHYSICS.items()
}
MODEL_OPTION_CHOICES: dict[str, tuple[str, ...]] = {}
for _physics_options in MODEL_OPTION_CHOICES_BY_PHYSICS.values():
    for _option, _values in _physics_options.items():
        MODEL_OPTION_CHOICES[_option] = tuple(dict.fromkeys(
            (*MODEL_OPTION_CHOICES.get(_option, ()), *_values)
        ))

ELEMENTS_BY_PHYSICS: dict[str, dict[int, tuple[str, ...]]] = {
    physics: {
        dimension: tuple(elements)
        for dimension, elements in dimensions.items()
    }
    for physics, dimensions in _SNAPSHOT_ELEMENTS_BY_PHYSICS.items()
}
RIGID_ELEMENTS_2D = RIGID_ELEMENTS_BY_DIMENSION.get(2, ())
RIGID_ELEMENTS_3D = RIGID_ELEMENTS_BY_DIMENSION.get(3, ())
MODEL_OPTIONS_BY_PHYSICS: dict[str, dict[str, tuple[str, ...]]] = {
    physics: {
        element: tuple(options)
        for dimension_elements in ELEMENTS_BY_PHYSICS.get(physics, {}).values()
        for element in dimension_elements
        if element not in RIGID_ELEMENTS_2D + RIGID_ELEMENTS_3D
    }
    for physics, options in MODEL_OPTION_CHOICES_BY_PHYSICS.items()
}

MODEL_COMMON_OPTIONS_BY_PHYSICS: dict[str, tuple[str, ...]] = {
    physics: tuple(options)
    for physics, options in MODEL_OPTION_CHOICES_BY_PHYSICS.items()
}

MODEL_OPTION_DEFAULTS: dict[str, str] = {
    "anisotropy": "iso__",
    "kinematic": "small",
    "formulation": "UpdtL",
    "mass_storage": "lump_",
    "material": "elas_",
    "external_model": "no___",
    "capacity_storage": "coher",
    "convection_type": "supg_",
    "physical_type": "solid",
    "fluid_comp_storage": "lump_",
}

DEFORMABLE_2D = set(
    ELEMENTS_BY_PHYSICS.get("MECAx", {}).get(2, ())
) - set(RIGID_ELEMENTS_2D)
DEFORMABLE_3D = set(
    ELEMENTS_BY_PHYSICS.get("MECAx", {}).get(3, ())
) - set(RIGID_ELEMENTS_3D)

RIGID_AVATARS_2D = {
    AvatarType.RIGID_DISK, AvatarType.RIGID_JONC, AvatarType.RIGID_POLYGON,
    AvatarType.RIGID_OVOID, AvatarType.RIGID_DISCRETE, AvatarType.RIGID_CLUSTER,
    AvatarType.ROUGH_WALL, AvatarType.FINE_WALL, AvatarType.SMOOTH_WALL,
    AvatarType.GRANULO_WALL,
}
RIGID_AVATARS_3D = {
    AvatarType.RIGID_SPHERE, AvatarType.RIGID_PLAN, AvatarType.RIGID_CYLINDER,
    AvatarType.RIGID_POLYHEDRON, AvatarType.ROUGH_WALL_3D,
    AvatarType.GRANULO_ROUGH_WALL_3D,
}

POPULATION_TYPES = {
    AvatarType.RIGID_DISK, AvatarType.RIGID_SPHERE,
    AvatarType.RIGID_DISCRETE, AvatarType.RIGID_CLUSTER,
    AvatarType.RIGID_CYLINDER, AvatarType.RIGID_POLYGON,
    AvatarType.RIGID_POLYHEDRON,
}

# GUI French loop names → canonical
LOOP_ALIASES = {
    "Cercle": "circle", "Grille": "grid", "Ligne": "line",
    "Spirale": "spiral", "Manuel": "manual",
    "circle": "circle", "grid": "grid", "line": "line",
    "spiral": "spiral", "manual": "manual",
}
