"""Names constrained by LMGC90's fixed-width identifiers."""
from __future__ import annotations


def lmgc5(name: str | None, default: str = "XXXXX") -> str:
    """Normalize a fixed-width LMGC90 identifier to five characters.

    Padding and truncation are intentionally lossy: distinct inputs may collide.
    Use only for LMGC90 fixed-width fields, never for application group names.
    """
    value = (name or "").strip() or default
    return value[:5].ljust(5, "x")