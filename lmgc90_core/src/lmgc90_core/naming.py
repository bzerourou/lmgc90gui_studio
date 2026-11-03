"""Names constrained by LMGC90's fixed-width identifiers."""
from __future__ import annotations


def lmgc5(name: str | None, default: str = "XXXXX") -> str:
    """Return a trimmed LMGC90 identifier, padded or truncated to five characters."""
    value = (name or "").strip() or default
    return value[:5].ljust(5, "x")