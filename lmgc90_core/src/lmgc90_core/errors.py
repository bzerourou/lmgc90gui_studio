"""Domain errors — never leak Qt or pylmgc90 types."""


class LMGC90Error(Exception):
    """Base error for the scientific core."""


class ValidationError(LMGC90Error):
    """An entity violates an LMGC90 or model constraint."""


class UnknownReferenceError(LMGC90Error):
    """A name or id does not resolve in the current project."""


class HistoryError(LMGC90Error):
    """Undo/redo stack cannot satisfy the request."""
