"""LMGC90 vocabulary — names match pylmgc90.pre, not GUI labels.

Contact-law parameter lists and category → law mappings are loaded from
``pylmgc90.pre.config.lmgc90dicts`` when available; otherwise the embedded
fallback (copy of a known pylmgc90 snapshot) is used.

Flag ``FROM_PYLMGC90`` is True when the live import succeeded; ``FROM_PYLMGC90_KEYS`` lists which dicts were taken from pylmgc90.
"""
from __future__ import annotations

from enum import Enum
from typing import Any
import importlib

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


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Vocabulary from pylmgc90.pre.config.lmgc90dicts (all public dicts)
# ---------------------------------------------------------------------------
# Strategy: import the module when available and harvest every public dict.
# Known keys are wired into the names the rest of the project already uses.
# Unknown keys are kept in PYLMGC90_RAW for diagnostics / future use.
# When the module is missing, embedded fallbacks are used (same shapes).
#
# Flags:
#   FROM_PYLMGC90      – True if the module imported at all
#   FROM_PYLMGC90_KEYS – frozenset of dict names successfully taken from live
# ---------------------------------------------------------------------------

def _as_tuple_dict(raw: dict) -> dict[str, tuple[str, ...]]:
    """Normalize dict values to tuples of str (pylmgc90 uses lists)."""
    out: dict[str, tuple[str, ...]] = {}
    for key, val in (raw or {}).items():
        if isinstance(val, (list, tuple)):
            out[str(key)] = tuple(str(x) for x in val)
        elif isinstance(val, dict):
            # nested → flatten keys only (rare)
            out[str(key)] = tuple(str(x) for x in val.keys())
        else:
            out[str(key)] = ()
    return out


def _as_str_keyed(raw: dict) -> dict[str, object]:
    return {str(k): v for k, v in (raw or {}).items()}


def _import_lmgc90dicts_module():
    """Return the lmgc90dicts module or raise ImportError."""
    import importlib
    last_err: Exception | None = None
    for mod_name in (
        "pylmgc90.pre.config.lmgc90dicts",
        "pylmgc90.pre.config.lmgc90_dicts",
        "pylmgc90.pre.lmgc90dicts",
    ):
        try:
            return importlib.import_module(mod_name)
        except ImportError as exc:
            last_err = exc
    raise ImportError(str(last_err))


def _harvest_public_dicts(mod) -> dict[str, dict]:
    """Collect every public dict-like attribute on the module."""
    found: dict[str, dict] = {}
    for name in dir(mod):
        if name.startswith("_"):
            continue
        try:
            val = getattr(mod, name)
        except Exception:
            continue
        if isinstance(val, dict):
            found[name] = val
    return found


def _pick(raws: dict[str, dict], *names: str) -> dict | None:
    for n in names:
        if n in raws and isinstance(raws[n], dict) and raws[n]:
            return raws[n]
    return None


# --- embedded fallbacks (snapshot; used when pylmgc90 is absent) ---

_FALLBACK_CONTACT_LAW_OPTIONS: dict[str, tuple[str, ...]] = {
    "IQS_CLB": ("fric",),
    "IQS_CLB_g0": ("fric",),
    "IQS_DS_CLB": ("fric", "cohesion"),
    "IQS_WET_DS_CLB": ("fric", "cohesion"),
    "IQS_MOHR_DS_CLB": ("fric", "cohesion", "Rtens"),
    "RST_CLB": ("rstn", "rstt", "fric"),
    "GAP_SGR_CLB": ("fric",),
    "GAP_SGR_CLB_g0": ("fric",),
    "VEL_SGR_CLB": ("fric",),
    "GAP_MOHR_DS_CLB": ("fric", "cohesion", "Rtens"),
    "COUPLED_DOF": (),
    "NORMAL_COUPLED_DOF": (),
    "ELASTIC_REPELL_CLB": ("alert", "stiffness"),
    "ELASTIC_REPELL_WET_CLB": ("alert", "stiffness", "cohesion"),
    "ELASTIC_ROD": ("prestrain", "stiffness"),
    "ELASTIC_WIRE": ("prestrain", "stiffness"),
    "BRITTLE_ELASTIC_WIRE": ("prestrain", "stiffness", "force"),
    "MAC_CZM": ("dyfr", "stfr", "cn", "ct", "b", "w"),
    "IQS_MAC_CZM": ("dyfr", "stfr", "cn", "ct", "b", "w"),
    "MP_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2"),
    "MP3_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2"),
    "MAL_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2"),
    "IQS_MAL_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2"),
    "TH_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "dp1", "dp2"),
    "IQS_TH_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "dp1", "dp2"),
}

_FALLBACK_CONTACT_LAW_CATEGORIES: dict[str, tuple[str, ...]] = {
    "rigid/rigid": (
        "IQS_CLB", "IQS_CLB_g0", "IQS_DS_CLB", "RST_CLB",
        "IQS_WET_DS_CLB", "IQS_MOHR_DS_CLB",
        "IQS_MAC_CZM", "IQS_MAL_CZM", "IQS_TH_CZM",
    ),
    "deformable/deformable": (
        "GAP_SGR_CLB", "GAP_SGR_CLB_g0", "VEL_SGR_CLB", "GAP_MOHR_DS_CLB",
        "MAC_CZM", "MP_CZM", "MP3_CZM", "MAL_CZM", "TH_CZM",
    ),
    "rigid/deformable": (
        "IQS_CLB", "IQS_CLB_g0", "IQS_DS_CLB", "RST_CLB",
        "GAP_SGR_CLB", "GAP_SGR_CLB_g0", "VEL_SGR_CLB",
    ),
    "point/point": (
        "COUPLED_DOF", "NORMAL_COUPLED_DOF",
        "ELASTIC_REPELL_CLB", "ELASTIC_REPELL_WET_CLB",
        "ELASTIC_ROD", "ELASTIC_WIRE", "BRITTLE_ELASTIC_WIRE",
    ),
    "any/any": (
        "COUPLED_DOF", "NORMAL_COUPLED_DOF", "ELASTIC_REPELL_CLB",
    ),
}

# materialType → list of property names (no GUI defaults in pylmgc)
_FALLBACK_MATERIAL_OPTIONS: dict[str, tuple[str, ...]] = {
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

CONTACTORS_RIGID_2D = ("DISKx", "xKSID", "JONCx", "POLYG", "PT2Dx")
CONTACTORS_RIGID_3D = ("SPHER", "PLANx", "CYLND", "POLYR", "PT3Dx")
CONTACTORS_MESH_2D = ("CLxxx", "ALpxx", "PT2Dx")
CONTACTORS_MESH_3D = ("CSpxx", "ASpxx", "PT3Dx")

RIGID_ELEMENTS_2D = ("Rxx2D",)
RIGID_ELEMENTS_3D = ("Rxx3D",)

ELEMENTS_BY_PHYSICS = {
    "MECAx": {
        2: (
            "Rxx2D", "T3xxx", "T3Lxx", "T33xx", "T6xxx", "T63xx", "DKTxx",
            "Q4xxx", "Q4P0x", "Q44xx", "Q8xxx", "Q8Rxx", "Q84xx", "Q9xxx",
            "BARxx", "SPRG2", "S2xth",
        ),
        3: (
            "Rxx3D", "TE4xx", "TE4Lx", "TE44x", "TE10x", "TE104",
            "H8xxx", "H88xx", "H20xx", "H20Rx", "H208x",
            "PRI6x", "SHB6x", "PRI15", "BARxx", "SPRG3",
        ),
    },
    "THERx": {
        2: ("Rxx2D", "T3xxx", "T6xxx", "DKTxx", "Q4xxx", "Q4P0x", "Q8xxx", "Q8Rxx", "SPRG2", "S2xth"),
        3: ("Rxx3D", "TE4xx", "TE10x", "H8xxx", "H20xx", "H20Rx", "PRI6x", "PRI15", "SPRG3"),
    },
    "POROx": {
        2: ("T33xx", "T63xx", "Q44xx", "Q84xx"),
        3: ("TE44x", "TE104", "H88xx", "H208x"),
    },
    "MULTI": {
        2: (
            "Rxx2D", "T3xxx", "T3Lxx", "T33xx", "T6xxx", "T63xx", "DKTxx",
            "Q4xxx", "Q4P0x", "Q44xx", "Q8xxx", "Q8Rxx", "Q84xx", "Q9xxx",
            "BARxx", "SPRG2", "S2xth",
        ),
        3: (
            "Rxx3D", "TE4xx", "TE4Lx", "TE44x", "TE10x", "TE104",
            "H8xxx", "H88xx", "H20xx", "H20Rx", "H208x",
            "PRI6x", "SHB6x", "PRI15", "BARxx", "SPRG3",
        ),
    },
}


# --- live load ---

FROM_PYLMGC90 = False
FROM_PYLMGC90_KEYS: frozenset[str] = frozenset()
PYLMGC90_RAW: dict[str, dict] = {}
_CONTACT_LAW_OPTIONS: dict[str, tuple[str, ...]] = dict(_FALLBACK_CONTACT_LAW_OPTIONS)
CONTACT_LAW_CATEGORIES: dict[str, tuple[str, ...]] = dict(_FALLBACK_CONTACT_LAW_CATEGORIES)
MATERIAL_OPTIONS: dict[str, tuple[str, ...]] = dict(_FALLBACK_MATERIAL_OPTIONS)
CONTACTOR_PAIR_TO_LAWS: dict[str, tuple[str, ...]] = dict(_FALLBACK_CONTACT_LAW_CATEGORIES)

try:
    _mod = _import_lmgc90dicts_module()
    PYLMGC90_RAW = _harvest_public_dicts(_mod)
    FROM_PYLMGC90 = True
    _loaded: set[str] = set()

    # 1) Contact-law parameter lists
    _tb = _pick(
        PYLMGC90_RAW,
        "tactBehavOptions",
        "tact_behav_options",
        "behavOptions",
    )
    if _tb is not None:
        _CONTACT_LAW_OPTIONS = _as_tuple_dict(_tb)
        _loaded.add("tactBehavOptions")

    # 2) Contactor-pair → allowed laws
    _cp = _pick(
        PYLMGC90_RAW,
        "contactorPairToTactBehav",
        "contactorPairsToTactBehav",
        "contactorPairToTactBehavs",
        "contactor_pair_to_tact_behav",
    )
    if _cp is not None:
        CONTACT_LAW_CATEGORIES = _as_tuple_dict(_cp)
        CONTACTOR_PAIR_TO_LAWS = CONTACT_LAW_CATEGORIES
        _loaded.add("contactorPairToTactBehav")

    # 3) Material type → option names (several possible attribute names)
    _mo = _pick(
        PYLMGC90_RAW,
        "materialTypeOptions",
        "materialOptions",
        "bulkBehavOptions",
        "bulk_behav_options",
        "material_type_options",
    )
    if _mo is not None:
        MATERIAL_OPTIONS = _as_tuple_dict(_mo)
        _loaded.add(next(n for n in (
            "materialTypeOptions", "materialOptions", "bulkBehavOptions",
            "bulk_behav_options", "material_type_options",
        ) if n in PYLMGC90_RAW))

    # 4) Any other dicts of interest (kept in PYLMGC90_RAW, flag listed)
    for extra in (
        "bodyTypeToContactor",
        "avatarTypeToContactor",
        "seeTableOptions",
        "modelOptions",
        "elementOptions",
        "physicsOptions",
        "colorList",
        "colors",
    ):
        if extra in PYLMGC90_RAW:
            _loaded.add(extra)

    FROM_PYLMGC90_KEYS = frozenset(_loaded)
except Exception:
    FROM_PYLMGC90 = False
    FROM_PYLMGC90_KEYS = frozenset()
    PYLMGC90_RAW = {}
    _CONTACT_LAW_OPTIONS = dict(_FALLBACK_CONTACT_LAW_OPTIONS)
    CONTACT_LAW_CATEGORIES = dict(_FALLBACK_CONTACT_LAW_CATEGORIES)
    MATERIAL_OPTIONS = dict(_FALLBACK_MATERIAL_OPTIONS)
    CONTACTOR_PAIR_TO_LAWS = dict(_FALLBACK_CONTACT_LAW_CATEGORIES)


# Convenience aliases (GUI / filters) derived from categories
def _laws_in(*keys: str) -> tuple[str, ...]:
    seen: list[str] = []
    for k in keys:
        for law in CONTACT_LAW_CATEGORIES.get(k, ()):
            if law not in seen:
                seen.append(law)
    return tuple(seen)


LAWS_RIGID_RIGID = _laws_in("rigid/rigid")
LAWS_ANY_DEFORMABLE = _laws_in("deformable/deformable")
LAWS_RIGID_DEFORMABLE = _laws_in("rigid/deformable")
LAWS_POINT_POINT = _laws_in("point/point")
LAWS_ANY_ANY = _laws_in("any/any")

# If live categories use slightly different keys, still expose something useful
if not LAWS_RIGID_RIGID and CONTACT_LAW_CATEGORIES:
    # fallback: union of all category values
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

MODEL_OPTION_CHOICES: dict[str, tuple[str, ...]] = {
    "anisotropy": ("iso__", "ortho"),
    "kinematic": ("small", "large"),
    "formulation": ("UpdtL", "TotaL"),
    "mass_storage": ("lump_", "coher"),
    "material": ("elas_", "elasd", "J2iso", "J2mix", "kvisc"),
    "external_model": ("MatL_", "Demfi", "Umat_", "no___", "yes__"),
    "capacity_storage": ("lump_", "coher"),
    "convection_type": ("supg_", "char_", "center"),
    "physical_type": ("fluid", "solid"),
    "fluid_comp_storage": ("lump_", "coher"),
}

# ---------------------------------------------------------------------------
# Elements by physics (source of truth for MODEL_OPTIONS_BY_PHYSICS)
# Keys of the inner dicts are free (usually "2D" / "3D"); only .values() is used.
# ---------------------------------------------------------------------------
RIGID_ELEMENTS_2D: tuple[str, ...] = ("Rxx2D",)
RIGID_ELEMENTS_3D: tuple[str, ...] = ("Rxx3D",)

ELEMENTS_BY_PHYSICS: dict[str, dict[str, tuple[str, ...]]] = {
    # ----- Mécanique des solides -----
    "MECAx": {
        2: (
            # Continus 2D
            "T3xxx", "T3Lxx", "T33xx",
            "T6xxx", "T63xx",
            "DKTxx",
            "Q4xxx", "Q4P0x", "Q44xx",
            "Q8xxx", "Q8Rxx", "Q84xx",
            "Q9xxx",
            # Barres / ressorts
            "BARxx", "SPRG2", "S2xth",
            # Rigide
            "Rxx2D",
        ),
        3: (
            # Continus 3D
            "TE4xx", "TE4Lx", "TE44x",
            "TE10x", "TE104",
            "H8xxx", "H88xx",
            "H20xx", "H20Rx", "H208x",
            "PRI6x", "SHB6x", "PRI15",
            # Barres / ressorts
            "BARxx", "SPRG3",
            # Rigide
            "Rxx3D",
        ),
    },

    # ----- Thermique -----
    "THERx": {
        2: (
            "T3xxx", "T6xxx", "DKTxx",
            "Q4xxx", "Q4P0x", "Q8xxx", "Q8Rxx",
            "S2xth", "SPRG2",
        ),
        3: (
            "TE4xx", "TE10x",
            "H8xxx", "H20xx", "H20Rx",
            "PRI6x", "PRI15",
            "SPRG3",
        ),
    },

    # ----- Poro-mécanique / hydraulique -----
    "POROx": {
        2: (
            "T3xxx", "T6xxx",
            "Q4xxx", "Q4P0x", "Q8xxx", "Q8Rxx",
        ),
        3: (
            "TE4xx", "TE10x",
            "H8xxx", "H20xx", "H20Rx",
            "PRI6x", "PRI15",
        ),
    },

    # ----- Multi-physique (couplages) -----
    "MULTI": {
        2: (
            "T3xxx", "T6xxx",
            "Q4xxx", "Q8xxx",
        ),
        3: (
            "TE4xx", "TE10x",
            "H8xxx", "H20xx",
            "PRI6x", "PRI15",
        ),
    },
}

_MECHANICAL_MODEL_OPTIONS = ("kinematic", "formulation", "mass_storage")
_THERMAL_MODEL_OPTIONS = {
    **{
        element: ("capacity_storage", "formulation", "convection_type")
        for element in (
            "T3xxx", "T6xxx", "DKTxx", "Q4xxx", "Q4P0x", "Q8xxx", "Q8Rxx",
            "S2xth", "TE4xx", "TE10x", "H8xxx", "H20xx", "H20Rx", "PRI6x",
            "PRI15",
        )
    },
    "SPRG2": ("capacity_storage",),
    "SPRG3": ("capacity_storage",),
}
_POROMECHANICAL_MODEL_OPTIONS = {
    element: ("kinematic", "mass_storage", "capacity_storage")
    for elements in ELEMENTS_BY_PHYSICS["POROx"].values()
    for element in elements
}
_MULTIPHYSICS_MODEL_OPTIONS = {
    element: ("kinematic", "mass_storage", "formulation")
    for elements in ELEMENTS_BY_PHYSICS["MULTI"].values()
    for element in elements
}

MODEL_OPTIONS_BY_PHYSICS: dict[str, dict[str, tuple[str, ...]]] = {
    "MECAx": {
        element: _MECHANICAL_MODEL_OPTIONS
        for elements in ELEMENTS_BY_PHYSICS["MECAx"].values()
        for element in elements
        if element not in RIGID_ELEMENTS_2D + RIGID_ELEMENTS_3D
    },
    "THERx": _THERMAL_MODEL_OPTIONS,
    "POROx": _POROMECHANICAL_MODEL_OPTIONS,
    "MULTI": _MULTIPHYSICS_MODEL_OPTIONS,
}

MODEL_COMMON_OPTIONS_BY_PHYSICS: dict[str, tuple[str, ...]] = {
    "MECAx": ("material", "anisotropy", "external_model"),
    "THERx": ("external_model",),
    "POROx": (
        "material", "anisotropy", "external_model", "physical_type",
        "convection_type",
    ),
    "MULTI": (
        "material", "anisotropy", "external_model", "fluid_comp_storage",
        "convection_type",
    ),
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

MODEL_OPTION_CHOICES_BY_PHYSICS: dict[str, dict[str, tuple[str, ...]]] = {
    "THERx": {
        "formulation": ("class",),
        "external_model": ("no___", "yes__"),
    },
}

DEFORMABLE_2D = {
    "T3xxx", "T3Lxx", "T33xx", "T6xxx", "T63xx", "DKTxx",
    "Q4xxx", "Q4P0x", "Q44xx", "Q8xxx", "Q8Rxx", "Q84xx", "Q9xxx",
    "BARxx", "SPRG2", "S2xth",
}
DEFORMABLE_3D = {
    "TE4xx", "TE4Lx", "TE44x", "TE10x", "TE104",
    "H8xxx", "H88xx", "H20xx", "H20Rx", "H208x",
    "PRI6x", "SHB6x", "PRI15", "BARxx", "SPRG3",
}

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
