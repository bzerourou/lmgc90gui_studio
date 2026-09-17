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
│   └── datbox.py            writeDatbox / export helpers
├── tests/
└── examples/
```

## Rules

- **No Qt.** Engine is headless.
- **No mutation of Project** from the engine side unless the caller asks
  (e.g. granulo that produces a `ParticlePopulation` to add back).
- Identity = `avatar_id` / `population_id`. Always.
- Core remains import-pure: engine is the only place that may `import pylmgc90`.

## Limits 0.1.0

- Mesh builders (gmsh) are stubs / optional; deformable mesh emission relies
  on `mesh_params` already stored on the Avatar.
- Rare avatar types (ovoid, granuloWall3D custom faces) materialize if
  pylmgc exposes the constructor; otherwise a clear error is raised.
- No live chipy solver loop yet — use generated `command.py` + external run.
