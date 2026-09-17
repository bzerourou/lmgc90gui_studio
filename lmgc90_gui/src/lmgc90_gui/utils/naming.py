"""Default unique names for LMGC90 entities (≤ 5 characters).

Prefixes are short and stable so generated pre.py stays readable.
"""
from __future__ import annotations

from typing import Iterable, Optional, Set

# suggested base (≤5) per kind
DEFAULT_BASES: dict[str, str] = {
    "material": "MAT",
    "material_RIGID": "RIGID",
    "material_ELAS": "ELAS",
    "material_ELAS_DILA": "ELASD",
    "material_VISCO_ELAS": "VISCO",
    "material_ELAS_PLAS": "PLAS",
    "material_THERMO_ELAS": "THERM",
    "material_PORO_ELAS": "PORO",
    "material_DISCRETE": "DISC",
    "material_USER_MAT": "USER",
    "material_EXTERNAL": "EXT",
    "model": "MODEL",
    "model_MECAx": "MECAx",
    "model_THERx": "THERx",
    "model_POROx": "POROx",
    "model_MULTI": "MULTI",
    "model_rigid": "rigid",  # classic rigid model name
    "law": "LAW",
    "law_IQS_CLB": "IQS",
    "law_IQS_CLB_g0": "IQSg0",
    "law_IQS_DS_CLB": "IQSDS",
    "law_RST_CLB": "RST",
    "law_GAP_SGR_CLB": "GAP",
    "law_GAP_SGR_CLB_g0": "GAPg0",
    "law_MAC_CZM": "MAC",
    "law_MAL_CZM": "MAL",
    "law_ELASTIC_WIRE": "WIRE",
    "law_ELASTIC_ROD": "ROD",
    "group": "GRP",
    "postpro": "PP",
}


def _taken(existing: Iterable[str]) -> Set[str]:
    return {str(x).strip() for x in existing if x}


def unique_name(
    base: str,
    existing: Iterable[str],
    *,
    max_len: int = 5,
) -> str:
    """Return ``base`` truncated to *max_len*, or ``base`` + digit, unused in *existing*."""
    taken = _taken(existing)
    base = (base or "X").strip() or "X"
    root = base[:max_len]
    if root not in taken:
        return root
    # try base[:-1] + digit, then base[:-2] + two digits, …
    for width in (1, 2, 3):
        prefix_len = max_len - width
        if prefix_len < 1:
            continue
        prefix = root[:prefix_len]
        limit = 10 ** width
        for i in range(1, limit):
            candidate = f"{prefix}{i:0{width}d}"
            if candidate not in taken:
                return candidate
    # last resort
    for i in range(1, 10000):
        candidate = f"X{i}"[:max_len]
        if candidate not in taken:
            return candidate
    return "XXXXX"


def suggest_material_name(material_type: str, existing: Iterable[str]) -> str:
    key = f"material_{material_type}"
    base = DEFAULT_BASES.get(key) or DEFAULT_BASES["material"]
    # RIGID is 5 chars already; common STEEL / CONCR style aliases
    if material_type == "RIGID" and "STEEL" not in _taken(existing):
        return "STEEL"
    if material_type == "ELAS" and "CONCR" not in _taken(existing):
        return "CONCR"
    return unique_name(base, existing)


def suggest_model_name(physics: str, element: str, existing: Iterable[str]) -> str:
    if element in ("Rxx2D", "Rxx3D"):
        return unique_name("rigid", existing)
    key = f"model_{physics}"
    base = DEFAULT_BASES.get(key) or DEFAULT_BASES["model"]
    return unique_name(base, existing)


def suggest_law_name(law_type: str, existing: Iterable[str]) -> str:
    key = f"law_{law_type}"
    base = DEFAULT_BASES.get(key) or DEFAULT_BASES["law"]
    return unique_name(base, existing)


def suggest_group_name(kind: str, existing: Iterable[str]) -> str:
    base = {
        "granulo": "gran",
        "loop": "loop",
        "for_loop": "fline",
        "depot": "depot",
    }.get(kind, DEFAULT_BASES["group"])
    return unique_name(base, existing, max_len=8)  # groups are free-er
