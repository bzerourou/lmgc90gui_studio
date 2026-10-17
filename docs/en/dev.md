# LMGC90_GUI Studio — Architecture & Contributor Guide

> Monorepo `lmgc90gui_studio`: **`lmgc90_core`** 0.1.x · **`lmgc90_engine`** 0.1.x · **`lmgc90_gui`** 0.1.x (window “v0.6.x”).
> This revision replaces the old “monolithic MVC” guide (`src/core`, `ProjectState`, `_pylmgc_bodies`, controller mixins). Old → new mappings are in §1.3.

---

## Table of contents

1. [Overview](#1-overview)
2. [File structure](#2-file-structure)
3. [`lmgc90_core` — the scientific model](#3-lmgc90_core--the-scientific-model)
4. [`lmgc90_engine` — the pylmgc90 bridge](#4-lmgc90_engine--the-pylmgc90-bridge)
5. [`lmgc90_gui` — the PyQt6 client](#5-lmgc90_gui--the-pyqt6-client)
6. [Data flows](#6-data-flows)
7. [Key systems](#7-key-systems)
8. [Project lifecycle](#8-project-lifecycle)
9. [Conventions and patterns](#9-conventions-and-patterns)
10. [Contribution guide](#10-contribution-guide)
11. [Tests](#11-tests)
12. [Known attention points](#12-known-attention-points)

---

## 1. Overview

### 1.1 Three packages, one dependency direction

```
┌──────────────────────────────────────────────────────────────┐
│  lmgc90_gui studio   (PyQt6)                                 │
│  views · tabs · wizards · ProjectController (façade)         │
└───────────────┬──────────────────────────────────────────────┘
                │ depends on
┌───────────────▼──────────────────────────────────────────────┐
│  lmgc90_engine   (optional pylmgc90, no Qt)                  │
│  EngineSession · materialize · DATBOX · pylmgc deposit       │
└───────────────┬──────────────────────────────────────────────┘
                │ depends on
┌───────────────▼──────────────────────────────────────────────┐
│  lmgc90_core   (numpy only, no Qt, no pylmgc90)              │
│  Project · entities · history · validation · scripts         │
└──────────────────────────────────────────────────────────────┘
```

| Package | Role | Dependencies |
|---|---|---|
| `lmgc90_core` | Source of truth: `Project`, entities, `CommandHistory` (undo/redo), validation, numpy generators, `.lmgc90` + `.npz` sidecar serialisation, emission of `pre.py` / `command.py` / `run.sbatch`, example scenes. | `numpy` |
| `lmgc90_engine` | `Project` → real `pylmgc90.pre` objects, DATBOX writing, `pre.visuAvatars`, pylmgc granulo deposit. | `lmgc90_core`, `numpy`, `pylmgc90` *(optional)* |
| `lmgc90_gui` | Qt client: CRUD tabs, wizards, 3D viewer, computation workers, preferences, example catalogue. | `lmgc90_core`, `lmgc90_engine`, `PyQt6` *(optional for headless tests)* |

### 1.2 Architecture rules (non-negotiable)

- **Purity**: `lmgc90_core` never imports `pylmgc90`, `PyQt6`, `pyvista`, `gmsh`, `vtk` (guaranteed by `lmgc90_core/tests/test_purity.py`). The engine only imports `pylmgc90` inside functions (`test_engine_purity.py`).
- **Identity = `avatar_id` / `population_id`**, never a list index.
- **The controller owns no pylmgc90 object.** Live objects live in `EngineSession` after `materialize()`.
- **A single refresh source**: the `state_changed` signal.
- **No business logic in tabs**: they call `controller.*`.
- **AoS vs SoA**: `Avatar` = fine editing; `ParticlePopulation` = mass generation (SoA is the **default** deposit behaviour, no longer a checkbox).
- **Generated `pre.py` = reproducibility artefact** (more than the JSON).

### 1.3 Old → new architecture mapping

| Old (monolithic MVC) | New |
|---|---|
| `src/core/models.py` (`ProjectState`) | `lmgc90_core/entities.py` + `lmgc90_core/project.py` (`Project`) |
| `src/core/validators.py` | `lmgc90_core/validate.py` (`validate_*` functions) |
| `src/core/generators.py` | `lmgc90_core/generate.py` (`loop_positions`, `expand_loop`, `expand_for_loop`, `NumpyGranulo`) |
| `src/core/particle_population*.py` | `lmgc90_core/population.py` + `lmgc90_core/io.py` (sidecar) |
| `src/core/serializers.py` | `lmgc90_core/io.py` |
| `src/core/pylmgc_bridge.py` (`LMGC90Bridge`) | `lmgc90_engine/materialize.py` + `avatar_factory.py` |
| `src/utils/script_generator.py` | `lmgc90_core/pre_script.py` (`emit_pre`) |
| `src/utils/compute_script_generator.py` | `lmgc90_core/compute_script.py` (deprecated GUI-side shim) |
| `src/utils/fast_granulo_engin.py` | `NumpyGranulo` (core) — no separate “fast” engine any more |
| `controllers/*_mixin.py`, `_pylmgc_*` | thin `ProjectController` + `EngineSession` |
| `controller.state` | `controller.project` |
| `pre.*` pylmgc90 in the GUI | `lmgc90_core.pre` (pure factories with the same kwargs) |
| positional `avatar[i]` | still exposed in safe_eval, but real identity is `avatar_id` |
| “SoA” checkbox | `Project.deposit` always produces a `ParticlePopulation` |
| Particle Factory, script converter, Templates, project/granulo wizards | **not ported** in the current version |

---

## 2. File structure

```
lmgc90gui_studio/
├── lmgc90_core/
│   ├── pyproject.toml
│   ├── tests/
│   └── src/lmgc90_core/
│       ├── types.py               # enums, ELEMENTS_BY_PHYSICS, schemas
│       ├── entities.py            # Material, Model, Avatar, …
│       ├── ids.py
│       ├── validate.py
│       ├── project.py             # Project, CommandHistory
│       ├── commands.py            # Add*/Remove*/Update* commands
│       ├── pre.py                 # pure factories (same kwargs as pylmgc90)
│       ├── generate.py            # loops, NumpyGranulo
│       ├── masonry.py             # MasonryConfig, expand_masonry
│       ├── population.py          # ParticlePopulation (SoA)
│       ├── io.py                  # .lmgc90 JSON + .populations.npz
│       ├── pre_script.py          # emit_pre / emit_equivalent
│       ├── chipy_script.py        # emit_chipy
│       ├── compute_script.py      # ComputeScriptGenerator (command.py)
│       ├── pipeline.py            # Pipeline, render_sbatch
│       ├── numpy_compat.py        # patch np.cross (NumPy 2 / 2D)
│       ├── scenes/                # pure demonstration scenes
│       └── data/meshes/Carre.msh
│
├── lmgc90_engine/
│   ├── pyproject.toml
│   ├── examples/session_demo.py
│   ├── tests/
│   └── src/lmgc90_engine/
│       ├── session.py             # EngineSession
│       ├── materialize.py         # Project → pre containers + MaterializedScene
│       ├── avatar_factory.py      # Avatar/Population → pre bodies
│       ├── granulo.py             # pylmgc90 deposit → ParticlePopulation
│       ├── datbox.py              # writeDatbox, dual DATBOX (cell)
│       └── errors.py
│
└── lmgc90_gui/
    ├── pyproject.toml             # extras [qt] [viz] [dev]
    ├── main.py
    ├── examples/                  # headless_demo.py, wave1_scene.py
    ├── tests/
    └── src/lmgc90_gui/
        ├── app.py                 # main() + QApplication
        ├── controller/
        │   ├── project_controller.py
        │   └── signals.py         # pyqtSignal or stubs without Qt
        ├── views/
        │   ├── main_window.py     # create_main_window()
        │   ├── tree_view.py       # Model tree (read-only)
        │   ├── history_dock.py    # command stack + Undo/Redo
        │   ├── viewer_3d.py       # Viewer3D (PyVista)
        │   ├── styles.py
        │   ├── widgets/entity_tree.py
        │   └── tabs/              # material, model, avatar, loop, for_loop,
        │                          # granulo, contact, visibility, dof, postpro,
        │                          # viewer, groups, contactors, deformable,
        │                          # masonry, compute  (+ base_tab.py)
        ├── dialogs/               # wizards, preferences, journal, palette, …
        ├── workers/               # compute_worker, datbox_worker, materialize_worker
        ├── examples/              # ExampleSpec catalogue (metadata)
        ├── utils/                 # safe_eval, eval_context, preferences,
        │                          # app_journal, naming, field_forms, scene_geometry
        └── resources/
```

---

## 3. `lmgc90_core` — the scientific model

### 3.1 `types.py` — LMGC90 vocabulary

Enums (values = `pylmgc90` names): `MaterialType`, `AvatarType`, `ContactLawType`, `AvatarOrigin` (`MANUAL`, `LOOP`, `GRANULO`, `FACTORY`), `UnitSystem`.

Reference tables that drive validation **and** GUI forms:

| Constant | Usage |
|---|---|
| `ELEMENTS_BY_PHYSICS[physics][dim]` | allowed elements (validation + `ModelTab`) |
| `MATERIAL_PROPERTY_SCHEMA`, `MATERIAL_PROPERTY_CHOICES`, `ORTHOTROPIC_FIELDS_2D/3D`, `ISOTROPIC_FIELDS` | `MaterialTab` fields |
| `CONTACT_LAW_PROPERTY_SCHEMA`, `CONTACT_LAW_CATEGORIES` | `ContactTab` fields, law validation |
| `CONTACTORS_RIGID_2D/3D`, `CONTACTORS_MESH_2D/3D` | compatible contactor shapes |
| `RIGID_AVATARS_2D/3D`, `DEFORMABLE_2D/3D` | avatar ↔ model consistency |
| `POPULATION_TYPES` | types eligible for SoA (disk, sphere, discrete disk, cluster, cylinder, polygon, polyhedron) |
| `LOOP_ALIASES` | loop names (FR/EN) → canonical |

### 3.2 `entities.py` — serialisable entities

Dataclasses with no Qt/pylmgc dependency: `Material`, `Model`, `Avatar`, `ContactLaw`, `VisibilityRule`, `DOFOperation`, `PostProCommand`, `Loop`, `ForLoop`, `GranuloConfig`. Each exposes `to_dict()` / `from_dict()`.

```python
@dataclass
class Avatar:
    avatar_type: AvatarType
    center: list[float]
    material_name: str
    model_name: str
    color: str = "BLUEx"
    origin: AvatarOrigin = AvatarOrigin.MANUAL
    avatar_id: str = field(default_factory=new_avatar_id)   # stable
    radius: Optional[float] = None
    axis: Optional[dict] = None              # axe1/axe2/axe3
    vertices, nb_vertices, generation_type, is_hollow
    wall_params, contactors, mesh_params
```

`GranuloConfig` = **intent** of a deposit (arrays live in `ParticlePopulation`). `create_avatars=False` = “distribution only” (radii sampled into `config.radii`, no population).

### 3.3 `ids.py`

```python
new_avatar_id()                 # uuid4 hex
new_population_id()            # "pop_" + uuid4 hex
particle_id(pop_id, i)         # "pop_xxx:42"
parse_particle_id("pop_xxx:42") # → ("pop_xxx", 42)
```

### 3.4 `validate.py`

Functions raising `ValidationError`: `validate_material`, `validate_model`, `validate_avatar(avatar, model)`, `validate_contact_law`, `validate_visibility(rule, law_names)`, plus `compatible_contactors(type, dim)` and `is_shape_compatible`. Key rules: names ≤ 5 characters, density > 0, element compatible with physics/dimension, contactor shapes consistent with avatar type.

### 3.5 `Project` and `CommandHistory`

```python
p = Project(name="box", dimension=2)
p.add(pre.material(...))          # or Material / Model / Avatar / …
p.history.undo(); p.history.redo()
p.save(path); Project.load(path)
```

`Project` holds lists of entities, `populations`, `population_groups`, `granulo`, `dynamic_vars`, `avatar_groups`, and a `CommandHistory`. Mutations that go through `_run(Command)` are undoable. `record=False` is used when rebuilding from disk.

### 3.6 `pre.py` — factories “like pylmgc90”

Pure factories with the same kwargs as pylmgc90 (`material`, `model`, `rigidDisk`, `rigidSphere`, …) returning core entities. Used by the GUI so tabs never import pylmgc90.

### 3.7 `generate.py`, `masonry.py`

- Loops: `loop_positions`, `expand_loop`, `expand_for_loop`.
- Granulo: `NumpyGranulo().deposit(config) → GranuloResult`.
- Masonry: `MasonryConfig`, `expand_masonry` → list of `Avatar` with `origin=FACTORY`.

### 3.8 `population.py` — SoA

See [Particle populations](particle_population.md). `ParticlePopulation.create(...)`, `to_meta_dict` / `from_meta_and_arrays`, `as_avatar_view(i)`.

### 3.9 `io.py` — persistence

JSON `.lmgc90` + optional `.populations.npz` sidecar. Schema migration v1→v2. History stacks restored on load.

### 3.10 Scripts

- `pre_script.emit_pre` → `pre.py`
- `compute_script.ComputeScriptGenerator` → `command.py`
- `chipy_script.emit_chipy` (simpler path)
- `pipeline.render_sbatch` → SLURM

### 3.11 `scenes/`

Pure scene builders (no Qt) used by the example library and tests.

---

## 4. `lmgc90_engine` — the pylmgc90 bridge

### 4.1 `EngineSession`

```python
session = EngineSession(project)
session.materialize()           # → MaterializedScene (raises PylmgcNotAvailable)
session.write_datbox("DATBOX")
session.emit_pre_script("pre.py")   # always available (delegates to core)
session.emit_chipy_script("command.py", dt=1e-3, nb_steps=5000)
session.export_all(dir, try_datbox=True)
session.visu_avatars()              # pre.visuAvatars on drawable bodies
session.run_granulo(config)         # pylmgc deposit → ParticlePopulation
session.mark_dirty(); session.dirty; session.body_map; session.population_map
```

A `dirty` flag allows deferring `materialize()` (worker thread). The controller calls `mark_dirty()` after each mutation.

### 4.2 `materialize.py`

`materialize_project(project) → MaterializedScene` builds in order: materials → models → AoS avatars → populations → laws → see-tables → DOF operations → post-processing. `MaterializedScene` holds the six `pre.*` containers and identity maps:

```python
body_by_avatar_id: dict[str, body]
bodies_by_population_id: dict[str, list[body]]
material_by_name, model_by_name, law_by_name
```

`_make_material` normalises options to the pylmgc90 API (aliases `alpha→dilatation`, `sigc→iso_hard`, orthotropy as lists, `DISCRETE` as vectors, etc.; see `lmgc90_engine/tests/test_material_properties.py`). `_apply_dof` only accepts known kwargs and strips Studio metadata (`phase`, …).

### 4.3 `avatar_factory.py`

`build_avatar(av, materials=, models=)`: one `if` per `AvatarType` (disk, sphere, jonc, polygon, polyhedron, cluster, cylinder, plane, 2D/3D walls, meshed, empty/brick avatar). `build_population_bodies(pop, ...)`: one `pre.rigidXxx` loop per particle (structural pylmgc90 limit). `_apply_contactors` attaches contactors (regular/full `POLYG/POLYR` translation, `shift`, mesh groups). `resolve_mesh_filepath` converts `.brep/.step/.iges/.geo` to `.msh` via **gmsh** (optional).

### 4.4 `granulo.py`, `datbox.py`

- `deposit_population(config)` calls `pre.depositInBox2D/3D`, `…Drum2D/Disk2D`, `…Couette2D`, `…Sphere3D`, `…Cylinder3D` and returns a `ParticlePopulation`.
- `datbox.write_datbox(scene, path)` applies `patch_numpy_cross()` then `pre.writeDatbox(...)`. `write_cell_dual_datbox` writes `DATBOX_SPRD/` + `DATBOX_STBL/` + `PHASES.json` (“cell” scenes). `export_pre_script` does not require pylmgc90.

### 4.5 Errors

`EngineError` ← `PylmgcNotAvailable`, `MaterializationError`, `UnknownBodyError`, `DatboxError`.

---

## 5. `lmgc90_gui` — the PyQt6 client

### 5.1 `ProjectController`

Thin façade (`QObject` if Qt present, else plain object via `signals.py`):

```python
ctrl = ProjectController()          # works without Qt (headless tests)
ctrl.project                         # lmgc90_core.Project
ctrl.session                         # EngineSession
ctrl.prefs, ctrl.journal             # Preferences, AppJournal
ctrl.state_changed / project_loaded / error_occurred   # Signal
with ctrl.batch(): ...               # single state_changed on exit
```

Method families:

| Family | Methods |
|---|---|
| Project | `new_project`, `load_project`, `save_project`, `apply_scene(builder, on_conflict=)` |
| Generic add | `add(obj)` + `add_material/model/avatar/law/visibility/dof/postpro/population` |
| Edit | `update_material/model/law/avatar/visibility/dof`, `remove_*` |
| Generation | `deposit`, `run_granulo_pylmgc`, `apply_loop`, `apply_for_loop`, `apply_masonry` |
| Groups / variables | `group`, `remove_group`, `set_dynamic_var`, `remove_dynamic_var` |
| History | `undo`, `redo` |
| Export / engine | `emit_pre_script`, `emit_chipy_script`, `export_all`, `prepare_run_directory`, `materialize`, `write_datbox`, `visu_avatars`, `pylmgc_available` |
| Preferences | `save_preferences`, `set_work_dir`, `work_dir` |

Any validation error is logged, emitted via `error_occurred`, then re-raised.

### 5.2 Views

- **`main_window.create_main_window(controller)`**: menus (File, Project, Edit, Tools, Computation, Tabs, Examples, Help), toolbar, *Model tree* dock (left), *History* dock (right), `all_tabs` registry (id → title, widget, icon).
- **Default tabs**: `material, model, avatar, contact, visibility, dof, viewer`. `material` and `model` are **essential** (non-closable). `Ctrl+1..9` open the first nine of Tabs → Open.
- **`tree_view`**: read-only; no dedicated population node beyond “Populations (SoA)” yet.
- **`history_dock`**: lists `project.history.describe_stack()` + Undo/Redo buttons.
- **`viewer_3d.Viewer3D`**: parametric PyVista rendering; Nav / Selection / Ruler modes; LMGC90 / type / material / origin colours; DOF and laws (see-tables) overlaid; PNG export. Refresh is **manual** (*Refresh scene* button).

### 5.3 Tabs: “factory” pattern

Each tab is a **function** `create_xxx_tab(parent=None)` that imports PyQt6 locally and returns a `QWidget + BaseTab` class. Tabs read `controller.project` on `state_changed` and call `controller.*` for mutations.

### 5.4 Dialogs and wizards

Preferences, command palette, application journal, chipy routines, example library, deformable/masonry assistants, etc.

### 5.5 Workers

`compute_worker`, `datbox_worker`, `materialize_worker`: QThread wrappers so the UI is not blocked during DATBOX/materialisation/computation.

### 5.6 Utils

| Module | Role |
|---|---|
| `safe_eval.py` / `eval_context.py` | expression evaluation in forms |
| `preferences.py` | `Preferences` (JSON `~/.lmgc90_gui/preferences.json`) |
| `app_journal.py` | circular journal + optional file |
| `field_forms.py` | avatar/DOF parameter schemas, `parse_vertices` |
| `scene_geometry.py` | 2D schematic geometry (subsamples large populations) |
| `compute_script_generator.py` | **deprecated shim** → `lmgc90_core.compute_script` |

### 5.7 Examples

`lmgc90_gui/examples/__init__.py` holds only **metadata** (`ExampleSpec(id, title, category, description, dimension, difficulty, scene, tags)`); geometry lives in `lmgc90_core.scenes`. A load-time assertion checks `SCENE_BUILDERS[id] is spec.scene`. Loading goes through `MainWindow._load_example`:

- **Replace**: `new_project(id, dim)` then `apply_scene(scene)`.
- **Add**: same dimension required; `apply_scene(scene, on_conflict="merge")`, history kept.

---

## 6. Data flows

### 6.1 Creating an avatar

```
AvatarTab._on_add()
  → pre.rigidDisk(...)                         # pure entity
  → controller.add_avatar(av) → controller.add(av)
      → Project.add(av) → _check_avatar (model/material exist, validate_avatar)
      → _run(AddAvatar) → CommandHistory.do → Project._insert_avatar
      → session.mark_dirty()
      → state_changed.emit()
  → all tabs / tree / history re-read from controller.project
```

### 6.2 Granulometric deposit

```
GranuloTab._on_deposit()
  → GranuloConfig(...)
  ├─ “distribution only”     → controller.deposit → Project.deposit (radii in config.radii)
  ├─ “pylmgc” checkbox       → controller.run_granulo_pylmgc → session.run_granulo
  │                              → engine.deposit_population → project.add(population)
  └─ default                 → controller.deposit
                                 ├─ pylmgc available → session.run_granulo (numpy fallback on failure)
                                 └─ otherwise        → Project.deposit → NumpyGranulo
```

### 6.3 Save / load

```
save_project(path)
  → io.save_project: project_to_dict → JSON (.lmgc90)
  → save_populations_sidecar(project.populations) → <name>.populations.npz
  → data["particle_populations_sidecar"] = "<name>.populations.npz"

load_project(path)
  → io.load_project: validates schema, migrates v1→v2
  → merges JSON meta + .npz arrays → ParticlePopulation
  → rebuilds entity lists (Project(record=False)), restores history stacks
```

Unlike the old version, there is **no** “reconstruction of pylmgc90 objects on load”: materialisation is lazy (`session.materialize()` at DATBOX / `visuAvatars` time).

### 6.4 Computation

```
ComputeTab (dt, solver, I/O) + ChipyRoutinesDialog (routines, extraction, steering)
  → get_parameters() → controller.prepare_run_directory / emit_chipy_script
       → pre.py + command.py (+ DATBOX if pylmgc available and auto_write_datbox)
  → create_compute_worker → subprocess “python command.py” (cwd = directory)
  → lines → computation log + application journal
```

---

## 7. Key systems

### 7.1 Identity

An `Avatar` keeps the same `avatar_id` for its whole life; groups, DOF (`target_value`), `Loop.model_avatar_id`, post-processing refer to it. An SoA particle has a **derived** id `"{population_id}:{i}"` (never stored).

Documented exception: in `safe_eval`, `avatar[i]` is positional (writing convenience in forms).

### 7.2 Dynamic variables

`project.dynamic_vars`: name → expression (or number). Evaluated **in insertion order** by `resolve_dynamic_vars`; an unevaluable expression remains a string. Persisted in the `.lmgc90`. SoA populations are **not** exposed in `avatar[...]` / `group[...]`.

### 7.3 History (undo/redo)

`Project.history` saves its stacks in the `.lmgc90` (`history` key) and a readable `journal`. The *History* dock shows each command’s `describe()`.

### 7.4 Preferences

`Preferences` (dataclass): chipy parameters (`dt`, `nb_steps`, `theta`, `tol`, …), environment (`python_executable`, `work_directory`, `projects_directory`, `auto_write_datbox`, `confirm_run`), autosave, recents, performance (`show_avatars_in_tree`, `max_tree_avatars`, …), viewer. `chipy_params()` feeds `emit_chipy_script`.

### 7.5 Name conflicts (`on_conflict`)

`error` (default) · `skip` (reuse existing material/model/law, ignore duplicate see-tables/post-pro) · `merge` (same + group union). Used by “Add to project” for examples.

---

## 8. Project lifecycle

```
1. File → New              controller.new_project(name, dimension)  → new Project + EngineSession
2. Configuration           tabs → controller.add_* (undoable)
3. Save                    Ctrl+S → .lmgc90 (+ .populations.npz)
4. Scripts / DATBOX        Computation → Generate DATBOX / scripts (Ctrl+F5)
                           Tools → Generate pre.py / command.py / Export all
5. Computation             F5 → Compute tab → chipy subprocess
6. Reload                  File → Open → io.load_project
```

---

## 9. Conventions and patterns

| Element | Convention | Example |
|---|---|---|
| Classes | PascalCase | `ProjectController`, `ParticlePopulation` |
| Qt factories | `create_*_tab/dialog/wizard` | `create_material_tab()` |
| Qt slots | `_on_` prefix | `_on_add` |
| Core entities | no Qt/pylmgc state | `Material`, `Avatar` |
| LMGC90 names | ≤ 5 characters (material, model, law, colour, shape) | `STEEL`, `rigid`, `BLUEx` |
| Heavy imports | local (inside functions) | `from PyQt6...` in `create_*` |

View-side error handling: `try/except (ValidationError, ValueError)` → `QMessageBox.warning`. The controller re-raises after emitting `error_occurred`.

---

## 10. Contribution guide

### Add an avatar type

1. `types.py`: `AvatarType` value, and add to `RIGID_AVATARS_2D/3D` if rigid; compatible contactors if needed.
2. `entities.py` / `pre.py`: fields and factory.
3. `validate.py`: consistency rules.
4. `avatar_factory.py`: `build_avatar` branch.
5. `field_forms.py` + `AvatarTab`: form fields.
6. Tests.

### Add a contact law

1. `types.py`: `ContactLawType` + `CONTACT_LAW_PROPERTY_SCHEMA`.
2. `validate.py` / `ContactTab`.
3. Engine materialisation if special kwargs.

### Add a material type / option

1. `MATERIAL_PROPERTY_SCHEMA` / choices.
2. `validate_material`, `MaterialTab`.
3. `materialize._make_material` aliases if needed.

### Add a tab

1. `create_xxx_tab` in `views/tabs/`.
2. Register in `main_window` `all_tabs`.
3. Wire `state_changed` and controller calls.

### Add a dialog / wizard

`dialogs/` + menu entry in `main_window`.

### Add a preference

`Preferences` dataclass + preferences dialog + persistence key.

### Add an example

1. Scene builder in `lmgc90_core/scenes/`.
2. `ExampleSpec` in `lmgc90_gui/examples/`.
3. Ensure `SCENE_BUILDERS[id] is spec.scene`.

### Add a mass generator (SoA)

See [Particle populations](particle_population.md) §B.7 and the checklist below.

**Contributor checklist (SoA)**

- [ ] Creation only via `ParticlePopulation.create`
- [ ] Insertion via `Project.add(pop)` / `Project.deposit` (undoable command)
- [ ] `population_groups` updated (done by `_insert_population`)
- [ ] Sidecar: nothing to do if going through `Project.save`
- [ ] `pre_script`, `avatar_factory`, `viewer_3d` handle the new type
- [ ] Tests: `create`, `to_dict/from_dict`, `to_meta_dict` + sidecar round-trip, deterministic deposit (`seed`)

---

## 11. Tests

- **`lmgc90_core/tests`**: purity, entities, validation, Project/commands, granulo, population, io, scripts.
- **`lmgc90_engine/tests`**: purity, material properties, materialize (if pylmgc available).
- **`lmgc90_gui/tests`**: headless controller, safe_eval, preferences.

Run with `pytest` from each package or the monorepo root according to the project layout.

---

## 12. Known attention points

- **Persistence of generated avatars**: only avatars with `origin == manual` are written to JSON. Avatars from `apply_loop`, `apply_for_loop` or **masonry** (`expand_masonry` sets `origin=FACTORY`) are therefore not reloaded on open, while groups that reference them are. `for_loops` are not written to JSON.
- **Non-uniform undo**: `apply_for_loop`, `apply_masonry`, `deposit` (via `_insert_population`), as well as controller `remove_material/model/law/visibility/dof/postpro/population` and `update_*`, modify the `Project` without a `Command`. The test `test_deposit_is_soa_and_one_undo` nevertheless expects a single undo of the deposit.
- **Groups and DOF in `pre.py`**: `_emit_dof` for a `group` target only applies the operation to the first member (comment “apply to each member”). The engine (`_apply_dof`) does loop over all members.
- **Population groups**: `EngineSession.run_granulo` also adds the `population_id` into `avatar_groups` (duplicate with `population_groups`). `compute_script._resolve_group_ids` only resolves AoS avatars (index + 1) and does not handle populations.
- **Population emission**: `pre_script._emit_population` only knows disk, sphere, discrete disk, cluster, cylinder; polygon/polyhedron fall back to `rigidDisk`.
- **Viewer**: `_render_via_pylmgc90` still imports `...core.pylmgc_bridge` (old architecture); the “🔬” mode must be ported to `EngineSession`.
- **Population loading**: a missing or incomplete sidecar silently ignores the related populations (no more `load_warnings`).
- **Not ported**: Particle Factory, script converter, Project/Granulometry wizards, Templates/Library tab.

---

## Annex — File to change by need

| Need | File |
|---|---|
| New data type / enum | `lmgc90_core/types.py`, `entities.py` |
| Validation rule | `lmgc90_core/validate.py` |
| New undoable action | `lmgc90_core/commands.py` + `Project` |
| Save format | `lmgc90_core/io.py` |
| `pre.py` content | `lmgc90_core/pre_script.py` |
| `command.py` content | `lmgc90_core/compute_script.py` |
| pylmgc90 call | `lmgc90_engine/avatar_factory.py`, `materialize.py` |
| DATBOX | `lmgc90_engine/datbox.py` |
| Shared GUI logic | `lmgc90_gui/controller/project_controller.py` |
| One tab | `lmgc90_gui/views/tabs/<name>_tab.py` |
| 3D view | `lmgc90_gui/views/viewer_3d.py` |
| Expression evaluation | `lmgc90_gui/utils/safe_eval.py`, `eval_context.py` |
