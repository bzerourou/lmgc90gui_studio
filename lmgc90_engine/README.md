# lmgc90_engine

Runtime bridge between **`lmgc90_core.Project`** (pure dataclasses, no Fortran)
and **`pylmgc90.pre` / chipy** (real DATBOX, real bodies).

```
researcher / notebook / GUI
        │
        ▼
   lmgc90_core          Project, entities, CommandHistory, emit pre.py
        │
        ▼
   lmgc90_engine        EngineSession — materialize, map avatar_id → body, writeDatbox
                        schema/ — catalogues, snapshots, audit
        │
        ▼
   pylmgc90.pre / chipy
```

## Install

```bash
pip install -e ../lmgc90_core
pip install -e .                # engine (numpy + core)
# optional, for live materialization:
pip install pylmgc90            # or your site install
```

## Three responsibilities

1. **Materialize** a `Project` into live `pre.materials()`, `pre.models()`,
   `pre.avatars()`, laws, see tables.
2. **Keep identity** — every body is keyed by `avatar_id` / `population_id`,
   never by list index. Deferred sync is possible (dirty flag).
3. **Write the real DATBOX** via `pre.writeDatbox` (or emit the same script
   the core already generates).

## Quick start

```python
from pathlib import Path
from lmgc90_core import Project, pre
from lmgc90_engine import EngineSession

p = Project(name="box", dimension=2)
p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
p.add(pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL"))

session = EngineSession(p)
session.materialize()          # builds pylmgc objects if available
print(session.body_map)        # {avatar_id: <pre body>}
session.write_datbox(Path("DATBOX"))
```

Without `pylmgc90` installed, `materialize()` and `write_datbox()` raise
`PylmgcNotAvailable`. Script emission (`session.emit_pre_script()`) always
works — it delegates to `lmgc90_core`.

## Schema: catalogues, snapshots, audit

Subpackage **`lmgc90_engine.schema`** is the only place that may probe
pylmgc90 **catalogues and APIs** for UI compatibility data (separate from
materialize / DATBOX).

| Module | Role |
|--------|------|
| `introspection.py` | Live catalogues from `lmgc90dicts` (`_CATALOG_NAMES` whitelist); `inspect_runtime()` also describes public `pre` / `chipy` callables |
| `snapshot.py` | Build/write versioned JSON + `index.json` (`lmgc90-engine-snapshot`) |
| `laws.py` / `model_options.py` | Contact-law and model-option helpers for the GUI |
| `audit.py` | Read-only drift report (core catalogues vs installed runtime) |

**Resolution order** for catalogue data used by helpers / status:

1. **INTROSPECTION** — live `lmgc90dicts` when importable
2. **SNAPSHOT** — JSON bundled in `lmgc90_core/capabilities/`
3. **FALLBACK** — empty engine side; core still exposes hard-coded `FALLBACK_*` tables in `lmgc_dicts`

Runtime tab helpers call `load_compatibility_catalogs()` (in-memory cache only).
They do **not** write snapshot files. Snapshots are produced only by the CLI
or `write_capability_snapshot()`.

### Runtime capability snapshots

Export the installed runtime's `pre.*` / Chipy API metadata and available
`lmgc90dicts` catalogues as a versioned JSON snapshot. Run this in the
environment where `pylmgc90` is installed:


```bash
lmgc90-engine-snapshot
```

By default, it writes `src/lmgc90_core/capabilities/pylmgc90-<version>.json`
and updates `index.json`. The core package embeds and loads these pure-JSON
snapshots without importing `pylmgc90`. The engine prefers the bundled snapshot
catalogs and falls back to live runtime introspection when no snapshot is
available.
Use `--output-dir` to write elsewhere; copy the generated snapshot and index
into the core package's `capabilities` directory before rebuilding the core
distribution if you used a custom output directory.

The GUI material form uses the captured material option and conditional-choice
catalogs to build its fields. Runtime material types that are not in the core
enum remain valid string values in saved projects and generated pre-scripts.
The contactors form likewise uses dimension/body-type availability and exposes
the runtime's additional required and optional contactor options. Visibility
suggestions reuse those mappings, including runtime-only shape aliases.

Arity is the number of fixed positional parameters. For opaque native Chipy
bindings it may be inferred from the first docstring line; otherwise `arity`
is `null`. Catalogues are captured as exposed by the install; missing dicts
are not fabricated.

```python
from lmgc90_engine.schema import (
    compatibility_catalog_source,
    load_compatibility_catalogs,
    audit_core_catalogs,
)

print(compatibility_catalog_source())  # INTROSPECTION | SNAPSHOT | FALLBACK
catalogs = load_compatibility_catalogs()
report = audit_core_catalogs()         # optional drift report
```

## Package layout

```
lmgc90_engine/
├── src/lmgc90_engine/
│   ├── __init__.py          public API
│   ├── errors.py
│   ├── session.py           EngineSession (map + dirty + materialize)
│   ├── materialize.py       Project → pre containers
│   ├── avatar_factory.py    Avatar / ParticlePopulation → pre body
│   ├── granulo.py           deposit helpers (pylmgc path)
│   ├── datbox.py            writeDatbox / export helpers
│   └── schema/              capability catalogues & snapshots
│       ├── introspection.py
│       ├── snapshot.py
│       ├── laws.py
│       ├── model_options.py
│       └── audit.py
├── tests/
└── examples/
```

## Rules

- **No Qt.** Engine is headless.
- **No mutation of Project** from the engine side unless the caller asks
  (e.g. granulo that produces a `ParticlePopulation` to add back).
- Identity = `avatar_id` / `population_id`. Always.
- Core remains import-pure: engine is the only place that may `import pylmgc90`.

## Limits 0.7.0

- Mesh builders (gmsh) are stubs / optional; deformable mesh emission relies
  on `mesh_params` already stored on the Avatar.
- Rare avatar types (ovoid, granuloWall3D custom faces) materialize if
  pylmgc exposes the constructor; otherwise a clear error is raised.
- No live chipy solver loop yet — use generated `command.py` + external run.
