"""Engine-specific errors. Core ValidationError is reused where appropriate."""
from __future__ import annotations


class EngineError(Exception):
    """Base for lmgc90_engine failures."""


class PylmgcNotAvailable(EngineError):
    """pylmgc90 is not installed or cannot be imported."""


class MaterializationError(EngineError):
    """Failed to turn a core entity into a pylmgc90.pre object."""


class UnknownBodyError(EngineError):
    """avatar_id / population_id not present in the session maps."""


class DatboxError(EngineError):
    """writeDatbox or path-related failure."""
