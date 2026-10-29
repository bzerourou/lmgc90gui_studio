"""Règles chipy partagées — Python pur (ni Qt, ni pylmgc90, ni numpy).

"""
from __future__ import annotations

import re
from typing import Any, Iterable, Mapping, Optional

# --------------------------------------------------------------------------
# Détecteurs d'interaction (modules de chipy.macro.SelectProxTactors)
# nom -> (contacteur A, contacteur B)
# --------------------------------------------------------------------------
DETECTORS_2D: dict[str, tuple[str, str]] = {
    "CLALp": ("CLxxx", "ALpxx"),
    "CLJCx": ("CLxxx", "JONCx"),
    "DKALp": ("DISKx", "ALpxx"),
    "DKDKL": ("DISKx", "DISKL"),
    "DKDKx": ("DISKx", "DISKx"),
    "DKJCx": ("DISKx", "JONCx"),
    "DKKDx": ("DISKx", "xKSID"),      # disque / disque creux ou discret
    "DKPLx": ("DISKx", "POLYG"),
    "P2P2L": ("PT2DL", "PT2DL"),
    "PLALp": ("POLYG", "ALpxx"),
    "PLJCx": ("POLYG", "JONCx"),
    "PLPLx": ("POLYG", "POLYG"),      # briques rigides polygonales
    "PTPT2": ("PT2Dx", "PT2Dx"),
}
DETECTORS_3D: dict[str, tuple[str, str]] = {
    "CDCDx": ("CYLND", "CYLND"),
    "CDPLx": ("CYLND", "PLANx"),
    "CSASp": ("CSxxx", "ASpxx"),
    "CSPRx": ("CSxxx", "POLYR"),
    "PRASp": ("POLYR", "ASpxx"),
    "PRPLx": ("POLYR", "PLANx"),
    "PRPRx": ("POLYR", "POLYR"),
    "PTPT3": ("PT3Dx", "PT3Dx"),
    "SPCDx": ("SPHER", "CYLND"),
    "SPDCx": ("SPHER", "DNLYC"),
    "SPPLx": ("SPHER", "PLANx"),
    "SPPRx": ("SPHER", "POLYR"),
    "SPSPx": ("SPHER", "SPHER"),
}

# Anciennes clés de préférences -> détecteur réel
LEGACY_FLAGS = {
    "use_PT2Dx": "use_PTPT2",
    "use_PT3Dx": "use_PTPT3",
    "use_DKMECAx": "use_DKALp",
    "use_ALpMECAx": "use_CLALp",
}
# Clés sans aucun équivalent chipy : ignorées
DROPPED_FLAGS = ("use_SPMECAx", "use_ALpALp", "use_NODES")


def canon_shape(shape: Optional[str]) -> str:
    """Normalise un nom de contacteur (casse ; CSpxx -> CSxxx, à confirmer)."""
    s = (shape or "").strip().lower()
    return "csxxx" if s == "cspxx" else s


def _pair_index(table: Mapping[str, tuple[str, str]]) -> dict[frozenset, str]:
    return {frozenset(canon_shape(s) for s in pair): name for name, pair in table.items()}


_PAIRS = {2: _pair_index(DETECTORS_2D), 3: _pair_index(DETECTORS_3D)}


def detector_for_pair(a: str, b: str, dimension: int) -> Optional[str]:
    """Détecteur chipy pour une paire de contacteurs, ou None s'il n'existe pas."""
    return _PAIRS[2 if int(dimension) == 2 else 3].get(
        frozenset({canon_shape(a), canon_shape(b)})
    )


def explicit_flags(params: Mapping[str, Any]) -> dict[str, bool]:
    """Flags use_* réellement fournis par l'appelant, alias résolus."""
    flags = {k: bool(v) for k, v in params.items()
             if k.startswith("use_") and v is not None}
    for old, new in LEGACY_FLAGS.items():
        if old in flags:
            if flags.pop(old):
                flags[new] = True
    for key in DROPPED_FLAGS:
        flags.pop(key, None)
    return flags


def select_detectors(dimension: int,
                     params: Optional[Mapping[str, Any]] = None,
                     visibility: Iterable[Any] = ()) -> list[str]:
    """Détecteurs à émettre, dans l'ordre officiel, pour la dimension donnée.

    Un flag fourni explicitement (True/False) l'emporte ; sinon on déduit des
    tables de visibilité (seules sources de vérité des paires qui interagissent).
    Les détecteurs de l'autre dimension sont toujours exclus.
    """
    table = DETECTORS_2D if int(dimension) == 2 else DETECTORS_3D
    explicit = explicit_flags(params or {})
    inferred = {
        detector_for_pair(r.candidate_contactor, r.antagonist_contactor, dimension)
        for r in visibility
    }
    return [name for name in table if explicit.get(f"use_{name}", name in inferred)]


# --------------------------------------------------------------------------
# Inspections / extractions
# --------------------------------------------------------------------------
_NB_SELF = re.compile(r"^(?P<m>\w+?)_GetNb(?P=m)$", re.IGNORECASE)


def takes_no_id(entry: Mapping[str, Any],
                known_no_id: Iterable[str] = ()) -> bool:
    """Appel sans identifiant ?

    Vrai pour <Module>_GetNb<Module> (DISKx_GetNbDISKx...) ou quand l'utilisateur
    n'a donné ni IDs ni groupe. L'ancienne règle « 'GetNb' in nom » classait à
    tort DISKx_GetNbPointOutlines(i) parmi les fonctions sans argument.
    """
    func = entry.get("func", "")
    if func in known_no_id or _NB_SELF.match(func):
        return True
    return not ((entry.get("ids") or "").strip() or (entry.get("group") or "").strip())


def inspection_statement(entry: Mapping[str, Any],
                         known_no_id: Iterable[str] = ()) -> str:
    """Une instruction Python valide (sans indentation) pour une entrée."""
    func = entry["func"]
    store = (entry.get("store") or "").strip()
    if store and not store.isidentifier():
        raise ValueError(f"nom de variable invalide : {store!r}")
    if takes_no_id(entry, known_no_id):
        call = f"chipy.{func}()"
        return f"{store} = {call}" if store else call
    call = f"chipy.{func}(_id)"
    return f"{store}.setdefault(_id, []).append({call})" if store else call


def store_init_lines(entries: Iterable[Mapping[str, Any]],
                     known_no_id: Iterable[str] = ()) -> list[str]:
    """`nom = {}` (une fois, avant la boucle) pour chaque variable par-ID."""
    names: list[str] = []
    for e in entries:
        store = (e.get("store") or "").strip()
        if store and not takes_no_id(e, known_no_id) and store not in names:
            names.append(store)
    return [f"{n} = {{}}" for n in names]


# --------------------------------------------------------------------------
# Critère d'arrêt (les anciennes fonctions chipy.Get* n'existent pas)
# --------------------------------------------------------------------------
STOP_VECTORS = {"vel_max": "V____", "disp_max": "X____"}


def stop_criterion_lines(kind: str, dimension: int) -> list[str]:
    """Lignes calculant `_crit` à partir de RBDYx_GetBodyVector (API réelle)."""
    vec = STOP_VECTORS.get(kind)
    if vec is None:
        raise ValueError(
            f"critère d'arrêt {kind!r} sans équivalent chipy "
            f"(disponibles : {', '.join(STOP_VECTORS)})"
        )
    px = "RBDY2" if int(dimension) == 2 else "RBDY3"
    return [
        "_crit = max(",
        f"    (float(np.abs(chipy.{px}_GetBodyVector({vec!r}, _i)).max())",
        f"     for _i in range(1, chipy.{px}_GetNb{px}() + 1)),",
        "    default=float('inf'))",   # aucun corps rigide -> ne jamais s'arrêter
    ]