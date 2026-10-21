"""LMGC90 vocabulary — names match pylmgc90.pre, not GUI labels."""
from __future__ import annotations

from enum import Enum


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


LAWS_RIGID_RIGID = (
    "IQS_CLB", "IQS_CLB_g0", "IQS_DS_CLB", "RST_CLB",
    "IQS_WET_DS_CLB", "xQS_WET_DS_CLB", "IQS_MOHR_DS_CLB",
    "IQS_MAC_CZM", "IQS_WET_CZM", "IQS_MAL_CZM", "IQS_TH_CZM",
    "BRITTLE_COATING_CLB", "IQS_ABP_CZM", "IQS_EXPO_CZM",
    "IQS_EXPO_CZM_SPRING", "IQS_STICK", "IQS_CLB_nosldt",
    "IQS_CLB_RGR", "IQS_EXPO_CZM_P", "IQS_EXPO_CZM_SPRING_P",
)
LAWS_ANY_DEFORMABLE = (
    "GAP_SGR_CLB", "GAP_SGR_CLB_g0", "GAP_SGR_STICK",
    "GAP_SGR_CLB_nosldt", "VEL_SGR_CLB", "preGAP_SGR_CLB",
    "MAC_CZM", "MAL_CZM", "GAP_MOHR_DS_CLB", "MP_CZM", "MP3_CZM",
    "MP3_CZM_THER", "TH_CZM", "ABP_CZM", "EXPO_CZM",
    "EXPO_CZM_SPRING", "EXPO_CZM_P", "EXPO_CZM_SPRING_P",
    "GTN_CZM", "GTN2_CZM", "TOSI_CZM", "TOSI_CZM_INCRE",
)
LAWS_RIGID_DEFORMABLE = LAWS_ANY_DEFORMABLE
LAWS_POINT_POINT = (
    "ELASTIC_WIRE", "BRITTLE_ELASTIC_WIRE", "ELASTIC_ROD", "VOIGT_ROD",
    "NARD_ROD",
)
LAWS_ANY_ANY = (
    "COUPLED_DOF", "NORMAL_COUPLED_DOF", "ELASTIC_REPELL_CLB",
    "ELASTIC_REPELL_CLB_g0", "ELASTIC_REPELL_CLB_adapt",
    "VISCO_ELASTIC_REPELL_CLB",
)

CONTACT_LAW_CATEGORIES = {
    "rigid/rigid": LAWS_RIGID_RIGID,
    "any/defo": LAWS_ANY_DEFORMABLE,
    "rigid/deformable": LAWS_ANY_DEFORMABLE,
    "point/point": LAWS_POINT_POINT,
    "any/any": LAWS_ANY_ANY,
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
    # MULTI: union of MECAx elements (multi-physics models accept the same mesh catalogue)
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

# Options are copied from pylmgc90.pre.config.lmgc90dicts.tactBehavOptions.
_CONTACT_LAW_OPTIONS: dict[str, tuple[str, ...]] = {
    "IQS_CLB": ("fric",),
    "IQS_CLB_g0": ("fric",),
    "IQS_DS_CLB": ("dyfr", "stfr"),
    "IQS_CLB_RGR": ("fric", "ToverH", "gtol"),
    "IQS_WET_DS_CLB": ("cohn", "coht", "Wthk", "dyfr", "stfr"),
    "xQS_WET_DS_CLB": ("cohn", "coht", "Wthk", "dyfr", "stfr"),
    "IQS_MOHR_DS_CLB": ("cohn", "coht", "dyfr", "stfr"),
    "IQS_STICK": (),
    "IQS_CLB_nosldt": ("fric", "dt__"),
    "RST_CLB": ("rstn", "rstt", "fric"),
    "GAP_SGR_CLB": ("fric",),
    "GAP_SGR_STICK": (),
    "GAP_SGR_CLB_nosldt": ("fric", "dt__"),
    "preGAP_SGR_CLB": ("pgap", "fric"),
    "VEL_SGR_CLB": ("fric",),
    "GAP_SGR_CLB_g0": ("fric",),
    "GAP_MOHR_DS_CLB": ("cohn", "coht", "dyfr", "stfr"),
    "MAC_CZM": ("dyfr", "stfr", "cn", "ct", "b", "w"),
    "IQS_MAC_CZM": ("dyfr", "stfr", "cn", "ct", "b", "w"),
    "IQS_WET_CZM": ("cohn", "Wthk", "cn", "ct", "visc", "w"),
    "MAL_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2"),
    "IQS_MAL_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2"),
    "COUPLED_DOF": (),
    "NORMAL_COUPLED_DOF": (),
    "ELASTIC_REPELL_CLB": ("stiffness", "fric"),
    "ELASTIC_REPELL_CLB_g0": ("stiffness", "fric"),
    "ELASTIC_REPELL_CLB_adapt": ("stiffness", "fric"),
    "VISCO_ELASTIC_REPELL_CLB": ("stiffness", "viscosity", "fric"),
    "ELASTIC_WIRE": ("stiffness", "prestrain"),
    "ELASTIC_ROD": ("stiffness", "prestrain"),
    "VOIGT_ROD": ("stiffness", "prestrain", "viscosity"),
    "BRITTLE_ELASTIC_WIRE": ("stiffness", "prestrain", "Fmax"),
    "MP_CZM": ("dyfr", "stfr", "cn", "ct", "w"),
    "MP3_CZM": ("dyfr", "stfr", "cn", "ct", "smax", "w"),
    "MP3_CZM_THER": ("dyfr", "stfr", "cn", "ct", "smax", "w", "lambdas", "lambdac"),
    "TH_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "dp1", "dp2"),
    "IQS_TH_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "dp1", "dp2"),
    "ABP_CZM": ("dyfr", "stfr", "cn", "ct", "phi", "s1", "s2", "G1", "G2", "du1", "du2"),
    "IQS_ABP_CZM": ("dyfr", "stfr", "cn", "ct", "phi", "s1", "s2", "G1", "G2", "du1", "du2"),
    "EXPO_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "eta"),
    "IQS_EXPO_CZM": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "eta"),
    "EXPO_CZM_SPRING": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "eta", "k1", "k2"),
    "IQS_EXPO_CZM_SPRING": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "eta", "k1", "k2"),
    "BRITTLE_COATING_CLB": ("fric", "stiffness", "Fmax", "g0"),
    "NARD_ROD": ("E", "nu", "s1", "s2"),
    "GTN_CZM": ("dyfr", "stfr", "cn", "ct", "f0", "fc", "k", "q1", "q2", "e", "Y", "s0", "Kh", "n", "fN", "eN", "sN"),
    "GTN2_CZM": ("dyfr", "stfr", "cn", "ct", "f0", "fc", "k", "q1", "q2", "e", "Y", "s0", "Kh", "n", "fN", "eN", "sN"),
    "TOSI_CZM": ("dyfr", "stfr", "cn", "ct", "f0", "fc", "n", "K", "R", "s0", "Q", "Gc1", "Gc2", "kcoal", "hdef", "n_mol"),
    "TOSI_CZM_INCRE": ("dyfr", "stfr", "cn", "ct", "f0", "fc", "n", "K", "R", "s0", "Q", "Gc1", "Gc2", "kcoal", "hdef", "n_mol"),
    "EXPO_CZM_P": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "mu_g", "eta"),
    "IQS_EXPO_CZM_P": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "mu_g", "eta"),
    "EXPO_CZM_SPRING_P": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "mu_g", "eta", "k1", "k2"),
    "IQS_EXPO_CZM_SPRING_P": ("dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2", "mu_g", "eta", "k1", "k2"),
}

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
