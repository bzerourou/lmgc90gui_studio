"""NumPy 2.x compatibility helpers for pylmgc90 (2D cross product).

pylmgc90's writeBodies uses ``numpy.cross`` on 2D frame axes. NumPy 2 only
accepts 3D vectors for ``np.cross``, which breaks DATBOX export.

Call :func:`patch_numpy_cross` once before ``pre.writeDatbox`` / body IO, or
embed :data:`PRE_PY_CROSS_PATCH` at the top of generated ``pre.py`` scripts.
"""
from __future__ import annotations

from typing import Any

# Injected into emitted pre.py (after ``import numpy as np``).
PRE_PY_CROSS_PATCH = '''\
# --- NumPy 2.x + pylmgc90 2D compatibility (np.cross on 2-vectors) ---
_np_cross = np.cross
def _lmgc90_safe_cross(a, b, *args, **kwargs):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape[-1] == 2 and b.shape[-1] == 2:
        return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]
    return _np_cross(a, b, *args, **kwargs)
np.cross = _lmgc90_safe_cross
'''

_patched = False


def patch_numpy_cross(np_module: Any = None) -> bool:
    """Monkey-patch ``np.cross`` in-process. Idempotent. Returns True if applied."""
    global _patched
    if _patched:
        return False
    if np_module is None:
        import numpy as np_module  # type: ignore
    np = np_module
    _np_cross = np.cross

    def _lmgc90_safe_cross(a, b, *args, **kwargs):
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        if a.ndim >= 1 and b.ndim >= 1 and a.shape[-1] == 2 and b.shape[-1] == 2:
            return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]
        return _np_cross(a, b, *args, **kwargs)

    np.cross = _lmgc90_safe_cross  # type: ignore[assignment]
    _patched = True
    return True
