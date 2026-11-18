# Architecture and contributor guide

This repository contains three installable Python packages: `lmgc90_core`,
`lmgc90_engine`, and `lmgc90_gui`. The package directories are the source of
truth; this guide describes the current code rather than the repository's
historical monolithic GUI architecture.

## Package boundaries

```text
lmgc90_gui  ─────►  lmgc90_engine  ─────►  lmgc90_core
     │                                       ▲
     └───────────────────────────────────────┘
```

| Package | Responsibility |
|---|---|
| `lmgc90_core` | Serializable project entities, validation, undo/redo commands, project I/O, scene builders, and script generation. It does not depend on Qt or pylmgc90. |
| `lmgc90_engine` | Materializes a core `Project` as pylmgc90 objects, writes DATBOX files, and provides runtime compatibility catalogs. The pylmgc90 dependency is optional. |
| `lmgc90_gui` | PyQt6 application, views, dialogs, controller, workers, and the GUI metadata for the example library. Qt and visualization dependencies are optional package extras. |

Keep dependencies flowing toward the core: the core must remain usable without
the engine or GUI. Business rules and persistent data belong in the core;
runtime-specific conversion belongs in the engine; widgets belong in the GUI.

## Repository layout

```text
lmgc90_core/
  src/lmgc90_core/       # entities, Project, commands, validation, I/O, scripts, scenes
  tests/
  examples/
lmgc90_engine/
  src/lmgc90_engine/     # EngineSession, materialization, DATBOX, schema catalogs
  tests/
lmgc90_gui/
  src/lmgc90_gui/
    controller/          # ProjectController and signal compatibility
    views/                # main window, tabs, widgets, 3D viewer
    dialogs/
    workers/
    examples/             # ExampleSpec metadata
  tests/
docs/
  en/
  fr/
```

Each package has its own `pyproject.toml`, source tree, and tests. The
top-level project does not replace those package manifests.

## Core model and persistence

`lmgc90_core.Project` is the project aggregate. Its entities and factories are
defined in `entities.py` and `pre.py`; `types.py` holds enums and fallback
schemas; `validate.py` contains validation; and `commands.py` implements
undoable mutations.

Use the public project methods such as `Project.add`, `Project.deposit`,
`Project.group`, and the corresponding update/remove methods. The
`Project._insert_*` and `Project._drop_*` methods are internal command APIs
used by `commands.py`, not application-facing mutation methods.

`Avatar` and `ParticlePopulation` have stable IDs (`avatar_id` and
`population_id`). Do not use list position as persistent identity. A
`ForLoop`'s `target_kind` determines whether it generates avatars or
populations; there is no `use_soa` flag.

Project files use the `.lmgc90` extension and JSON content. When particle
populations are present, their arrays are stored in a sibling
`.populations.npz` sidecar referenced by the project file. Read and write
through `Project.save` and `Project.load` (or the corresponding functions in
`io.py`) so the metadata and arrays remain in sync.

Useful core modules:

| Module | Responsibility |
|---|---|
| `project.py`, `commands.py` | Project API and undo/redo |
| `entities.py`, `types.py` | Persistent entities, enums, fallback schemas |
| `validate.py` | Core validation |
| `generate.py`, `population.py`, `masonry.py` | Loop, population, and masonry generation |
| `io.py` | Project JSON and population sidecar |
| `pre_script.py`, `chipy_script.py`, `compute_script.py`, `pipeline.py` | Generated solver and batch scripts |
| `scenes/` | Core-only example scene builders |

## Engine

`lmgc90_engine.EngineSession` owns runtime state for a core `Project`.
`materialize.py` converts core entities into pylmgc90 objects and keeps maps
from project IDs to runtime bodies. `datbox.py` handles DATBOX writing;
`avatar_factory.py` builds runtime bodies; and `schema/` provides
compatibility catalogs for runtime-dependent materials, laws, and contactors.

The engine is the boundary for pylmgc90-specific behavior. Do not put
pylmgc90 objects in core entities or GUI state. Code that only emits scripts
or edits projects should not require pylmgc90 to be installed.

## GUI and controller

`lmgc90_gui.controller.ProjectController` is the GUI-facing façade over
`Project` and `EngineSession`. Views read `controller.project` and route
mutations through controller methods. They subscribe to `state_changed` to
refresh; tabs should not own project business logic or runtime pylmgc90
objects.

`views/main_window.py` assembles the current tab and menu registries.
Individual tab factories live under `views/tabs/`; dialogs, workers, and
viewer-specific code live in their respective package directories. Treat the
registries in code as authoritative rather than maintaining a second,
hard-coded list in this guide.

The application entry point is `lmgc90_gui.app.main`; it opens the main
window maximized. Keep diagnostic module paths in tooltips or the application
journal rather than visible labels, since long labels increase the window's
minimum width. The 3D viewer toolbar uses two rows and the results bar keeps a
bounded minimum width so the main window can fit standard desktop displays.

## Example scenes

Core scene builders are functions that receive a `Project` and construct a
scene using core entities and helpers. They are collected in
`lmgc90_core.scenes.SCENE_BUILDERS`. The GUI's `ExampleSpec` entries contain
display metadata and point to those same functions; the GUI checks that each
metadata entry matches the scene registry.

The example-loading UI calls `ProjectController.apply_scene`. Replacing an
example first creates a new project; appending requires the same project
dimension and preserves the existing project and history. `apply_scene`
handles pending granulo configurations as part of applying the scene.

To add an example:

1. Implement the scene in `lmgc90_core/scenes/` using core-only APIs.
2. Export it from `lmgc90_core.scenes` and register its ID in
   `SCENE_BUILDERS`.
3. Add an `ExampleSpec` for that ID in `lmgc90_gui/examples/`.
4. Update the relevant scene/export tests and user documentation if needed.

The GUI's `EXAMPLES` list is the current user-visible catalog; avoid copying
its full inventory into documentation that would immediately become stale.

## Runtime-backed catalogs

Core enums and schemas provide portable fallback data. Where available, the
engine's compatibility catalog uses versioned pylmgc90 data or runtime
introspection; GUI forms use that catalog and fall back to core data when
runtime data is unavailable. When documenting a catalog, state which source
and version it describes rather than implying that a runtime-dependent list
is universal.

## Tests and contribution workflow

Each package has an independent pytest suite. From the package directory,
run:

```text
python -m pytest
```

Keep changes at the layer that owns the behavior. For a new entity or
validation rule, start in core; for pylmgc90 conversion, update engine
materialization; for a widget, update the GUI and call the controller API.
Add focused tests for new behavior and preserve the package's import and
dependency boundaries.
