# Developer guide (technical reference)

This chapter is a **technical reference** for contributors working on LMGC90_GUI Studio (architecture, packages `lmgc90_core` / `lmgc90_gui` / `lmgc90_engine`, script generators, tests).

It is not an end-user modelling guide. User documentation starts at the [index](overview.md).

Key areas:

* **lmgc90_core** — project model, validation, `pre` / `command.py` generation (`compute_script.py`).
* **lmgc90_gui** — Qt interface, tabs, chipy routines dialog, preferences.
* **lmgc90_engine** — workers and execution helpers when present.

Generation of computation scripts must keep advanced chipy options in the correct place relative to the time loop (before / inside / after). See the French developer pages for detailed diagrams if this English page is kept brief.
