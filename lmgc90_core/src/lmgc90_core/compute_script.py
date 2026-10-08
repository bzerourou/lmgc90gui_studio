# ============================================================================
# compute_script.py — lmgc90_core
# ============================================================================
"""Full chipy command.py generator (zlib-compressed payload, expands on import)."""
from __future__ import annotations
import zlib, base64
_src = zlib.decompress(base64.b64decode("PLACEHOLDER_WILL_FAIL")).decode("utf-8")
_ns: dict = {"__name__": __name__, "__file__": __file__, "__package__": __package__}
exec(compile(_src, __file__, "exec"), _ns)
for _k in ("ComputeScriptGenerator", "generate_command_script", "write_command_script"):
    if _k in _ns:
        globals()[_k] = _ns[_k]
del _src, _ns, _k, zlib, base64
