"""Runtime-backed contact-law parameter fields with core defaults as fallback."""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from .introspection import _load_compatibility_catalogs


@lru_cache(maxsize=1)
def _runtime_law_options() -> dict[str, tuple[str, ...]]:
    catalogs = _load_compatibility_catalogs()
    raw = catalogs.get("tactBehavOptions", {})
    return {
        str(law): tuple(str(option) for option in options)
        for law, options in raw.items()
    }


@lru_cache(maxsize=1)
def _runtime_law_categories() -> dict[str, tuple[str, ...]]:
    catalogs = _load_compatibility_catalogs()
    raw = catalogs.get("contactorPair2TactBehav", {})
    return {
        str(category): tuple(str(law) for law in laws)
        for category, laws in raw.items()
    }


def contact_law_catalog(
    known_laws: tuple[str, ...] | list[str],
    fallback_categories: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    """Return GUI categories filtered to known and installed contact laws."""
    runtime_options = _runtime_law_options()
    runtime_categories = _runtime_law_categories()
    if runtime_options:
        law_order = tuple(runtime_options)
        law_names = set(law_order)
    else:
        core_allowed_laws = {
            law for laws in fallback_categories.values() for law in laws
        }
        law_order = tuple(law for law in known_laws if law in core_allowed_laws)
        law_names = set(law_order)

    category_sources = {
        "rigid/rigid": ("rigid/rigid",),
        "any/defo": (
            "any/defo", "rigid/deformable", "deformable/deformable",
        ),
        "point/point": ("point/point",),
        "any/any": ("any/any",),
    }
    categories = {}
    for category, source_keys in category_sources.items():
        if category in runtime_categories:
            values = runtime_categories[category]
        elif runtime_categories:
            values = ()
        else:
            values = tuple(
                law for key in source_keys
                for law in fallback_categories.get(key, ())
            )
        categories[category] = tuple(dict.fromkeys(
            law for law in values if law in law_names
        ))

    return {
        "source": "pylmgc90" if runtime_categories else "core_fallback",
        "laws": law_order,
        "categories": categories,
    }


def contact_law_pair_compatibility(
    law_type: str,
    candidate_body: str,
    candidate_contactor: str,
    antagonist_body: str,
    antagonist_contactor: str,
) -> bool | None:
    """Check a law/contact pair from pylmgc tables; None means no reliable data."""
    catalogs = _load_compatibility_catalogs()
    categories = catalogs.get("contactorPair2TactBehav")
    body_contactors = catalogs.get("bodyType2contactor")
    rigid = set(catalogs.get("rigidContactor", ()))
    points = set(catalogs.get("pointContactor", ()))
    if not categories or not body_contactors or not rigid or not points:
        return None

    aliases = {
        "CSpxx": "CSxxx", "CSxx3": "CSxxx", "CSxx4": "CSxxx",
        "ASpx3": "ASpxx", "ASpx4": "ASpxx",
        "POLYD": "POLYR", "POLYF": "POLYR", "POLYO": "POLYR",
    }

    def normalize(shape: str) -> str:
        return aliases.get(shape, shape)

    candidate = normalize(candidate_contactor)
    antagonist = normalize(antagonist_contactor)
    supported_candidate = set(body_contactors.get(candidate_body, ()))
    supported_antagonist = set(body_contactors.get(antagonist_body, ()))
    if candidate_contactor not in supported_candidate or antagonist_contactor not in supported_antagonist:
        return False

    candidate_point = candidate in points
    antagonist_point = antagonist in points
    if candidate_point != antagonist_point:
        compatible_laws = set(categories.get("any/any", ()))
    elif candidate_point:
        compatible_laws = (
            set(categories.get("point/point", ()))
            | set(categories.get("any/any", ()))
        )
    elif candidate in rigid and antagonist in rigid:
        compatible_laws = (
            set(categories.get("rigid/rigid", ()))
            | set(categories.get("any/any", ()))
        )
    else:
        compatible_laws = (
            set(categories.get("any/defo", ()))
            | set(categories.get("any/any", ()))
        )
    return law_type in compatible_laws


def contact_law_property_schema(
    law_type: str,
    fallback: tuple[tuple[str, Any, str], ...] = (),
) -> tuple[tuple[str, Any, str], ...]:
    """Use installed pylmgc parameter names, retaining known defaults when possible.

    Parameters absent from the core fallback are marked required with a ``None``
    default. If pylmgc or its parameter catalog is unavailable, the fallback is
    returned unchanged.
    """
    runtime = _runtime_law_options().get(str(law_type))
    if runtime is None:
        return tuple(fallback)

    defaults = {name: (default, kind) for name, default, kind in fallback}
    return tuple(
        (name, defaults[name][0], defaults[name][1])
        if name in defaults else (name, None, "float")
        for name in runtime
    )