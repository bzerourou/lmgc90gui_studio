# ============================================================================
# compute_script.py — lmgc90_core
# ============================================================================
"""Full chipy command.py generator (zlib-compressed chunks, expands on import)."""
from __future__ import annotations

from pathlib import Path
import zlib
import base64

_here = Path(__file__).resolve().parent
_parts = []
for _i in range(4):
    _t = (_here / f"_cs_b64_{_i}.txt").read_text(encoding="ascii")
    if _i == 2:
        _t = _t[::-1]  # chunk 2 stored reversed
    _parts.append(_t)
_b64 = "".join(_parts)
_src = zlib.decompress(base64.b64decode(_b64)).decode("utf-8")
_ns: dict = {"__name__": __name__, "__file__": __file__, "__package__": __package__}
exec(compile(_src, __file__, "exec"), _ns)
for _k in ("ComputeScriptGenerator", "generate_command_script", "write_command_script"):
    if _k in _ns:
        globals()[_k] = _ns[_k]
del _src, _ns, _k, zlib, base64, _here, _b64, _parts, _i, _t
