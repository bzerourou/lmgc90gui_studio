"""
lmgc_dicts.py — Dictionnaires LMGC90 : source pylmgc90 si disponible,
sinon valeurs manuelles (le module core reste fonctionnel sans pylmgc90).

Usage :
    from .lmgc_dicts import ELEMENTS_BY_PHYSICS, GEO2ELEMENT, SOURCES
"""
import importlib
from typing import Any, Callable, Dict, List, Optional, Tuple

# ============================================================================
# 1. Valeurs manuelles (fallback)
# ============================================================================
_ELEMENTS_2D = [
    "Rxx2D", "T3xxx", "T3Lxx", "T33xx", "T6xxx", "T63xx", "DKTxx",
    "Q4xxx", "Q4P0x", "Q44xx", "Q8xxx", "Q8Rxx", "Q84xx", "Q9xxx",
    "BARxx", "SPRG2", "S2xth",
]
_ELEMENTS_3D = [
    "Rxx3D", "TE4xx", "TE4Lx", "TE44x", "TE10x", "TE104",
    "H8xxx", "H88xx", "H20xx", "H20Rx", "H208x",
    "PRI6x", "SHB6x", "PRI15", "BARxx", "SPRG3",
]

_MANUAL_ELEMENTS_BY_PHYSICS: Dict[str, Dict[int, List[str]]] = {
    "MECAx": {2: _ELEMENTS_2D, 3: _ELEMENTS_3D},
    "THERx": {
        2: ["Rxx2D", "T3xxx", "T6xxx", "DKTxx", "Q4xxx", "Q4P0x",
            "Q8xxx", "Q8Rxx", "SPRG2", "S2xth"],
        3: ["Rxx3D", "TE4xx", "TE10x", "H8xxx", "H20xx", "H20Rx",
            "PRI6x", "PRI15", "SPRG3"],
    },
    "POROx": {2: ["T33xx", "T63xx", "Q44xx", "Q84xx"],
              3: ["TE44x", "TE104", "H88xx", "H208x"]},
    "MULTI": {2: ["T33xx", "T63xx", "Q44xx", "Q84xx"],
              3: ["TE44x", "TE104", "H8xxx", "H88xx", "H208x"]},
}

_MANUAL_GEO2ELEMENT: Dict[str, Tuple[str, ...]] = {
    'Point': ('Rxx2D', 'Rxx3D'),
    'S2xxx': ('SPRG2', 'SPRG3', 'BARxx', 'S2xth'),
    'S3xxx': (),
    'Q4xxx': ('Q4xxx', 'Q4P0x', 'Q44xx'),
    'T3xxx': ('T3xxx', 'T3Lxx', 'DKTxx', 'T33xx'),
    'Q8xxx': ('Q8xxx', 'Q8Rxx', 'Q84xx'),
    'Q9xxx': ('Q9xxx',),
    'T6xxx': ('T6xxx', 'T63xx'),
    'TE4xx': ('TE4xx', 'TE4Lx', 'TE44x'),
    'TE10x': ('TE10x', 'TE104'),
    'H8xxx': ('H8xxx', 'H88xx'),
    'H20xx': ('H20xx', 'H20Rx', 'H208x'),
    'PRI6x': ('PRI6x', 'SHB6x'),
    'PRI15': ('PRI15',),
}

_MANUAL_PHYSICS: List[str] = ["MECAx", "THERx", "POROx", "MULTI"]

# Contacteurs (cf. contactor_compat.py)
_MANUAL_CONTACTORS = {
    "RBDY2": ["DISKx", "xKSID", "JONCx", "POLYG", "PT2Dx"],
    "RBDY3": ["SPHER", "PLANx", "CYLND", "POLYR", "PT3Dx"],
    "MAILx_2D": ["CLxxx", "ALpxx", "PT2Dx"],
    "MAILx_3D": ["CSpxx", "ASpxx", "PT3Dx"],
}

# Lois de contact par catégorie (cf. models.py)
_MANUAL_CONTACT_LAWS: Dict[str, List[str]] = {
    "Rigide / Rigide": ["IQS_CLB", "IQS_CLB_g0", "IQS_DS_CLB",
                        "IQS_MOHR_DS_CLB", "IQS_MAC_CZM", "RST_CLB"],
    "Rigide / Déformable (ou Déf/Déf)": ["GAP_SGR_CLB", "GAP_SGR_CLB_g0",
                                         "GAP_MOHR_DS_CLB", "MAC_CZM", "MAL_CZM"],
    "Point / Point": ["ELASTIC_WIRE", "BRITTLE_ELASTIC_WIRE",
                      "ELASTIC_ROD", "VOIGT_ROD"],
    "Toutes (any / any)": ["COUPLED_DOF", "NORMAL_COUPLED_DOF",
                           "ELASTIC_REPELL_CLB"],
}

# Options de modèle (spécifiques au GUI : on les garde manuelles par défaut,
# mais on tente d'enrichir depuis pylmgc90 — voir _CANDIDATES)
_MANUAL_OPTION_VALUES: Dict[str, List[str]] = {
    "kinematic":      ["small", "large"],
    "formulation":    ["UpdtL", "TotaL"],
    "mass_storage":   ["lump_", "coher"],
    "material":       ["elas_", "elasd", "J2iso", "J2mix", "kvisc"],
    "anisotropy":     ["iso__", "ortho"],
    "external_model": ["MatL_", "Demfi", "Umat_", "no___", "yes__"],
}

# ============================================================================
# 2. Chargement de pylmgc90 (jamais bloquant)
# ============================================================================
_IMPORT_PATHS = [
    "pylmgc90.pre_lmgc.lmgc90dicts",
    "pylmgc90.pre_lmgc.config.lmgc90dicts",
    "pylmgc90.lmgc90dicts",
    "pylmgc90.pre_lmgc",
]


def _load_pylmgc_module() -> Optional[Any]:
    for path in _IMPORT_PATHS:
        try:
            mod = importlib.import_module(path)
            return mod
        except Exception:
            continue
    return None


_MOD = _load_pylmgc_module()


def dump_pylmgc_dicts() -> Dict[str, str]:
    """
    Diagnostic : {nom: type} pour chaque attribut public de lmgc90dicts.
    À lancer une fois pour ajuster _CANDIDATES ci-dessous :
        python -c "from src.core.lmgc_dicts import dump_pylmgc_dicts as d; \
                   import pprint; pprint.pprint(d())"
    """
    if _MOD is None:
        return {}
    return {n: type(getattr(_MOD, n)).__name__
            for n in dir(_MOD) if not n.startswith('_')}


# ============================================================================
# 3. Validateurs de forme + adaptateurs
# ============================================================================
def _is_name(s: Any) -> bool:
    return isinstance(s, str) and len(s) == 5


def _is_name_seq(v: Any) -> bool:
    return isinstance(v, (list, tuple)) and all(_is_name(x) for x in v)


def _adapt_geo2element(raw: Any) -> Optional[Dict[str, Tuple[str, ...]]]:
    if not isinstance(raw, dict) or not raw:
        return None
    out = {}
    for k, v in raw.items():
        if isinstance(v, str):
            v = (v,)
        if not (_is_name(k) and _is_name_seq(v)):
            return None
        out[k] = tuple(v)
    return out


def _adapt_physics(raw: Any) -> Optional[List[str]]:
    if isinstance(raw, dict):
        raw = list(raw.keys())
    if isinstance(raw, (list, tuple)) and raw and _is_name_seq(raw):
        return list(raw)
    return None


def _adapt_str_list_dict(raw: Any) -> Optional[Dict[str, List[str]]]:
    if not isinstance(raw, dict) or not raw:
        return None
    out = {}
    for k, v in raw.items():
        if not isinstance(k, str):
            return None
        if isinstance(v, (list, tuple)) and all(isinstance(x, str) for x in v):
            out[k] = list(v)
        else:
            return None
    return out


# nom_interne -> (noms candidats dans lmgc90dicts, adaptateur)
# Complète/corrige ces noms après avoir lancé dump_pylmgc_dicts().
_CANDIDATES: Dict[str, Tuple[List[str], Callable[[Any], Any]]] = {
    "GEO2ELEMENT":   (["geo2elem", "geo2element", "geoToElement",
                       "geo2elements"], _adapt_geo2element),
    "PHYSICS":       (["physicsList", "physics", "physicsDict",
                       "listPhysics"], _adapt_physics),
    "OPTION_VALUES": (["optionValues", "modelOptions", "options",
                       "optionsDict"], _adapt_str_list_dict),
}


def _from_pylmgc(key: str) -> Optional[Any]:
    if _MOD is None or key not in _CANDIDATES:
        return None
    names, adapt = _CANDIDATES[key]
    for n in names:
        if hasattr(_MOD, n):
            try:
                val = adapt(getattr(_MOD, n))
            except Exception:
                val = None
            if val is not None:
                return val
    return None


# ============================================================================
# 4. Résolution finale (pylmgc90 prioritaire, sinon manuel)
# ============================================================================
SOURCES: Dict[str, str] = {}


def _resolve(key: str, manual: Any, merge: bool = False) -> Any:
    """
    merge=True : valeurs pylmgc90 + clés manuelles absentes de pylmgc90
    (utile pour les dicts enrichis par des entrées purement GUI).
    """
    ext = _from_pylmgc(key)
    if ext is None:
        SOURCES[key] = "manuel"
        return manual
    if merge and isinstance(ext, dict) and isinstance(manual, dict):
        merged = dict(manual)
        merged.update(ext)
        SOURCES[key] = "pylmgc90+manuel"
        return merged
    SOURCES[key] = "pylmgc90"
    return ext


GEO2ELEMENT = _resolve("GEO2ELEMENT", _MANUAL_GEO2ELEMENT)
PHYSICS = _resolve("PHYSICS", _MANUAL_PHYSICS)
OPTION_VALUES = _resolve("OPTION_VALUES", _MANUAL_OPTION_VALUES, merge=True)


def _derive_elements_by_physics() -> Dict[str, Dict[int, List[str]]]:
    """
    pylmgc90 ne fournit pas (à ma connaissance) la table physique × dimension :
    on la garde manuelle, mais on la FILTRE par les éléments connus de
    pylmgc90 (GEO2ELEMENT) quand il vient de pylmgc90, pour détecter
    les éléments manuels inexistants.
    """
    table = {p: {d: list(l) for d, l in dims.items()}
             for p, dims in _MANUAL_ELEMENTS_BY_PHYSICS.items()}
    if SOURCES.get("GEO2ELEMENT", "").startswith("pylmgc90"):
        known = {e for els in GEO2ELEMENT.values() for e in els}
        known |= {"Rxx2D", "Rxx3D"}
        for p in table:
            for d in table[p]:
                dropped = [e for e in table[p][d] if e not in known]
                if dropped:
                    import warnings
                    warnings.warn(
                        f"lmgc_dicts: éléments absents de pylmgc90 "
                        f"({p}, {d}D) : {dropped}"
                    )
    return table


ELEMENTS_BY_PHYSICS = _derive_elements_by_physics()
SOURCES["ELEMENTS_BY_PHYSICS"] = "manuel (validé par pylmgc90)" \
    if SOURCES["GEO2ELEMENT"].startswith("pylmgc90") else "manuel"

CONTACTORS = _MANUAL_CONTACTORS;       SOURCES["CONTACTORS"] = "manuel"
CONTACT_LAW_CATEGORIES = _MANUAL_CONTACT_LAWS
SOURCES["CONTACT_LAW_CATEGORIES"] = "manuel"

PYLMGC90_DICTS_AVAILABLE = _MOD is not None