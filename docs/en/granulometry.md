# Granulometry and particle populations

The **Granulo** tab generates a population of particles whose radii lie between two bounds, and places them in a container. An SoA population can represent many grains without creating an individual graphical row for each particle.

![](../captures/granulo.png)

## Prepare the project

1. Create a material compatible with the grains in **Materials**.
2. Create a rigid model suited to the dimension (`MECAx` with `Rxx2D` or `Rxx3D`) in **Models**.
3. Open **Tabs → Open → Granulo** (`Ctrl+6`).

## Configure the deposit

1. Set **N particles**.
2. Fill in **Min radius** and **Max radius**. The minimum radius must be strictly less than the maximum.
3. Choose the **Container** offered for the project dimension:
   - 2D: `Box2D`, `Disk2D`, `Drum2D`, `Couette2D`;
   - 3D: `Box3D`, `Sphere3D`, `Cylinder3D`.
4. Complete the container dimensions shown under **Container**: `lx`, `ly`, `lz`, `r`, `rint` or `rext` as applicable.
5. Choose the **Avatar type**. In 2D: disk, discrete disk or polygon; in 3D: sphere or polyhedron.
6. Select **Material** and **Model**.
7. Fill in **Color (5 char.)** and **Group (5 char.)**.
8. Set **Seed** to reproduce the draw. The value `random` requests a random seed.

## Choose a generation mode

- **NumPy SoA deposit**: leave **Use pylmgc deposit (engine) if available** unchecked. The application builds a compact population and adds it to the project.
- **pylmgc deposit**: check this option if pylmgc90 is available in the environment and you want to use its deposit routines.
- **Distribution only**: check **Distribution only (radii)** to generate and store radii without producing avatars or a population. In this mode, the pylmgc deposit is disabled.

## Generate and check the result

1. Review the count, radii, container, body type and material/model references.
2. Click **Generate deposit**.
3. Check the confirmation message.
4. The list shows created populations as `[SoA]` with their size, type and group. Distribution-only entries are marked `[dist]`.
5. To remove a population, select it in the list then click **Delete selection**.
6. Open **3D Visualisation** and click **Refresh scene** to see the population.

Deletion applies to a population; check the selected row before confirming.

## Dimension and contact

The container type must match the project dimension. Populations generate their own rigid bodies/colours, but interactions still need compatible contact laws and visibility tables. In **Visibility**, use the colours and contactors suggested from the population; choose the right candidate/antagonist pair and a consistent **Alert** distance.

To repeat a generation with an iteration variable, see [ForLoop](for_loop.md). For the representation of large populations, see [Particle populations](particle_population.md) (technical reference).


# ParticlePopulation — SoA architecture for bulk particles

> Complement to the [developer guide](dev.md). Technical reference (not a graphical how-to).
> Code: `lmgc90_core/population.py`, `lmgc90_core/io.py`, `lmgc90_core/generate.py`, `lmgc90_engine/granulo.py`, `lmgc90_engine/avatar_factory.py`.

---

## 1. Why SoA?

| Approach | Structure | Use case | Practical limit |
|---|---|---|---|
| **AoS** (`project.avatars`) | One `Avatar` object per body | Walls, manual avatars, deformables, unit editing | a few thousand before UI slowdown |
| **SoA** (`project.populations`) | One `ParticlePopulation` = two numpy arrays | Granulometric deposits, large homogeneous volumes | tens to hundreds of thousands of particles |

`ParticlePopulation` **does not replace** `Avatar`: both coexist in `Project`.

```
Project
├── avatars:      list[Avatar]               # AoS — fine editing
└── populations:  list[ParticlePopulation]   # SoA — volumes
    population_groups: dict[name → [population_id]]
```

**Major change vs the old version:** SoA is no longer a checkbox option. `Project.deposit()` **always** produces a population (except “distribution only” mode). There is no longer `particle_populations` in a `ProjectState`, nor `_pylmgc_population_bodies` in the controller.

---

## 2. Data model

```python
@dataclass
class ParticlePopulation:
    population_id: str             # "pop_<uuid>" — one id per population
    avatar_type: AvatarType        # homogeneous
    material_name: str             # homogeneous
    model_name: str                # homogeneous
    color: str                     # homogeneous
    origin: AvatarOrigin           # GRANULO, LOOP, ...
    dimension: int                 # 2 or 3 (= centers.shape[1])
    centers: np.ndarray            # (N, dim) float64
    radii: np.ndarray              # (N,)     float64
    group_name: Optional[str] = None
    extra_params: dict = {}        # nb_disk, h, nb_vertices, ...
```

### 2.1 Supported types

`types.POPULATION_TYPES`: `RIGID_DISK`, `RIGID_SPHERE`, `RIGID_DISCRETE`, `RIGID_CLUSTER`, `RIGID_CYLINDER`, `RIGID_POLYGON`, `RIGID_POLYHEDRON`.

Required `extra_params` by type (validated in `_validate_extra`):

| Type | `extra_params` |
|---|---|
| `rigidCluster` | `nb_disk` integer ≥ 2 (default 3) |
| `rigidCylinder` | `h` > 0 mandatory |
| `rigidPolygon` | `nb_vertices` integer ≥ 3 |
| `rigidPolyhedron` | `nb_vertices` integer ≥ 4 |

### 2.2 Validated construction

Always via `create()`:

```python
pop = ParticlePopulation.create(
    avatar_type="rigidDisk",              # AvatarType or string
    material_name="TDURx", model_name="rigid",
    centers=centers, radii=radii,
    color="BLUEx",
    origin="granulo",
    group_name="depot",
    population_id=None,                   # generated if absent
    extra_params=None,
)
```

`ValueError` cases: unsupported type, `centers` not `(N, 2|3)`, `radii` not `(N,)`, different lengths, radius ≤ 0, invalid `extra_params`.

### 2.3 Particle identity

Derived, never stored (`ids.py`):

```python
pop.particle_avatar_id(i)                   # "pop_abc…:42"
parse_particle_id("pop_abc…:42")            # ("pop_abc…", 42)
```

The `population_id` is stable; index `i` is positional (the population is treated as a block: no individual deletion or reordering).

### 2.4 Point view

```python
av = pop.as_avatar_view(i)    # builds ONE Avatar (avatar_id = derived id)
```

Reserve this for point inspection. **Never** loop over the whole population except in assumed cases (the 3D viewer does; see §6).

### 2.5 Statistics

```python
len(pop); pop.bounds(); pop.radius_stats()   # {"min","max","mean"}
```

---

## 3. Generation

### 3.1 Core: `NumpyGranulo`

`Project.deposit(config)` calls `NumpyGranulo().deposit(config)` (vectorised batch rejection, reproducible `seed`) then inserts the population. Handled containers:

| Dim. | `container_type` | `container_params` |
|---|---|---|
| 2D | `Box2D` | `lx`, `ly` — domain `[0, lx] × [0, ly]` (like `depositInBox2D`) |
| 2D | `Disk2D`, `Drum2D` | `r` |
| 2D | `Couette2D` | `rint`, `rext` |
| 3D | `Box3D` | `lx`, `ly`, `lz` |
| 3D | `Sphere3D` | `r` |
| 3D | `Cylinder3D` | `r` (or `R`), `lz` |

The result (`GranuloResult`) gives `nb_placed`, `nb_requested`, `fill_ratio`. The placed count may be less than requested.

### 3.2 “Distribution only” mode

`GranuloConfig(create_avatars=False)`: draws only `nb_particles` radii in `[radius_min, radius_max]`, stores them in `config.radii` and adds the config to `project.granulo`. No population, no avatar.

### 3.3 pylmgc90 deposit (engine)

`lmgc90_engine.granulo.deposit_population(config)` calls `pre.depositInBox2D/3D`, `depositInDrum2D/Disk2D`, `depositInCouette2D`, `depositInSphere3D`, `depositInCylinder3D` and returns a `ParticlePopulation`. The controller chooses:

```
controller.deposit(config)
  ├─ create_avatars=False → Project.deposit (radii only)
  ├─ pylmgc available     → session.run_granulo (fallback to NumpyGranulo on failure)
  └─ otherwise            → Project.deposit (NumpyGranulo)
```

The **Granulo** tab also exposes an explicit “pylmgc deposit (engine)” checkbox (`run_granulo_pylmgc`).

### 3.4 Scenes and `ForLoop`

- Example scenes declare a `GranuloConfig` in `project.granulo`; `ProjectController.apply_scene` then calls `deposit` for each config without `population_id`.
- `ForLoop` target `granulo` → one population per iteration; target `granulo_dist` → radii distributions only. The `avatar` target of a `ForLoop` remains **AoS** (no SoA path for avatar loops).

---

## 4. Two-level persistence

### 4.1 Sidecar `.npz`

| File | Content |
|---|---|
| `project.lmgc90` (JSON) | `particle_populations`: metadata via `to_meta_dict()` (no arrays, with `n_particles`), `populations_groups`, `granulo_generations`, key `particle_populations_sidecar` |
| `project.populations.npz` | `"<population_id>__centers"` and `"<population_id>__radii"` (compressed) |

```python
from lmgc90_core.io import sidecar_path_for, save_populations_sidecar, load_populations_sidecar

sidecar_path_for(Path("p.lmgc90"))        # → p.populations.npz
save_populations_sidecar(populations, npz_path)
load_populations_sidecar(npz_path)        # {pop_id: (centers, radii)}
```

Rules:
- no population → no `.npz` written; an old sidecar is **deleted**;
- missing sidecar → `load_populations_sidecar` returns `{}`.

### 4.2 Reload

`io.load_project` merges JSON meta + arrays; only populations whose arrays are found are restored (`if pid in arrays`). A population whose array is missing is **silently ignored** (there are no longer `load_warnings`).

### 4.3 Serialisation forms

| Methods | Usage |
|---|---|
| `to_meta_dict()` / `from_meta_and_arrays(meta, centers, radii)` | production (JSON + npz) |
| `to_dict()` / `from_dict(d)` | standalone (arrays as lists) — tests, duplication |

---

## 5. History and undo

`AddPopulation(population, config)` is the add `Command` (one command regardless of size); `revert` calls `_drop_population` (removes population, associated `GranuloConfig` and `population_groups` entries). `Project.add(ParticlePopulation)` goes through this command. See [dev.md §12](dev.md#12-points-de-vigilance-connus) for undo coverage of `Project.deposit` and `controller.remove_population`.

---

## 6. Population consumers

| Consumer | Behaviour |
|---|---|
| **`pre_script.emit_pre`** | per population: `np.array` of centres/radii, then loop `for … pre.rigidXxx(...)` + `bodies.addAvatar`. Emitted functions: disk, sphere, discrete disk, cluster, cylinder (other types fall back to `rigidDisk`). |
| **`engine.materialize`** | `build_population_bodies`: one `pre.<fn>` loop per particle; result in `scene.bodies_by_population_id[pop_id]` (and exposed by `session.population_map`). Populations are added **after** AoS avatars in the `bodies` container. |
| **`viewer_3d`** | `_expand_renderables` calls `as_avatar_view(i)` for each particle (O(N) temporary objects), then merges by batches (type + colour) disk/sphere. Large volumes: expect slowdown. |
| **`scene_geometry`** (2D schematic) | subsampled to `max_population_preview=5000` particles. |
| **`visibility_tab` / `dof_tab`** | use `pop.color` and `pop.avatar_type` to suggest colours/contactors; DOFs target an avatar, an avatar group or a colour (not a particle). |
| **`safe_eval`** | `avatar[...]` and `group[...]` expose **only** `project.avatars` / `avatar_groups`. |
| **`compute_script`** | agnostic: once DATBOX is written, an SoA particle is an `RBDY2/3` body like any other. Avatar groups only resolve AoS. |

---

## 7. AoS / SoA comparison

| Criterion | AoS — `Avatar` | SoA — `ParticlePopulation` |
|---|---|---|
| Storage | one object per body | 2 contiguous arrays + meta |
| Identity | stored `avatar_id` | stored `population_id`; particle id derived |
| Creation | `Project.add` × N (one command each); loops/masonry | `Project.deposit` — one population |
| Individual edit | native (`AvatarTab`) | no (population = block) |
| Types | all | `POPULATION_TYPES` |
| Serialisation | inline JSON (manual avatars) | JSON meta + `.npz` sidecar |
| `pre.py` | one line per avatar | one loop per population |
| Undo | one command per avatar | `AddPopulation` (one command) |
| `safe_eval` | yes | no |

**Choice rule:** large number of strictly homogeneous particles, no need for individual editing → SoA; otherwise AoS.

---

## 8. Pitfalls and conventions

1. **Homogeneity:** one population = one type, one material, one model, one colour.
2. **No mass materialisation** (`as_avatar_view` in a loop) outside the viewer.
3. **Sidecar in sync:** the `.npz` is written with the `.lmgc90`; copy/move them together.
4. **Regeneration:** redepositing creates a **new** population (new `population_id`); old ids `pop_xxx:i` become invalid.
5. **Masonry:** this is not SoA — bricks remain individual `Avatar`s.
6. **New SoA type:** add the type to `POPULATION_TYPES`, validate its `extra_params` (`_validate_extra`), complete `build_population_bodies` (`fn_map`) and `pre_script._emit_population`.
