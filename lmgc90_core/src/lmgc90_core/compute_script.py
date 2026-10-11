# ============================================================================
# compute_script.py — lmgc90_core
# ============================================================================
"""Full chipy ``command.py`` generator (no Qt, no engine).

STATUS (2026-10-08)
-------------------
The complete fixed version (887 lines) is ready with these API alignments:

  * PT3Dx contactor → PTPT3 interaction for SelectProxTactors
  * RBDY3 full macro path when dim == 3
  * *MAILx_ prefix (mecaMAILx / therMAILx / poroMAILx) instead of *FEMx_
  * NODES removed from SelectProxTactors list

Because of tool payload size limits, the full source could not be pushed
in one shot through the automated channel.  Get it from the project
workspace:

    artifacts/compute_script_fixed.py

Then copy over this path:

    cp artifacts/compute_script_fixed.py \\
       lmgc90_core/src/lmgc90_core/compute_script.py

Or ask for a re-push of the plain source in a follow-up message.
"""
from __future__ import annotations

raise ImportError(
    "compute_script.py is a temporary pointer. "
    "Copy artifacts/compute_script_fixed.py over this file "
    "(full fixed source, 887 lines, PTPT3 / RBDY3 / *MAILx_)."
)
