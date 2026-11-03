"""Runtime model-option choices with the core vocabulary as fallback."""
from __future__ import annotations

from functools import lru_cache

from .introspection import _load_compatibility_catalogs


@lru_cache(maxsize=1)
def _runtime_model_options() -> dict[str, dict[str, tuple[str, ...]]]:
    raw = _load_compatibility_catalogs().get("modelOptions", {})
    return {
        str(physics): {
            str(option): tuple(str(choice) for choice in choices)
            for option, choices in options.items()
        }
        for physics, options in raw.items()
        if isinstance(options, dict)
    }


def model_option_choices(
    physics: str,
    option: str,
    fallback: tuple[str, ...] | list[str] = (),
) -> tuple[str, ...]:
    """Return installed choices for a model option, or the supplied fallback."""
    choices = _runtime_model_options().get(str(physics), {}).get(str(option))
    if choices is None:
        return tuple(fallback)
    return choices