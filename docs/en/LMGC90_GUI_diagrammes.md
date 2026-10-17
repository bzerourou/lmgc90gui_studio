# LMGC90 Studio — Detailed architecture

> **Version:** 0.6.0  > **Author:** bzerourou  > **class diagrams** and **sequence diagrams** for the **core / engine / gui** architecture.
---

## Table of contents

1. [Overview](#1-overview)
2. [Class diagram — core](#2-class-diagram--lmgc90_core)
3. [Class diagram — engine](#3-class-diagram--lmgc90_engine)
4. [Class diagram — gui](#4-class-diagram--lmgc90_gui)
5. [Class diagram — cross-cutting](#5-class-diagram--cross-cutting-view)
6. [Sequences — CRUD & history](#6-sequences--crud--history)
7. [Sequences — materialize & DATBOX](#7-sequences--materialize--datbox)
8. [Sequences — granulo](#8-sequences--granulo)
9. [Sequences — multi-target ForLoop](#9-sequences--multi-target-forloop)
10. [Sequences — open project / Undo](#10-sequences--open-project--undo)
11. [Sequences — visu & script export](#11-sequences--visu--script-export)
12. [Architecture rules](#12-architecture-rules)

---

## 1. Overview

```mermaid
flowchart TB
  subgraph GUI["📦 lmgc90_gui"]
    direction TB
    APP[app.main]
    MW[MainWindow]
    PC[ProjectController]
    TABS[Tabs + Dialogs + Viewer3D]
    WRK[Workers subprocess]
    APP --> MW
    MW --> TABS
    MW --> PC
    TABS --> PC
    PC --> WRK
  end

  subgraph ENG["📦 lmgc90_engine"]
    ES[EngineSession]
    MAT[materialize_project]
    AF[avatar_factory]
    GR[granulo depositIn*]
    DB[datbox.write]
    ES --> MAT
    MAT --> AF
    ES --> GR
    ES --> DB
  end

  subgraph CORE["📦 lmgc90_core"]
    PR[Project]
    ENT[entities + types]
    CMD[CommandHistory]
    GEN[generate / masonry / population]
    SCR[pre_script / chipy_script / io]
    PR --> ENT
    PR --> CMD
    PR --> GEN
    PR --> SCR
  end

  PC -->|owns| PR
  PC -->|owns| ES
  ES -->|reads| PR
  MAT -.->|optional| PY[(pylmgc90.pre)]
  AF -.-> PY
  GR -.-> PY
  DB -.-> PY
```

| Package | Role | Dependencies |
|---------|------|-------------|
| **core** | Model truth, Undo, serialisation, scripts | Python + NumPy |
| **engine** | Live materialisation, DATBOX, native deposits | core + optional pylmgc90 |
| **gui** | MVC interface | core + engine + PyQt6 (+ PyVista) |

---

## 2. Class diagram — `lmgc90_core`

### 2.1 Project and aggregates

```mermaid
classDiagram
  direction TB

  class Project {
    +str name
    +int dimension
    +UnitSystem units
    +list~Material~ materials
    +list~Model~ models
    +list~Avatar~ avatars
    +list~ContactLaw~ contact_laws
    +list~VisibilityRule~ visibility
    +list~DOFOperation~ dof_operations
    +list~PostProCommand~ postpro
    +list~Loop~ loops
    +list~ForLoop~ for_loops
    +list~GranuloConfig~ granulo
    +list~ParticlePopulation~ populations
    +dict avatar_groups
    +dict population_groups
    +dict dynamic_vars
    +CommandHistory history
    +add(entity)
    +remove_avatar(id)
    +deposit(cfg)
    +apply_for_loop(fl)
    +save(path) / load(path)
  }

  class Material {
    +str name
    +MaterialType material_type
    +float density
    +dict properties
  }

  class Model {
    +str name
    +str physics
    +str element
    +int dimension
    +dict options
  }

  class Avatar {
    +str avatar_id
    +AvatarType avatar_type
    +list center
    +str material_name model_name color
    +AvatarOrigin origin
    +float|None radius
    +dict|None axis wall_params mesh_params
    +list contactors
    +copy() Avatar
  }

  class ContactLaw {
    +str name
    +ContactLawType law_type
    +float|None friction
    +dict properties
  }

  class VisibilityRule {
    +str candidate_body
    +str candidate_contactor
    +str candidate_color
    +str antagonist_body
    +str antagonist_contactor
    +str antagonist_color
    +str behavior_name
    +float alert
  }

  class DOFOperation {
    +str operation_type
    +str target_type
    +str target_value
    +dict parameters
  }

  class PostProCommand {
    +str name
    +int step
    +str target_type
    +str target_value
    +dict parameters
  }

  class Loop {
    +str loop_type
    +int count
    +float step radius offset_*
    +str model_avatar_id
    +str|None group_name
    +list generated_ids
  }

  class ForLoop {
    +str var_name
    +float start stop step
    +str target_kind
    +str model_avatar_id
    +str template_name
    +int template_index
    +str expr_x expr_y expr_z
    +str|None expr_radius
    +dict expressions
    +str|None group_name
    +list generated_ids
  }

  class GranuloConfig {
    +int nb_particles
    +float radius_min radius_max
    +str container_type
    +dict container_params
    +str material_name model_name avatar_type color
    +str|None group_name
    +int|None seed
    +str|None population_id
    +int dimension
    +bool create_avatars
    +list|None radii
  }

  class ParticlePopulation {
    +str population_id
    +AvatarType avatar_type
    +str material_name model_name color
    +ndarray centers
    +ndarray radii
    +str|None group_name
    +as_avatar_view(i) Avatar
    +to_meta_dict() dict
  }

  class MasonryConfig {
    +int n_courses n_columns
    +float brick_lx ly lz joint
    +str bond material_name model_name
    +str color group_name brick_name
    +int dimension
  }

  Project "1" *-- "*" Material
  Project "1" *-- "*" Model
  Project "1" *-- "*" Avatar
  Project "1" *-- "*" ContactLaw
  Project "1" *-- "*" VisibilityRule
  Project "1" *-- "*" DOFOperation
  Project "1" *-- "*" PostProCommand
  Project "1" *-- "*" Loop
  Project "1" *-- "*" ForLoop
  Project "1" *-- "*" GranuloConfig
  Project "1" *-- "*" ParticlePopulation
  Project "1" o-- "1" CommandHistory
  Avatar --> Material : material_name
  Avatar --> Model : model_name
  VisibilityRule --> ContactLaw : behavior_name
  GranuloConfig --> ParticlePopulation : population_id
  Loop --> Avatar : template
  ForLoop --> Avatar : template optional
```

### 2.2 Command history (Undo / Redo)

```mermaid
classDiagram
  direction LR

  class Command {
    <<protocol>>
    +apply(project)
    +revert(project)
    +describe() str
    +to_journal() dict
  }

  class CommandHistory {
    +list undo_stack
    +list redo_stack
    +list journal_log
    +push(cmd)
    +undo(project)
    +redo(project)
    +journal() list
  }

  class AddMaterial
  class AddModel
  class AddAvatar
  class RemoveAvatar
  class AddPopulation
  class AddLaw
  class AddSeeTable
  class AddDOF
  class AddPostPro
  class AddLoop
  class SetGroup

  CommandHistory o-- "*" Command : stacks
  Command <|.. AddMaterial
  Command <|.. AddModel
  Command <|.. AddAvatar
  Command <|.. RemoveAvatar
  Command <|.. AddPopulation
  Command <|.. AddLaw
  Command <|.. AddSeeTable
  Command <|.. AddDOF
  Command <|.. AddPostPro
  Command <|.. AddLoop
  Command <|.. SetGroup
```

### 2.3 Types & validation (excerpt)

```mermaid
classDiagram
  class MaterialType {
    <<enumeration>>
    RIGID
    ELAS
    ELAS_DILA
    VISCO_ELAS
    ELAS_PLAS
    THERMO_ELAS
    PORO_ELAS
    DISCRETE
  }

  class AvatarType {
    <<enumeration>>
    RIGID_DISK
    RIGID_JONC
    RIGID_POLYGON
    EMPTY_AVATAR
    MESH_DEFORMABLE
    RIGID_SPHERE
    RIGID_PLAN
    RIGID_CYLINDER
    RIGID_POLYHEDRON
    ...
  }

  class ContactLawType {
    <<enumeration>>
    IQS_CLB
    MAL_CZM
    ELASTIC_WIRE
    COUPLED_DOF
    ...
  }

  Material --> MaterialType
  Avatar --> AvatarType
  ContactLaw --> ContactLawType
```

Related constants: `MATERIAL_PROPERTY_SCHEMA`, `ORTHOTROPIC_FIELDS_2D/3D`, `CONTACTORS_RIGID_2D/3D`, `CONTACT_LAW_PROPERTY_SCHEMA`.

---

## 3. Class diagram — `lmgc90_engine`

```mermaid
classDiagram
  direction TB

  class EngineSession {
    +Project project
    +MaterializedScene|None _scene
    +bool _dirty
    --
    +mark_dirty()
    +materialize(force) MaterializedScene
    +write_datbox(path, ...)
    +visu_avatars(force)
    +emit_pre_script(path) str
    +emit_chipy_script(...) str
    +export_all(outdir)
    +run_granulo(cfg) ParticlePopulation
    +available() bool
  }

  class MaterializedScene {
    +Any materials_container
    +Any models_container
    +Any bodies_container
    +dict material_by_name
    +dict model_by_name
    +dict body_by_avatar_id
    +dict law_by_name
    +int dimension
    +str project_name
  }

  class materialize_project {
    <<function>>
    +materialize_project(project) MaterializedScene
  }

  class avatar_factory {
    <<module>>
    +build_avatar(av, ...)
    +build_population_bodies(pop, ...)
    +_apply_contactors(...)
  }

  class granulo {
    <<module>>
    +deposit_population(config) ParticlePopulation
  }

  class datbox {
    <<module>>
    +write_datbox(scene, path)
    +write_cell_dual_datbox(...)
  }

  EngineSession --> Project : reference
  EngineSession o-- MaterializedScene
  EngineSession ..> materialize_project
  EngineSession ..> granulo
  EngineSession ..> datbox
  materialize_project ..> avatar_factory
  MaterializedScene ..> "pylmgc90.pre" : live containers
```

**Materialize chain (order)**:

1. `pre.materials()` ← each `Material` (`_make_material`, orthotropic → `young`/`nu`/`G` lists)
2. `pre.models()` ← each `Model` (`dimension` ∈ {2,3}, name 5 char.)
3. Bodies ← `build_avatar` / populations / mesh expand
4. `tact_behav` ← laws
5. `see_table` ← visibility
6. DOF ← `imposeDrivenDof` / evolution / …

---

## 4. Class diagram — `lmgc90_gui`

```mermaid
classDiagram
  direction TB

  class MainWindow {
    +ProjectController controller
    +QTabWidget tabs
    +HistoryDock history
    +menus File Project Edit Tools Computation
    +open_tab(name)
    +on_state_changed()
  }

  class ProjectController {
    +Project _project
    +EngineSession _session
    +AppJournal journal
    --
    +add(entity)
    +add_material / add_model / add_avatar
    +remove_avatar(id)
    +update_avatar(id, av)
    +deposit(cfg)
    +run_granulo_pylmgc(cfg)
    +apply_for_loop(fl)
    +apply_masonry(cfg)
    +visu_avatars(force)
    +write_datbox(...)
    +undo() redo()
    +new_project() open() save()
    +pylmgc_available() bool
    +signal state_changed
  }

  class BaseTab {
    <<mixin>>
    +ProjectController|None controller
    +on_state_changed()
    +eval_float(text, default, name)
  }

  class MaterialTab
  class ModelTab
  class AvatarTab
  class ContactorsTab
  class ContactTab
  class VisibilityTab
  class DofTab
  class GranuloTab
  class ForLoopTab
  class GroupsTab
  class ViewerTab

  class EntityTree {
    +set_rows / clear_rows / add_row
    +selected_payload()
    +on_select callback
  }

  class Viewer3D {
    +refresh_from_project(project)
    +_draw_law_links()
    +DOF markers / axes
  }

  class MeshWizard
  class MasonryWizard
  class PreferencesDialog
  class CommandPaletteDialog
  class LinkVisibilityDialog

  class DatboxWorker
  class ComputeWorker

  MainWindow --> ProjectController
  MainWindow --> MaterialTab
  MainWindow --> AvatarTab
  MainWindow --> Viewer3D
  MainWindow --> MeshWizard
  MainWindow --> MasonryWizard
  BaseTab <|-- MaterialTab
  BaseTab <|-- AvatarTab
  BaseTab <|-- GranuloTab
  BaseTab <|-- ForLoopTab
  MaterialTab --> EntityTree
  AvatarTab --> EntityTree
  ProjectController --> Project
  ProjectController --> EngineSession
  ProjectController --> DatboxWorker
  ProjectController --> ComputeWorker
  Viewer3D --> Project : read-only geometry
```

---

## 5. Class diagram — cross-cutting view

```mermaid
classDiagram
  direction LR

  class ProjectController
  class Project
  class EngineSession
  class MaterializedScene
  class MainWindow
  class AvatarTab
  class MaterialTab

  MainWindow --> ProjectController
  AvatarTab --> ProjectController
  MaterialTab --> ProjectController
  ProjectController *-- Project : truth
  ProjectController *-- EngineSession : live session
  EngineSession --> Project : reference
  EngineSession o-- MaterializedScene : after materialize

  note for Project "Serialisable .lmgc90\nNo Qt, no pylmgc"
  note for MaterializedScene "Fortran/Python pre objects\nNot serialised in the project"
```

---

## 6. Sequences — CRUD & history

### 6.1 Adding a material

```mermaid
sequenceDiagram
  actor U as User
  participant MT as MaterialTab
  participant PC as ProjectController
  participant P as Project
  participant H as CommandHistory
  participant UI as Other tabs / tree

  U->>MT: Enter name/type/props → Add
  MT->>MT: _build_material() + validate name ≤5
  MT->>PC: add_material(Material)
  PC->>P: add(Material)
  P->>P: validate_material
  P->>H: push(AddMaterial)
  H->>H: apply → _insert_material
  P-->>PC: Material
  PC->>PC: session.mark_dirty()
  PC->>PC: emit state_changed
  PC-->>MT: refresh
  PC-->>UI: on_state_changed (lists updated)
```

### 6.2 Deleting an avatar

```mermaid
sequenceDiagram
  actor U as User
  participant AT as AvatarTab
  participant PC as ProjectController
  participant P as Project
  participant H as CommandHistory

  U->>AT: Select row + Delete
  AT->>AT: aid = _editing_id or tree.selected_payload()
  alt no id
    AT-->>U: message “select an avatar”
  else id known
    AT->>PC: remove_avatar(aid)
    PC->>P: remove_avatar(aid)
    P->>P: avatar(aid)
    P->>H: push(RemoveAvatar)
    H->>P: _drop_avatar (lists + groups + related DOF)
    PC->>PC: mark_dirty + emit
    AT->>AT: clear form / selection
  end
```

### 6.3 Undo

```mermaid
sequenceDiagram
  actor U as User
  participant MW as MainWindow
  participant PC as ProjectController
  participant P as Project
  participant H as CommandHistory

  U->>MW: Edit → Undo (Ctrl+Z)
  MW->>PC: undo()
  PC->>P: undo()
  P->>H: undo(project)
  H->>H: pop undo_stack → cmd.revert(project)
  H->>H: push redo_stack
  PC->>PC: mark_dirty + emit state_changed
  MW-->>U: tree / history dock refreshed
```

---

## 7. Sequences — materialize & DATBOX

```mermaid
sequenceDiagram
  actor U as User
  participant MW as MainWindow
  participant PC as ProjectController
  participant ES as EngineSession
  participant MAT as materialize_project
  participant AF as avatar_factory
  participant Pre as pylmgc90.pre
  participant DB as datbox

  U->>MW: Generate DATBOX / F5
  MW->>PC: write_datbox(path) or export
  PC->>ES: materialize(force=True)
  ES->>MAT: materialize_project(project)

  loop materials
    MAT->>Pre: pre.material(name, type, density, props…)
  end
  loop models
    MAT->>Pre: pre.model(name, physics, element, dimension)
  end
  loop avatars / populations
    MAT->>AF: build_avatar / build_population_bodies
    AF->>Pre: rigidDisk / emptyAvatar / brick2D? / mesh…
    AF->>Pre: addContactors if needed
  end
  loop laws + see + DOF
    MAT->>Pre: tact_behav / see_table / imposeDrivenDof
  end

  MAT-->>ES: MaterializedScene
  ES-->>PC: scene
  PC->>ES: write_datbox(…)
  ES->>DB: write bodies + bulk + …
  DB->>Pre: writeDatbox / IO macros
  ES-->>PC: OK
  PC-->>U: journal “DATBOX written”
```

### emptyAvatar (detail)

```mermaid
sequenceDiagram
  participant AF as avatar_factory
  participant Pre as pylmgc90.pre

  AF->>AF: wall_params.brick_name + sizes?
  alt explicit masonry brick
    AF->>Pre: brick2D(name, lx, ly).rigidBrick(...)
  else empty composite
    AF->>Pre: emptyAvatar(...) or avatar(dim, model)
    AF->>AF: _apply_contactors(DISKx, JONCx, …)
  end
```

---

## 8. Sequences — granulo

### 8.1 Distribution only (no avatars)

```mermaid
sequenceDiagram
  actor U as User
  participant GT as GranuloTab
  participant PC as ProjectController
  participant P as Project

  U->>GT: check “Distribution only” → Generate
  GT->>PC: deposit(GranuloConfig create_avatars=False)
  PC->>P: deposit(cfg)
  P->>P: sample radii [rmin,rmax] (seed)
  P->>P: granulo.append(cfg)  without population
  P-->>PC: None
  PC-->>GT: message N radii
```

### 8.2 SoA or pylmgc deposit

```mermaid
sequenceDiagram
  actor U as User
  participant GT as GranuloTab
  participant PC as ProjectController
  participant ES as EngineSession
  participant P as Project
  participant NG as NumpyGranulo
  participant Pre as pylmgc90.pre

  U->>GT: Generate deposit (Box2D/Cylinder3D/…)
  alt pylmgc checked and available
    GT->>PC: run_granulo_pylmgc(cfg)
    PC->>ES: run_granulo(cfg)
    ES->>Pre: granulo_Random + depositInXxx
    ES->>P: insert ParticlePopulation
  else numpy SoA
    GT->>PC: deposit(cfg)
    PC->>P: deposit(cfg)
    P->>NG: rejection packing
    NG-->>P: ParticlePopulation
    P->>P: populations + granulo
  end
  PC-->>GT: N particles placed
```

---

## 9. Sequences — multi-target ForLoop

```mermaid
sequenceDiagram
  actor U as User
  participant FT as ForLoopTab
  participant PC as ProjectController
  participant P as Project

  U->>FT: target = material|avatar|dof|visibility|granulo|…
  U->>FT: template + start/stop/step + expressions
  FT->>PC: apply_for_loop(ForLoop)
  PC->>P: apply_for_loop(fl)

  alt target_kind == avatar
    P->>P: expand_for_loop(template, expr_x/y/z)
    P->>P: avatars.append × N
  else material / model
    P->>P: clone template + eval density/name
    P->>P: add(Material|Model) × N
  else dof / visibility
    P->>P: clone op/rule + eval params/alert
  else granulo / granulo_dist
    P->>P: deposit(cfg) per iteration
  end

  P->>P: for_loops.append(fl)
  PC-->>FT: N elements generated
```

---

## 10. Sequences — open project / Undo

```mermaid
sequenceDiagram
  actor U as User
  participant MW as MainWindow
  participant PC as ProjectController
  participant P as Project
  participant ES as EngineSession
  participant Disk as File .lmgc90

  U->>MW: Open…
  MW->>PC: open(path)
  PC->>P: Project.load(path)
  P->>Disk: JSON + .npz populations sidecar
  Disk-->>P: entities + history journal
  PC->>PC: _project = P
  PC->>ES: EngineSession(project)  scene invalidated
  PC->>PC: emit state_changed
  MW-->>U: all tabs reloaded
  Note over ES: materialize only when needed\n(visu / DATBOX)
```

---

## 11. Sequences — visu & script export

### 11.1 Parametric viewer (no mandatory materialize)

```mermaid
sequenceDiagram
  actor U as User
  participant V as Viewer3D
  participant PC as ProjectController
  participant P as Project

  U->>V: Refresh scene
  V->>PC: project
  PC-->>V: Project
  loop each Avatar / population
    V->>V: _mesh_* by AvatarType
    V->>V: DOF markers / law links
  end
  V-->>U: PyVista scene
```

### 11.2 pre.visuAvatars (pylmgc)

```mermaid
sequenceDiagram
  actor U as User
  participant PC as ProjectController
  participant ES as EngineSession
  participant Pre as pylmgc90.pre

  U->>PC: visu_avatars(force=True)
  PC->>ES: materialize(force)
  ES-->>PC: scene
  PC->>ES: visu_avatars()
  ES->>Pre: pre.visuAvatars(bodies, …)
```

### 11.3 Export pre.py (pure core)

```mermaid
sequenceDiagram
  actor U as User
  participant PC as ProjectController
  participant P as Project
  participant SCR as pre_script

  U->>PC: Export pre.py
  PC->>P: to_pre_script()
  P->>SCR: emit materials → models → avatars → laws → see → DOF
  SCR-->>U: executable pre.py file outside GUI
```

---

## 12. Architecture rules

1. **Source of truth** = `lmgc90_core.Project` (never the pylmgc containers).
2. **core**: zero Qt / pylmgc90 imports (headless tests).
3. **engine**: materialises on demand; `mark_dirty` after every GUI mutation.
4. **gui**: `ProjectController` = sole façade; tabs do not touch `pre` directly (except core `pre.*` helpers to build entities).
5. **LMGC90 names** = 5 characters at export / materialize.
6. **emptyAvatar** ≠ brick: brick only if `wall_params.brick_name` + dimensions.
7. **Examples** = `def scene(project) -> None` in core entities, no Fortran scripts in core.

---

*Studio architecture — detailed classes & sequences (core / engine / gui).*
