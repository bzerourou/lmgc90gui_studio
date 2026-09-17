"""Stable identities. Never reuse a consumed id. Never key by list index."""
from __future__ import annotations

import uuid


def new_avatar_id() -> str:
    return uuid.uuid4().hex


def new_population_id() -> str:
    return "pop_" + uuid.uuid4().hex


def particle_id(population_id: str, index: int) -> str:
    return f"{population_id}:{index}"


def parse_particle_id(avatar_id: str) -> tuple[str, int] | None:
    if ":" not in avatar_id:
        return None
    pop_id, _, rest = avatar_id.partition(":")
    if not pop_id.startswith("pop_"):
        return None
    try:
        idx = int(rest)
    except ValueError:
        return None
    return pop_id, idx
