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
    IQS_MOHR_DS_CLB = "IQS_MOHR_DS_CLB"
    IQS_MAC_CZM = "IQS_MAC_CZM"
    RST_CLB = "RST_CLB"
    GAP_SGR_CLB = "GAP_SGR_CLB"
    GAP_SGR_CLB_G0 = "GAP_SGR_CLB_g0"
    GAP_MOHR_DS_CLB = "GAP_MOHR_DS_CLB"
    MAC_CZM = "MAC_CZM"
    MAL_CZM = "MAL_CZM"
    ELASTIC_WIRE = "ELASTIC_WIRE"
    BRITTLE_ELASTIC_WIRE = "BRITTLE_ELASTIC_WIRE"
    ELASTIC_ROD = "ELASTIC_ROD"
    VOIGT_ROD = "VOIGT_ROD"
    COUPLED_DOF = "COUPLED_DOF"
    NORMAL_COUPLED_DOF = "NORMAL_COUPLED_DOF"
    ELASTIC_REPELL_CLB = "ELASTIC_REPELL_CLB"


class AvatarOrigin(str, Enum):
    MANUAL = "manual"
    LOOP = "loop"
    GRANULO = "granulo"
    FACTORY = "factory"


class UnitSystem(str, Enum):
    SI = "SI"
    CGS = "CGS"


LAWS_RIGID_RIGID = (
    "IQS_CLB", "IQS_CLB_g0", "IQS_DS_CLB",
    "IQS_MOHR_DS_CLB", "IQS_MAC_CZM", "RST_CLB",
)
LAWS_RIGID_DEFORMABLE = (
    "GAP_SGR_CLB", "GAP_SGR_CLB_g0", "GAP_MOHR_DS_CLB", "MAC_CZM", "MAL_CZM",
)
LAWS_POINT_POINT = (
    "ELASTIC_WIRE", "BRITTLE_ELASTIC_WIRE", "ELASTIC_ROD", "VOIGT_ROD",
)
LAWS_ANY_ANY = (
    "COUPLED_DOF", "NORMAL_COUPLED_DOF", "ELASTIC_REPELL_CLB",
)

CONTACT_LAW_CATEGORIES = {
    "rigid/rigid": LAWS_RIGID_RIGID,
    "rigid/deformable": LAWS_RIGID_DEFORMABLE,
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

# Contact-law type → extra kwargs beyond name / law / fric
CONTACT_LAW_PROPERTY_SCHEMA: dict[str, tuple[tuple[str, object, str], ...]] = {
    "IQS_CLB": (("fric", 0.3, "float"),),
    "IQS_CLB_g0": (("fric", 0.3, "float"), ("g0", 0.0, "float")),
    "IQS_DS_CLB": (("fric", 0.3, "float"), ("Rest", 0.0, "float")),
    "IQS_MOHR_DS_CLB": (("fric", 0.3, "float"), ("cohes", 0.0, "float"), ("Rest", 0.0, "float")),
    "IQS_MAC_CZM": (("W", 100.0, "float"), ("dn", 1e-4, "float"), ("dt", 1e-4, "float")),
    "RST_CLB": (("fric", 0.3, "float"), ("Rest", 0.0, "float")),
    "GAP_SGR_CLB": (("fric", 0.3, "float"),),
    "GAP_SGR_CLB_g0": (("fric", 0.3, "float"), ("g0", 0.0, "float")),
    "GAP_MOHR_DS_CLB": (("fric", 0.3, "float"), ("cohes", 0.0, "float")),
    "MAC_CZM": (("W", 100.0, "float"), ("dn", 1e-4, "float"), ("dt", 1e-4, "float")),
    "MAL_CZM": (("W", 100.0, "float"), ("dn", 1e-4, "float"), ("dt", 1e-4, "float")),
    "ELASTIC_WIRE": (("stiffness", 1e5, "float"), ("prestrain", 0.0, "float")),
    "BRITTLE_ELASTIC_WIRE": (("stiffness", 1e5, "float"), ("force_max", 1e3, "float")),
    "ELASTIC_ROD": (("stiffness", 1e5, "float"),),
    "VOIGT_ROD": (("stiffness", 1e5, "float"), ("viscosity", 10.0, "float")),
    "COUPLED_DOF": (),
    "NORMAL_COUPLED_DOF": (),
    "ELASTIC_REPELL_CLB": (("stiffness", 1e6, "float"),),
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
