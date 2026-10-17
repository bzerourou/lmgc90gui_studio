# Particle populations (SoA) and granulometry

A **particle population** (`ParticlePopulation`) is how LMGC90_GUI Studio stores **a large number of identical grains** (same type, same material, same model, same colour): instead of one avatar per grain, the project keeps two arrays (positions, radii). That is what makes tens of thousands of grains manageable without slowing the interface.

- **Part A — User**: create, check, visualise, save and delete a population; link grains to contact; troubleshooting.
- **Part B — Developer**: data model, generation, persistence, consumers, extension.

> **Changes vs the old version**
> - SoA is no longer a **checkbox**: a deposit **always** creates a population (except “Distribution only”).
> - The step-by-step granulometry wizard and the “numpy beta” dialog no longer exist: everything goes through the **Granulo** tab (`Ctrl+6`).
> - Default generation is a **random non-overlapping draw** (numpy), not a gravity deposit; the physical `pre.depositIn*` deposit is only used if pylmgc90 is available (see §A.4).
> - Avatar loops (**Loops**, **ForLoop** target `avatar`) remain individual avatars: they do not create a population.

---

# Part A — User

## A.1 Population or individual avatars?

| Need | Tool | Result |
|---|---|---|
| Hundreds to hundreds of thousands of same-type grains | **Granulo** | 1 population |
| A few bodies to edit one by one (walls, parts, varied shapes) | **Avatars**, **Loops**, **ForLoop (avatar)**, **Masonry** | 1 avatar per body |
| Composite bodies, meshes | **Avatars (emptyAvatar)** + **Contactors**, **Deformable** | avatars |

What you **can** do with a population: visualise it, link it to contact laws (by **colour** and **shape**), save it, export to `pre.py` / DATBOX, delete it as a block.

What you **cannot** do: edit an isolated grain, move it, delete it alone, target it alone with a DOF operation, or use it in `avatar[i]` / `group['name']` expressions. To change anything, delete the population and recreate it.

## A.2 Prerequisites

1. A **material** (type `RIGID`, density e.g. 2500) — *Materials* tab.
2. A **rigid model** of the project dimension (`MECAx` / `Rxx2D` or `Rxx3D`) — *Models* tab.
3. Ideally, confining **walls** and a **floor** already in place (or added right after generation) with contact laws and visibility tables.

## A.3 The Granulo tab form

Open **Tabs → Open → Granulo** (`Ctrl+6`).

| Field | Detail | Default |
|---|---|---|
| **N particles** | from 1 to 500 000 | `200` |
| **Min / max radius** | 10⁻⁶ to 10³; **min must be strictly less than max** | `0.05` / `0.15` |
| **Container** | list filtered by project dimension (table below) | first in list |
| *Container parameters* | fields that change with the container | see table |
| **Avatar type** | 2D: `rigidDisk`, `rigidDiscreteDisk`, `rigidPolygon`; 3D: `rigidSphere`, `rigidPolyhedron` | first in list |
| **Material** | all project materials | — |
| **Model** | models of the **same dimension** as the project | — |
| **Colour (5 char.)** | padded with `x` if shorter (e.g. `BLU` → `BLUxx`), truncated to 5 | `BLUEx` |
| **Group (5 char.)** | same | `granx` |
| **Seed** | integer ≥ 0, or `random` (minimum field value) | `42` |
| **Use pylmgc deposit (engine)** | see §A.4 | unchecked |
| **Distribution only (radii)** | creates neither avatars nor a population | unchecked |

> **Types `rigidPolygon` / `rigidPolyhedron`.** They appear in the list but the form cannot yet fill their parameters (vertex count): the deposit is then refused with a message like *“rigidPolygon: extra_params['nb_vertices'] …”*. For now use `rigidDisk`, `rigidDiscreteDisk` or `rigidSphere`.

### Containers

| Dim. | Container | Parameters (default) | Deposit zone |
|---|---|---|---|
| 2D | **Box2D** | `lx=1`, `ly=1` | rectangle `[0, lx] × [0, ly]` |
| 2D | **Disk2D** | `r=1` | disk of radius `r` centred at `(0, 0)` |
| 2D | **Drum2D** | `r=1` | same as Disk2D (drum) |
| 2D | **Couette2D** | `rint=0.5`, `rext=1` | ring between `rint` and `rext`, centred at `(0, 0)` |
| 3D | **Box3D** | `lx=ly=lz=1` | box `[0, lx] × [0, ly] × [0, lz]` |
| 3D | **Sphere3D** | `r=1` | sphere centred at `(0, 0, 0)` |
| 3D | **Cylinder3D** | `r=1`, `lz=2` | cylinder along Z, base at `z=0`, centred at `x=y=0` |

Grains are placed **entirely inside** the container (radius is taken into account). The container is a **sampling zone**, not a body: it creates no wall. Place your walls and floor accordingly (they must surround the indicated zone, hence wall coordinates like `x = −thickness` and `x = lx + thickness` in the examples).

A container of a different dimension than the project is refused (*“Container Box3D is 3D, project is 2D”*).

## A.4 Choose the generation mode

Four possible behaviours:

| Mode | How | Particulars |
|---|---|---|
| **Numpy (default without pylmgc90)** | boxes unchecked, pylmgc90 absent | **random non-overlapping draw**; reproducible with `Seed`; no gravity |
| **pylmgc90 (if installed)** | automatic, **even with box unchecked** | uses `pre.depositInBox2D/3D`, `…Drum2D`, `…Couette2D`, `…Sphere3D`, `…Cylinder3D`; on failure, silent fallback to numpy (message in journal `F7`) |
| **Forced pylmgc90** | **Use pylmgc deposit (engine)** checked | no fallback: if pylmgc90 is missing or fails, an error message is shown |
| **Distribution only** | **Distribution only (radii)** | draws N radii in `[rmin, rmax]`, stores the intent (`[dist]` in the list); **no** grain, no population; the pylmgc box is then disabled |

> Positions from numpy and from pylmgc90 differ (different algorithms). For comparable studies, keep the same mode and the same seed.

## A.5 Generate, check, delete

1. Check material, model, radii, container, colour and group.
2. **Generate deposit**.
3. A message shows: *“Population pop_xxx… — N particles (Container)”*. **N is the number actually placed**, which may be less than requested (§A.6).
4. The top list shows the population: `[SoA] xxxxxxxx…  N=…  <type>  <group>`. Distribution-only entries appear as `[dist] N=… r∈[…,…] → … radii (Container)`.
5. **Delete selection** removes the selected population as a block (and its deposit intent). This deletion is not undoable with `Ctrl+Z`. `[dist]` rows cannot be deleted from this list.
6. In **3D Visualisation**, click **Refresh scene** to display the grains.
7. The status bar shows `bodies=` = avatars + grains.
8. The **Model tree** lists the population (short id, grain count, type).

## A.6 How many grains will actually be placed?

The numpy draw tries candidates in batches and stops after **25 × N** attempts: if the container is too small or too full, there are fewer grains than requested (no error is raised).

Orders of magnitude (random packing without gravity):

| Dimension | Reasonably attainable surface/volume fraction |
|---|---|
| 2D (disks) | about 40 to 50 % |
| 3D (spheres) | about 25 to 35 % |

Quick 2D estimate: `N × π × r_mean² ÷ (lx × ly)` should stay under ≈ 0.4. For denser packings, use wider polydispersity (`rmax/rmin ≥ 2`), a larger container, or the pylmgc90 (gravity) deposit then a compaction computation.

**Volumes:** the numpy deposit compares each batch to already placed grains; cost grows quickly with N. For several tens of thousands of grains, expect significant time and memory (or prefer pylmgc90, or several medium-sized deposits).

## A.7 Several deposits

Each deposit is **independent**: no overlap check between populations. Two deposits in the same container (same zone) will produce overlapping grains. For side-by-side populations, use containers with disjoint zones (e.g. one `Box2D` for one, a `Disk2D` or another geometry for the other) or move walls accordingly. Give **different colours** to each population if they need different contact laws.

## A.8 Reproducibility

- Same seed + same parameters + same mode ⇒ same radii and positions (numpy mode).
- `random` (minimum Seed field value) = random seed: each run differs.
- Positions are stored in the project: reopening a project **does not redeposit** the grains.

## A.9 Link the population to contact

Grains are rigid bodies `RBDY2`/`RBDY3` with a `DISKx` (2D) or `SPHER` (3D) contactor of the population **colour**.

1. **Contact**: create a law (e.g. `IQS_CLB`, friction 0.3–0.5).
2. **Visibility**: **⚡ Grains↔grains** (grain/grain) and **⚡ Grains↔ground** (grain/wall `JONCx`). The tab automatically offers the population colour and contactor. Check the law and **Alert**, then add.
3. **Walls**: `smoothWall` / `roughWall` (contactor `JONCx`) or `rigidPlan` (3D, `PLANx`), colour different from the grains, and **fixed** by `imposeDrivenDof` (`component=[1, 2, 3]`, `dofty='vlocy'`, `ct=0.0`).
4. **Compute**: suitable detectors (`DKDKx` + `DKJCx` in 2D; `SPSPx` + `SPPLx`… in 3D).
5. Visibility **⚠ Check** button to spot a population colour without a table.

Reminders:
- A **population group** (form *Group* field) is not, in the current version, a target offered by the **DOF** and **Post-pro** tabs (they list avatar groups).
- A DOF operation cannot target an isolated grain.
- The DOF “color” target is not applied when the engine writes DATBOX directly (check the exported `pre.py` if you rely on it).

## A.10 `ForLoop` and populations

In **ForLoop**, two targets use deposits:

| Target | Effect |
|---|---|
| `granulo` | one **population** per iteration |
| `granulo_dist` | one **radius distribution** per iteration (no grain) |

Each iteration: seed = rounded value of the variable; `expr N`, `expr rmin`, `expr rmax` (ForLoop fields) replace particle count and radii. All other parameters (container, material, model, type, colour) are taken from the **first deposit already in the project**, or from defaults (first material/model, `Box2D` 1×1 in 2D or `Box3D` 1×1×1 in 3D). Iterations are independent: see §A.7 for overlaps.

## A.11 Save, export, performance

### Files

| File | Content |
|---|---|
| `my_project.lmgc90` | JSON: population metadata (id, type, material, model, colour, origin, dimension, group, `n_particles`), deposit intent (`granulo_generations`) |
| `my_project.populations.npz` | compressed `centers` and `radii` arrays of all populations |

**Copy, move or archive both files together.** If the `.npz` is missing on open, the related populations are ignored without a message: the project opens without grains. If the project no longer has any population, the old `.npz` is deleted on save.

Typical array weight: `(dimension + 1) × 8` bytes per grain before compression, i.e. 24 bytes in 2D (≈ 2.4 MB for 100 000 grains).

### Exports

- **`pre.py`**: each population becomes a loop that recreates bodies from numpy arrays **written in clear text** in the file. For very large populations the file is bulky; writing DATBOX directly (Computation → Generate DATBOX, pylmgc90 required) avoids that step.
- **`command.py`**: identical with or without population (grains are bodies like any other in DATBOX).

### Performance

- 3D viewer: rendering turns each grain into a temporary object then merges disks/spheres by same-colour batches. Manageable up to a few tens of thousands of grains; beyond that, refresh becomes slow (the viewer is a check aid).
- Grains of the same colour are drawn as a **single** object: they are not individually selectable in *Select* mode.
- Creating pylmgc90 bodies: one call per grain (LMGC90 limit), so time proportional to N when writing DATBOX.

## A.12 Provided examples

| Example (Examples → Library) | Deposit |
|---|---|
| Granulometric deposit | 500 disks, `Box2D` 4 × 4, radii 0.03–0.08, seed 42 |
| Rotating drum | 200 disks, `Drum2D` `r=2.0`, radii 0.05–0.09 |
| Hopper discharge | 180 disks, `Box2D` 2 × 1.6, radii 0.04–0.07 |
| Avalanche on slope | 200 disks, `Box2D` 1.5 × 1.0 |
| Biaxial compression | 200 disks, `Box2D` 2 × 1.5 |
| Couette cell | 250 disks, `Couette2D` `rint=1`, `rext=2` |
| 3D cylinder (deposit) | 1000 spheres, `Cylinder3D` `R=7.5`, `lz=10` |
| Drum/granular bed… | see the catalogue |

Load one with **Replace**, then use **Refresh scene**. Grains are deposited automatically when the example loads.

## A.13 Troubleshooting

| Symptom | Cause / solution |
|---|---|
| *rmin must be < rmax* | min radius ≥ max radius |
| *Material and model required* | create a material and a model of the project dimension |
| *Container … is 2D/3D, project is …* | choose a container of the right dimension (or change project dimension) |
| Population smaller than requested | container too full (§A.6) |
| Error at `rigidPolygon` / `rigidPolyhedron` | vertex parameters not fillable in the form (§A.3) |
| *pylmgc90 is required…* | pylmgc box forced without pylmgc90: uncheck it |
| Nothing appears in 3D | click **Refresh scene**; check the population exists in the list |
| Grains go through the floor | no law/visibility for grain colour; floor not fixed; detector not enabled |
| Overlapping grains after two deposits | independent deposits in the same zone (§A.7) |
| Population gone on reopen | `.populations.npz` file missing or renamed |
| Cannot delete a `[dist]` row | not supported from this list |
| Ctrl+Z does not undo the deposit | deposit removal/undo is via **Delete selection** |

---

# Part B — Developer

> Code: `lmgc90_core/population.py`, `io.py`, `generate.py`, `project.py`, `commands.py`, `pre_script.py` · `lmgc90_engine/granulo.py`, `avatar_factory.py`, `materialize.py` · `lmgc90_gui/views/tabs/granulo_tab.py`, `for_loop_tab.py`, `controller/project_controller.py`.

## B.1 AoS vs SoA

| Criterion | AoS — `Avatar` | SoA — `ParticlePopulation` |
|---|---|---|
| Storage | one object per body in `project.avatars` | 2 contiguous arrays + meta in `project.populations` |
| Identity | stored `avatar_id` | stored `population_id`; derived particle id `"{pop_id}:{i}"` |
| Creation | `Project.add` (one command per avatar), loops, masonry | `Project.deposit` / engine `run_granulo` |
| Individual edit | native | no (block) |
| Types | all | `types.POPULATION_TYPES` |
| Serialisation | JSON (avatars `origin == manual`) | JSON meta + `.npz` sidecar |
| `pre.py` | one line per avatar | one loop per population |
| `safe_eval` | `avatar[i]`, `group[...]` | not exposed |

```
Project
├── avatars:           list[Avatar]
├── populations:       list[ParticlePopulation]
├── population_groups: dict[str, list[population_id]]
└── granulo:           list[GranuloConfig]     # deposit intents
```

## B.2 Data model

```python
@dataclass
class ParticlePopulation:
    population_id: str          # "pop_<uuid>"
    avatar_type: AvatarType     # homogeneous
    material_name: str
    model_name: str
    color: str
    origin: AvatarOrigin
    dimension: int              # = centers.shape[1]
    centers: np.ndarray         # (N, dim) float64
    radii: np.ndarray           # (N,)     float64
    group_name: Optional[str] = None
    extra_params: dict = {}
```

`POPULATION_TYPES`: `RIGID_DISK`, `RIGID_SPHERE`, `RIGID_DISCRETE`, `RIGID_CLUSTER`, `RIGID_CYLINDER`, `RIGID_POLYGON`, `RIGID_POLYHEDRON`.

Required `extra_params` (`_validate_extra`):

| Type | Key |
|---|---|
| `rigidCluster` | `nb_disk` (int ≥ 2, default 3) |
| `rigidCylinder` | `h` > 0 (mandatory) |
| `rigidPolygon` | `nb_vertices` (int ≥ 3) |
| `rigidPolyhedron` | `nb_vertices` (int ≥ 4) |

> `GranuloTab` and `NumpyGranulo.deposit` do not feed `extra_params`; polygons/polyhedra therefore fail at `create()` (see A.3).

### Validated construction

```python
ParticlePopulation.create(
    avatar_type="rigidDisk", material_name="TDURx", model_name="rigid",
    centers=centers, radii=radii, color="BLUEx", origin="granulo",
    group_name="depot", population_id=None, extra_params=None,
)
```

`ValueError` if: unsupported type, `centers` ≠ `(N, 2|3)`, `radii` ≠ `(N,)`, different lengths, a radius ≤ 0, invalid `extra_params`.

### Identity and views

```python
pop.particle_avatar_id(i)     # "pop_xxx:42"
parse_particle_id("pop_xxx:42")  # ("pop_xxx", 42)   (ids.py)
pop.as_avatar_view(i)         # ONE temporary Avatar (derived id)
pop.bounds(); pop.radius_stats(); len(pop)
```

`as_avatar_view` must not be called in a loop except in assumed cases (viewer).

## B.3 Generation

### Core: `NumpyGranulo` (`generate.py`)

```python
NumpyGranulo().deposit(config) -> GranuloResult(population, nb_requested, nb_placed, attempts)
```

- `rng = np.random.default_rng(config.seed)`; batches of `min(512, 4 × remaining)` candidates; uniform radii in `[radius_min, radius_max]`;
- `_inside` filter (container, radius included), then `_no_hit_batch` against all already placed particles, then sequential `_no_hit_one`;
- cap `max_attempts = N × 25`; object created with `ParticlePopulation.create(...)`, `origin=GRANULO`, `config.population_id` set;
- cost: dense comparison `(batch × placed)` ⇒ high memory/time for very large N.

Containers: `Box2D` (`[0,lx]×[0,ly]`), `Disk2D`/`Drum2D` (`r`), `Couette2D` (`rint`,`rext`), `Box3D`, `Sphere3D`, `Cylinder3D` (`r`/`R`, `lz`).

### `Project.deposit(config)`

```python
if not config.create_avatars:       # distribution only
    radii = rng.uniform(rmin, rmax, N) ; config.radii = [...] ; self.granulo.append(config) ; return None
result = NumpyGranulo().deposit(config)
self._insert_population(result.population, config)   # (see dev.md §12 for history)
return result.population
```

`_insert_population` adds the population, attaches `config` to `project.granulo` (with `population_id`) and fills `population_groups[group_name]`.

### Engine (`lmgc90_engine/granulo.py`)

`deposit_population(config, ...)`: draws radii (`default_rng(seed)`), calls `pre.depositInBox2D(radii, lx, ly)`, `depositInBox3D`, `depositInDrum2D`/`Disk2D`, `depositInCouette2D`, `depositInSphere3D`, `depositInCylinder3D`, normalises coordinates (`_normalize_coords`, `_parse_result`) and returns a population. `EngineSession.run_granulo(config)` wraps this path.

### Controller

```python
controller.deposit(config)                    # Project.deposit or engine path
controller.run_granulo_pylmgc(config)         # forced, no fallback
controller.remove_population(pid)             # direct _drop_population
```

### `ForLoop` (`Project.apply_for_loop`)

Targets `granulo` / `granulo_dist`: base = `self.granulo[0]` (or defaults); `expressions`: `nb_particles`|`n`, `radius_min`|`rmin`, `radius_max`|`rmax` (evaluated by `_safe_arith`); `seed=int(round(i))`; `group_name = for_loop.group_name`; `create_avatars = (kind == "granulo")`; each iteration calls `self.deposit(cfg)`.

## B.4 Persistence (`io.py`)

```python
sidecar_path_for("p.lmgc90")            # p.populations.npz
save_populations_sidecar(pops, npz)     # keys "<pid>__centers", "<pid>__radii"; empty ⇒ delete old .npz
load_populations_sidecar(npz)           # {pid: (centers, radii)}; missing ⇒ {}
```

- `project_to_dict` writes `particle_populations` (meta via `to_meta_dict()`), `populations_groups`, `granulo_generations` (including `radii` for distribution-only) and, if populations exist, `particle_populations_sidecar`.
- `load_project` merges meta + arrays; a population whose arrays are missing is ignored (no warning). Histories are restored by `load_stacks`.
- Forms: `to_meta_dict()` / `from_meta_and_arrays()` (production), `to_dict()` / `from_dict()` (standalone).

## B.5 Consumers

| Consumer | Behaviour |
|---|---|
| `pre_script._emit_population` | `centers_<id>` / `radii_<id>` in clear text + loop `pre.<fn>(r=…, center=…, model=…, material=…, color=…)`; `fn` ∈ {`rigidDisk`, `rigidSphere`, `rigidDiscreteDisk`, `rigidCluster`, `rigidCylinder`} (other types ⇒ `rigidDisk`) |
| `engine.materialize` | `build_population_bodies` (one `pre.<fn>` call per particle); `scene.bodies_by_population_id[pid]`; `session.population_map`; populations added after AoS avatars |
| `viewer_3d` | `_expand_renderables`: `as_avatar_view(i)` for each particle; merge by `(type, colour)` for disk/sphere; merged actor not pickable |
| `scene_geometry` | subsample to `max_population_preview = 5000` |
| `visibility_tab` | `_project_contact_options` adds `(body, shape, colour, role)` from `pop.avatar_type`, `pop.dimension`, `pop.color` |
| `dof_tab` | lists population colours; groups = `avatar_groups` |
| `compute_script` | indifferent; `_resolve_group_ids` only resolves AoS avatars |
| `eval_context` | `avatar[i]`, `group[...]`: AoS only |

## B.6 History

`AddPopulation(population, config)` is the add command (`revert` ⇒ `_drop_population`). `Project.add(ParticlePopulation)` uses it. Check in current code whether `Project.deposit` goes through `_run(AddPopulation)` (test `test_deposit_is_soa_and_one_undo` expects it; the read implementation calls `_insert_population` directly). See [dev.md §12](dev.md#12-points-de-vigilance-connus).

## B.7 Extend

**New SoA type**: `types.POPULATION_TYPES` → `population._validate_extra` (+ `as_avatar_view`) → `avatar_factory.build_population_bodies` (`fn_map`) → `pre_script._emit_population` (`fn`) → GUI (`GranuloTab`: fields for `extra_params`) → tests.

**Fix polygon/polyhedron in GUI**: add `nb_vertices`/`radius` fields in `GranuloTab` and pass them to `GranuloConfig` (`extra_params` to introduce in the model), then to `NumpyGranulo.deposit` → `ParticlePopulation.create(extra_params=…)`.

**New container**: `NumpyGranulo._sample` + `_inside`, `granulo_tab._CONTAINERS`, optionally `engine.granulo._call_deposit`.

**Checklist**
- [ ] creation via `ParticlePopulation.create`
- [ ] insertion via `Project.add(pop)` or `deposit` (ideally undoable command)
- [ ] `population_groups` filled
- [ ] `pre.py` emission and materialisation handle the type
- [ ] viewer and 2D preview handle the type
- [ ] tests: `create`, `to_dict/from_dict`, `to_meta_dict` + sidecar round-trip, deterministic deposit (`seed`)

## B.8 Related files

| File | Role |
|---|---|
| `lmgc90_core/population.py` | SoA dataclass, validation, views, serialisation |
| `lmgc90_core/io.py` | `.npz` sidecar, save/load |
| `lmgc90_core/generate.py` | `NumpyGranulo`, `GranuloResult` |
| `lmgc90_core/project.py`, `commands.py` | `deposit`, `AddPopulation`, `_insert/_drop_population`, `apply_for_loop` |
| `lmgc90_core/pre_script.py` | `_emit_population` |
| `lmgc90_core/scenes/demos.py` | scenes with `GranuloConfig` |
| `lmgc90_engine/granulo.py` | pylmgc90 deposit |
| `lmgc90_engine/avatar_factory.py`, `materialize.py` | pylmgc90 bodies |
| `lmgc90_gui/views/tabs/granulo_tab.py`, `for_loop_tab.py` | forms |
| `lmgc90_gui/controller/project_controller.py` | `deposit`, `run_granulo_pylmgc`, `remove_population`, `apply_scene` |
