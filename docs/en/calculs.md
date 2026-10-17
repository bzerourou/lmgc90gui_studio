# Prepare and run a computation

The **Compute** tab configures the computation script `command.py`, prepares the working directory and can launch the chipy process. Whether *pylmgc90* is available in the environment that runs LMGC90_GUI Studio determines which native functions are accessible.

![](../captures/calcul_tab.png)

## Open the Compute tab

- Choosing **Computation → Run computation** opens the **Compute** tab and starts the computation.
- The `F5` shortcut from the main window also opens the tab and triggers the computation action.

From top to bottom the tab includes: the **model summary**, the groups **Time parameters**, **Contact solver**, **Outputs**, **Chipy routines**, **Computation directory**, action buttons, a status line and the **computation log**.

## Set basic parameters

### 1. Time parameters

| Field | Key | Default | Description |
|---|---|---|---|
| **Time step (dt)** | `dt` | `1e-3` | integration step (s) |
| **Number of steps** | `nb_steps` | `1000` | number of steps; simulated duration = `dt × nb_steps` |
| **Integrator theta** | `theta` | `0.5` | θ-scheme parameter (`Integrator_InitTheta`): 0.5 = Crank–Nicolson, 1 = implicit Euler |

All fields are text; a **decimal comma** is accepted (`1e-3`, `0,5`). Expressions and dynamic variables are **not** accepted here.

**Choosing `dt` (order of magnitude):** the displacement per step should stay small compared with the smallest radius (for example `v_max × dt ≲ 0.1 × r_min`). LMGC90 has no stability condition tied to a contact stiffness, but a too large `dt` degrades detection and accuracy. With deformable bodies, also account for elastic waves. Start small, then increase.

### 2. Contact solver

| Field | Key | Default | Description |
|---|---|---|---|
| **Tolerance** | `tol` | `1.666e-4` | contact solver convergence criterion |
| **Relaxation** | `relax` | `1.0` | relaxation factor |
| **Norm** | `norm` | `Quad ` | convergence norm: `Quad ` · `QM   ` · `Maxim` (5-character strings including spaces) |
| **GS iterations 1** | `gs_it1` | `50` | Gauss–Seidel iteration parameter (1st loop) |
| **GS iterations 2** | `gs_it2` | `1000` | Gauss–Seidel iteration parameter (2nd loop) |
| **Solver type** | `solver_type` | `Stored_Delassus_Loops` | `Stored_Delassus_Loops` · `Exchange_Local_Global` · `Conjugate_Gradient` |

The `norm` and `solver_type` strings are passed **padded with spaces** (5 and 30 characters) as required by `chipy.ExSolver`: do not edit them by hand. The exact meaning of the norm and of `gs_it1`/`gs_it2` is defined by LMGC90 (see its documentation); in practice, increasing the iterations improves convergence at the cost of runtime, and proper convergence is checked with the post-processing command `SOLVER INFORMATIONS`.

### 3. Outputs

| Field | Key | Default | Description |
|---|---|---|---|
| **WriteOut frequency** | `freq_write` | `50` | write results every N steps (`chipy.WriteOut(freq)`) |
| **Display frequency** | `freq_display` | `50` | visualisation files every N steps (`WriteDisplayFiles(freq)`) |
| **Disable chipy log messages** | `disable_log` | checked | `chipy.utilities_DisableLogMes()` after initialisation |
| **ReadDatbox(deformable=True)** | `deformable` | depends on project | read deformable bodies |

Directories produced by a run (created by `chipy.checkDirectories()`): `OUTBOX/`, `DISPLAY/`, `POSTPRO/`. Open visualisation files in ParaView; the application does not provide a results browser.

**Note:** the default UI values are starting parameters, not a guarantee of stability or convergence. Adapt the time step, solver and frequencies to the scale of the problem.

### 4. Tab buttons

| Button | Action |
|---|---|---|
| **Load preferences** | reloads into the form the saved values (dt, nb_steps, theta, tol, relax, gs_it1/2, norm, solver, frequencies, deformable, log) and the working directory |
| **Save → preferences** | writes these values and the directory to `~/.LMGC90_GUI Studio/preferences.json` |
| **Prepare DATBOX / scripts** | writes `pre.py`, `command.py` and (if possible) `DATBOX/` |
| **Run computation (F5)** | executes `command.py` |
| **Stop** | requests process termination |

![](../captures/calcul_tab2.png)

> Settings from the **chipy dialog** (routines, extraction, steering, inspection) are **not saved** in preferences or in the project: they live in memory for the tab session. After restarting the application, you must enter them again.

### 5. Computation directory

**Computation directory** field + **Browse…**. If the field is empty when you act, a folder picker opens. It must receive `command.py`, `pre.py` and `DATBOX/`. The last chosen directory is remembered (preferences).

### 6. Prepare, then run

#### Prepare

1. Parameters are read (message *“Invalid parameters: …”* on input error) and **saved to preferences**.
2. The directory is created if needed.
3. `pre.py` is written (always possible).
4. `command.py` is written with **all** parameters: form **and** chipy settings.
5. If the preference *DATBOX live if pylmgc90 available* is on (default) **and** pylmgc90 is importable in the application: materialise then write `DATBOX/`.
6. A message lists the files written.

**Without pylmgc90 in the application:** no DATBOX. Generate it afterwards with an environment that has pylmgc90:

```bash
cd <computation_directory>
python pre.py        # writes DATBOX/ (pre.py ends with pre.writeDatbox)
```

#### Run (▶ / F5)

1. If `command.py` does not exist: offer to **prepare now**.
2. If the preference *Confirm before Run computation* is on (default): confirmation showing the directory and the command `python command.py`.
3. The tab log fills line by line (stdout + stderr merged); status becomes **Running…**, then **Finished (rc=…)** or **Failed**.
4. **Stop** sends a termination request.

Important points:

- **Running does not rewrite `command.py` if it already exists.** If you change a parameter, click **Prepare DATBOX/scripts** again before **Run computation**.
- Running **does not check** that `DATBOX/` is present.
- The interpreter is the one from the **Python interpreter** preference (default `python`, i.e. the one on `PATH`, not necessarily the one that runs `lmgc90-gui`). It must be able to `import pylmgc90`. Set it under **Tools → Preferences… → Paths** (for example the `python` of the pylmgc90 conda environment).
- Return code `rc ≠ 0` means an error: read the end of the log (and `F7`).

### 7. Other generation paths (watch the differences)

| Path | Chipy parameters used | Note |
|---|---|---|
| **Prepare DATBOX/scripts** (Compute tab) | **form + chipy dialog** | the only path that applies your routines/extractions |
| **Computation → Generate DATBOX / scripts…** (`Ctrl+F5`) | preferences only (dt, solver, frequencies…) | writes `pre.py`, `command.py`, DATBOX in a chosen folder; **does not apply** the chipy dialog |
| **Tools → Generate command.py…** | preferences only | same |
| **Tools → Export all…** | `dt = 1e-3`, `nb_steps = 5000` by default | does not use computation preferences |
| **Tools → Pipeline / SLURM…** | preferences | § 8.11 |

For a run with custom routines: use the **Compute** tab → **Prepare DATBOX/scripts**.

> Checked detectors must cover the contactor types actually present and the project visibility tables. A visibility table is not enough if the matching detector is not enabled.

---

### 8. The “Configure chipy routines…” dialog

The dialog opens from **Compute → Configure chipy routines…**. It drives the content of `command.py` and has **9 tabs**:

| # | Tab |
|---|-----|
| 1 | Model |
| 2 | Routines |
| 3 | **Advanced** |
| 4 | Extraction |
| 5 | Steering |
| 6 | Inspect. 2D |
| 7 | Inspect. 3D |
| 8 | Inspect. Interact. |
| 9 | **SET actions** |

Bottom buttons:

| Button | Effect |
|---|---|
| **Preview command.py script** | generates the script with `dt=1e-3`, `nb_steps=100`, `freq_write=freq_display=10` and current options; dark display, line count shown. Without a loaded project, a message says so. |
| **OK** | runs [validation](#89-validations-on-ok), then closes the dialog |
| **Cancel** | closes without applying |
| **Restore Defaults** | asks for confirmation, then resets all options |

On each open, **auto-detection** is applied from the project.

---

### 8.1 “Model” tab

#### 8.1.1 Auto-detection on open

Contact detectors are now **inferred from the project visibility tables** (`infer_chipy_contact_routines`), not only from dimension.

| Area | Content |
|---|---|
| Mechanical hypothesis | `Plane stress (mhyp=1)`, `Plane strain (mhyp=2)`, `Three-dimensional (mhyp=0)` |
| Deformable bodies | enable checkbox, **MAILx physics** (`MECAx`, `THERx`, `POROx`, `MULTI`), `Rloc_tol` (default `5e-2`) |
| Summary | name, dimension, avatars (including deformable), materials/models/laws, masonry, active laws, groups |

Points to note:

* 3D corresponds to `mhyp` = 0 in the dialog. The generator also forces `mhyp` = 0 when the project is 3D.
* In 3D, the 2D radio buttons (plane stress/strain) are disabled.
* Checking **deformable** triggers `_on_phys_changed`:
    * `MECAx` checks `mecaMAILx` and `mecaMAILx_WriteDisplayFiles`;
    * `THERx` checks `therMAILx`;
    * `POROx` and `MULTI` check `poroMAILx`.

![](../captures/chipy_model.png)

---

### 8.2 “Routines” tab

#### 8.2.1 Principle

The list now matches the official modules of `chipy.macro.SelectProxTactors`. **Contactors** (`DISKx`, `PT2Dx`, `SPHER`…) are loaded by `LoadTactors`. They are not checked here: only **interaction detectors** are checked.

#### Rigid bodies

| Checkbox | Effect |
|---|---|
| `RBDY2` | `RBDY2_*` macros (default ✅, active only if the project is 2D) |
| `RBDY3` | `RBDY3_*` macros (active only if the project is 3D) |

#### 2D detectors

| Detector | Contactor pair | Use |
|---|---|---|
| `CLALp` | CLxxx / ALpxx | line/line (masonry, MAILx interfaces) |
| `CLJCx` | CLxxx / JONCx | line/jonc |
| `DKALp` | DISKx / ALpxx | disk/MAILx line |
| `DKDKL` | DISKx / DISKL | disk/linear disk |
| `DKDKx` | DISKx / DISKx | disk/disk (default ✅) |
| `DKJCx` | DISKx / JONCx | disk/jonc (walls) |
| `DKKDx` | DISKx / POLYG | disk/polygon |
| `DKPLx` | DISKx / PLANx | disk/plane |
| `P2P2L` | PT2DL / PT2DL | point/point linear |
| `PLALp` | PLANx / ALpxx | plane/MAILx line |
| `PLJCx` | PLANx / JONCx | plane/jonc |
| `PLPLx` | PLANx / PLANx | plane/plane (dialog label) |
| `PTPT2` | PT2Dx / PT2Dx | point/point (cables, rods) |

#### 3D detectors

| Detector | Pair | Use |
|---|---|---|
| `CDCDx` | CYLND / CYLND | cylinder/cylinder |
| `CDPLx` | CYLND / PLANx | cylinder/plane |
| `CSASp` | CSxxx / ASpxx | surface/surface MAILx |
| `CSPRx` | CSxxx / POLYR | surface/polyhedron |
| `PRASp` | POLYR / ASpxx | polyhedron/MAILx surface |
| `PRPLx` | POLYR / PLANx | polyhedron/plane |
| `PRPRx` | POLYR / POLYR | polyhedron/polyhedron |
| `PTPT3` | PT3Dx / PT3Dx | point/point 3D |
| `SPCDx` | SPHER / CYLND | sphere/cylinder |
| `SPDCx` | SPHER / DNLYC | sphere/hollow cylinder |
| `SPPLx` | SPHER / PLANx | sphere/plane |
| `SPPRx` | SPHER / POLYR | sphere/polyhedron |
| `SPSPx` | SPHER / SPHER | sphere/sphere |

#### Global macro

Use `chipy.SelectProxTactors()` only: see [recommended workflow](#812-recommended-workflow).

#### MAILx modules

`mecaMAILx`, `therMAILx`, `poroMAILx`, `multiMAILx`. They only act if “deformable” is checked.

#### Shortcuts (compatibility aliases)

| Checkbox | Actually enables |
|---|---|
| Disk↔MAILx 2D (`use_DKMECAx`) | `DKALp` |
| CLALp masonry↔MAILx (`use_ALpMECAx`) | `CLALp` |
| Sphere↔MAILx 3D (`use_SPMECAx`) | `CSASp` |
| Update bulk behaviour | `chipy.UpdateBulkBehav()` |

#### 8.2.2 Choosing detectors

A detector must exist for **each pair** present in your visibility tables. The [table](#821-principle) gives the mapping. Examples:

| Pair (visibility) | Detector |
|---|---|
| `DISKx` / `DISKx` | `DKDKx` |
| `DISKx` / `JONCx` | `DKJCx` |
| `SPHER` / `SPHER` | `SPSPx` |
| `SPHER` / `PLANx` | `SPPLx` |
| `PT3Dx` / `PT3Dx` (cables, 3D rods) | `PTPT3` |

> **`POLYG` / `POLYG` (rigid 2D bricks):** the internal table `infer_chipy_contact_routines` maps this pair to `DKKDx` (code comment: *fallback*). Check in the LMGC90 documentation whether `PLPLx` suits your case better before running.

### 8.2.3 Auto-detection on open

The function `infer_chipy_contact_routines(project)` (in lmgc90_core) infers checkboxes from:

1. **avatars** and their default contactors (by avatar type);
2. **explicit contactors** (`contactors`);
3. **SoA populations**;
4. **visibility tables**, with candidate/antagonist pair → detector;
5. **co-present contactors** in the scene, even without a table;
6. **point/point laws** (`ELASTIC_WIRE`, `BRITTLE_ELASTIC_WIRE`, `ELASTIC_ROD`, `VOIGT_ROD`) → `PTPT2` (2D) or `PTPT3` (3D);
7. **presence of a mesh** → `mecaMAILx`;
8. **defaults** if nothing was inferred: `DKDKx` (+ `DKJCx`) in 2D, `SPSPx` (+ `SPPLx`) in 3D.

In the dialog:

* dimension checks `RBDY2` or `RBDY3`;
* **inferred detectors are checked**;
* **detectors specific to the other dimension are unchecked**. This improves on the old constraint “in 3D: uncheck DKDKx by hand”;
* a `mesh` avatar enables “deformable”;
* an avatar with `wall_params` (masonry) checks `CLALp`.

> Auto-detection checks boxes but only unchecks what belongs to the other dimension: re-read the result each time you open the dialog.

![](../captures/chipy_routines.png)

---

### 8.3 “Advanced” tab (new)

It groups **optional** calls, added to the script only if checked. Essential steps (`Initialize`, `ReadDatbox`, `ComputeFreeVelocity`, `WriteOut`…) remain automatic; `ReadDatbox` already reads DAT/INI files.

#### 8.3.1 Explicit assembly by physics (MAILx)

| Option | Generated calls (in the loop) | Available if |
|---|---|---|
| `advanced_assemble_mechanical` | `AssembleMechanicalLHS()` / `RHS()` | deformable + `mecaMAILx` |
| `advanced_assemble_thermal` | `AssembleThermalLHS()` / `RHS()` | deformable + `therMAILx` |
| `advanced_assemble_poro` | `AssemblePoroLHS()` / `RHS()` | deformable + `poroMAILx`, physics ≠ THM |
| `advanced_assemble_multi` | `AssembleMultiLHS()` / `RHS()` | deformable + physics **THMx** |

Irrelevant checkboxes are greyed out.

#### 8.3.2 Contacts, forces and diagnostics

| Option | Effect |
|---|---|
| `FdSelectProxTactors` | replaces standard selection (reserved for SPHER/SPHER contacts, see [validation](#89-validations-on-ok)) |
| `ComputeRnod` | `chipy.ComputeRnod()` after `UpdateStep` |
| `FatalDamping` | `RBDY2_FatalDamping()` / `RBDY3_FatalDamping()` just after `IncrementStep` |
| `SmoothForceComputation` | after `UpdateTactBehav`, before `StockRloc` |
| `DisplayProxTactors` | every step |
| `DisplayOutDof` | every step |
| `DisplayOutRnod` | every step |
| `DisplayOutVlocRloc` | every step |

#### 8.3.3 Extra outputs

**In the loop** (with frequency `freq_write`):

| Option | Call |
|---|---|
| HDF5 | `InitHDF5('<file>')` before the loop, then `WriteHDF5()` each step |
| `write_out_dof` | `RBDY2_WriteOutDof(freq_write)` or `RBDY3_WriteOutDof(freq_write)` depending on dimension |
| `write_out_gpv` | `WriteOutGPV(freq_write)` |
| `write_out_mp_values` | `WriteOutMpValues(freq_write)` |
| `write_out_rnod` | `WriteOutRnod(freq_write)` |
| `write_out_vloc_rloc` | `WriteOutVlocRloc(freq_write)` |

**After the loop:**

| Option | Call |
|---|---|
| `write_last` | `WriteLast()` |
| `write_last_dof` | `WriteLastDof()` |
| `write_last_gpv` | `WriteLastGPV()` |
| `write_last_mp_values` | `WriteLastMpValues()` |
| `write_last_rnod` | `WriteLastRnod()` |
| `write_last_vloc_rloc` | `WriteLastVlocRloc()` |
| `write_bodies` | `WriteBodies()` (preceded by `AddDof2InBodies()` if `add_dof2`) |
| `write_behaviours` | `WriteBehaviours()` |
| `write_driven_dof` | `WriteDrivenDof()` |
| `write_mp_behaviours` | `WriteMpBehaviours()` |

#### 8.3.4 Display and post-processing

| Option | Effect |
|---|---|
| `add_registers_to_display` | `chipy.addRegistersToDisplay()` before `OpenDisplayFiles` |
| `circular_selection` | `chipy.CircularSelection(x, y, r)` after `ReadDatbox` (field “Disk (x, y, r)”, default `0.0, 0.0, 1.0`) |

#### 8.3.5 Contact settings (checkboxes + argument fields)

Each row is checked and receives its **Python arguments** in a text field:

| Checkbox | Generated call | Example arguments |
|---|---|---|
| `set_contact_radius` | `SetContactRadius(args)` | `0.01` |
| `set_domain_boundary` | `SetDomainBoundary(args)` | `Xmin=-1.0, Xmax=1.0` |
| `set_number_interaction` | `SetNumberInteractionByContact(args)` (*experimental*) | `4` |
| `set_periodic_condition` | `SetPeriodicCondition(args)` | `xperiod=1.0` |

These calls are emitted just after `ReadDatbox`. The **HDF5 file** field (default `command.h5`) is set in the same area.

![](../captures/chip_avance.png)

---

### 8.4 “Extraction” tab

Sections: logs, visualisation, visibility, `GetBodyVector` RBDY2 and RBDY3, contact forces, energy, MAILx fields.

#### 8.4.1 Shared “Mode / Timing” widget

Visibility, GBV and inspections share this widget (list + value):

| Mode | Value | Generated code |
|---|---|---|
| Before the loop | `before` | single call before `for k` |
| Every step | `all` | each iteration |
| Every N steps | `every_n` (N ≥ 1) | `if k % N == 0:` |
| At step k = | `at_k` (k ≥ 0) | `if k == K:` |
| After the loop | `after` | single call after the loop |

- The numeric field is active only for `every_n` and `at_k`.
- `k` **starts at 0**.
- **Defaults:** *Before the loop* for visibility; *Every step* for GBV, inspections and SET actions.
- **Compatibility:** an old project without `step_mode` is converted. `in_loop=False` becomes `after`, `freq>1` becomes `every_n`, and the rest becomes `before` (visibility) or the zone default.

#### 8.4.2 “…” button (ID picker)

Opens a multi-select list of project avatars (Ctrl/Shift+click). It inserts **1-based** numbers (order of the avatar list) and pre-selects IDs already typed. The list is filtered by dimension (2D or 3D); `emptyAvatar` and `mesh` appear in both. Without a project, a message says so.

#### 8.4.3 Resolving IDs and groups

- **IDs take priority** over the group if both are set.
- A group is resolved to numbers `position + 1` in `project.avatars`.
- **SoA populations** are not in avatar groups. Their numbers start at `nb_avatars + 1`.
- If a group `avatar_id` is missing, a **warning** is logged (`F7`) and an **alert banner** is added before `CloseDisplayFiles` in `command.py`.

#### 8.4.4 Messages and visualisation

- `disable_log`: `utilities_DisableLogMes()` (the **Compute** tab checkbox overrides this one).
- Visualisation: `visu_RBDY2` (✅), `visu_RBDY3`, `visu_mecaMAILx`, `visu_therMAILx`, `visu_poroMAILx`, `display_in_loop` (✅).
- If `display_in_loop` is unchecked: a single final `…_WriteDisplayFiles(1)` outside the loop.

#### 8.4.5 Avatar visibility (`SetVisible` / `SetInvisible`)

Each row: Action, Dim. (2D → `RBDY2`, 3D → `RBDY3`), IDs (+ “…”), Group, Mode/Timing. Call: `chipy.RBDY2_SetVisible(id)` or `chipy.RBDY2_SetInvisible(id)`.

#### 8.4.6 Extraction `RBDY2_GetBodyVector` / `RBDY3_GetBodyVector`

Vectors: `Coor0`, `Coor_`, `Coorb`, `Coorm`, `X____`, `V____`, `Vbeg_`, `Vfree`, `Fext`, `Fint_`, `Reac`, `Ireac`. The generator produces a `for _id in [...]` loop calling `chipy.RBDYx_GetBodyVector('<vec>', _id)`.

![](../captures/chipy_extraction.png)

#### 8.4.7 Other extractions

| Checkbox | Call |
|---|---|
| Nodal forces | `inter_handler_Rnod()` |
| Local velocities | `inter_handler_Vloc()` |
| Local forces | `inter_handler_Rloc()` |
| Energy balance | `ComputeEnergy()` + `WriteEnergy()` |
| Kinetic energy | `RBDY2_KineticEnergy()` (2D, `RBDY2` active) |
| Per-element fields | `mecaMAILx_WriteBodies(freq_write)` (requires `mecaMAILx`) |
| Internal variables | `mecaMAILx_WriteInternalVariables(freq_write)` (requires `mecaMAILx`) |

---

### 8.5 “Steering” tab

| Area | Detail |
|---|---|
| **Restart** | generates `chipy.ReadIni(record=N)` after `ReadDatbox`, then `OpenDisplayFiles(restart=N+1)` (only if `N ≠ 0`) |
| **Stop criterion** | `energy` (`GetResidualEnergy`), `disp_max` (`GetMaxDisplacement`) or `force_res` (`GetForceResidual`), evaluated every `stop_freq` steps; `break` if `criterion < threshold` |
| **Multi-step** | outer loop over `dt_sequence`, `steps_per_phase = nb_steps // nb_phases`; the stop criterion only interrupts the current phase |

Reminder: `import math` is added to the script if a stop criterion is active.

![](../captures/chipy_pilotage.png)

---

### 8.6 “Inspect. 2D”, “Inspect. 3D”, “Inspect. Interact.” tabs

The catalogues now contain **several hundred** chipy functions. Each row has:

| Column | Role |
|---|---|
| **Chipy function** | list with tooltip (description) |
| **IDs** + “…” | contactor numbers (2D/3D) or pair numbers (Interact., 1-based); **empty** for functions with no argument |
| **Group** | resolved to IDs if IDs are empty |
| **Mode / Timing** | see [mode timing](#841-shared-mode--timing-widget) |
| **Python var.** | storage variable |

Catalogue content:

- **2D:** `DISKx_*`, `JONCx_*`, `POLYG_*`, `xKSID_*`, `RBDY2_*` (many: `GetAllMass`, `GetBodyVector`, `GetStress`, `GetVelocity`…), `PT2DL_*`, `PT2Dx_*`.
- **3D:** `SPHER_*`, `POLYR_*`, `CYLND_*`, `PLANx_*`, `DNLYC_*`, `RBDY3_*`, `PT3Dx_*`.
- **Interact.:** general (`GetDimension`, `TimeEvolution_Get*`), `DKDKx_GetCZMEnergy`, `PLPLx_GetCZMEnergy`, `PRPRx_Get*` (F2f, stresses, interaction vector), `ALpxx` / `ASpxx` / `CLpxx` / `CSpxx` / `CSxxx` (connectivities and data), `MAILx_Get*`, `bulk_behav_Get*`, `postpro_*`, `tact_behav_Get*`, `therMAILx_Get*`, `poroMAILx_Get*`, `multiMAILx_Get*`, `mesh2D_GetIndicesMeshQ4`.

Generator rules:

- Function **without ID** (name containing `GetNb`, or listed in `_NO_ID_FUNCS`): `chipy.Func()` or `var = chipy.Func()`.
- Function **with ID**: `for _id in [...]: chipy.Func(_id)` or `var__id = chipy.Func(_id)`.
- Timing uses the shared Mode/Timing widget.

![](../captures/chipy_inspec.png)

---

### 8.7 “SET actions” tab (new)

Inserts a chipy modification call (`Set…`) at a chosen time. It reuses the inspection row engine.

- **Catalogue:** several hundred `…_Set…` functions: `SetContactRadius`, `SetDimension`, `SetDomainBoundary`, `TimeEvolution_SetTimeStep`, `RBDY2_SetVisible` / `SetInvisible`, `RBDY3_SetXminBoundary`, `NewtonRaphson_Set*`, `nlgs_*`, `cpg_*`, `mecaMAILx_Set*`, `poroMAILx_Set*`, `tact_behav_Set*`, `postpro_Set*Zone`, etc.
- **Columns:** function, **arguments** (the “IDs” field becomes a Python-arguments field), group, mode/timing, variable.
- **Arguments:** valid Python expression, e.g. `dt * 0.5`, `1`, `Xmin=-1.0, Xmax=1.0`. With a group, use `_id` in the arguments.
- **Arity:** numeric catalogue values follow `lmgc90_user_2025` signatures; `None` means a function absent from that version.
- **Expected timing** (from `test_compute_script_set_actions.py`):

| Mode | Expected code |
|---|---|
| `before` | call before the loop |
| `all` | indented call inside the loop |
| `every_n` | `if k % 3 == 0:` then indented call |
| `at_k` | `if k == 0:` then indented call |
| `after` | call after the loop |

- Input errors expected by tests: `invalid Python arguments`, `valid chipy function name`, `invalid step mode`.

![](../captures/chipy_actionsSET.png)

---

### 8.9 Validations on **OK**

| Check | Message |
|---|---|
| Multi-step: number of `dt` ≠ number of phases | “N phases declared but M value(s) …” |
| Multi-step: a `dt` ≤ 0 or malformed | “all dt must be > 0” / “invalid format” |
| Deformable without any MAILx routine | “no MAILx routine … checked” |
| Advanced `Set…` checked without arguments | “enter the required arguments” |
| SET action: invalid name (not an identifier, Python keyword, or without “Set”) | “enter a valid chipy function name containing « Set »” |
| SET action: arguments not parseable (`ast.parse`) | “invalid Python arguments” |
| HDF5 without file name | “enter a file name” |
| HDF5 **and** individual ASCII `WriteOut*` checked | “HDF5 uses WriteOut… uncheck the ASCII outputs” |
| `AddDof2InBodies` without `WriteBodies` | “also check WriteBodies” |
| `CircularSelection` without or with invalid arguments | “enter the arguments (x, y, r)” / “invalid Python arguments” |
| `FdSelectProxTactors` with visibility pairs other than SPHER/SPHER | validation warning (reserved case) |

---

### 8.10 Useful preferences (Tools → Preferences…)

Relevant for computation:

- work directory / last computation directory;
- Python interpreter (must import `pylmgc90`);
- DATBOX live if pylmgc90 available;
- confirm before Run computation;
- default time/solver/output parameters.

---

### 8.11 SLURM export (cluster)

**Tools → Pipeline / SLURM…** generates an sbatch script from computation preferences (not from the full in-memory chipy dialog unless you prepared scripts first). Adjust modules, partitions and resource requests to your site.

---

## 8.12 Recommended workflow

1. Build the scene (materials, models, avatars, contact, visibility, DOF).
2. Open **Compute**, set dt, nb_steps, solver and frequencies.
3. Open **Configure chipy routines…**, review auto-detected detectors, adjust Advanced / Extraction / SET as needed, **OK**.
4. **Prepare DATBOX / scripts** (the only path that applies the dialog).
5. **Run computation** (`F5`) and watch the log.
6. If you change chipy options: **Prepare** again before **Run**.

---

## 8.13 Code attention points

1. **Global macro `SelectProxTactors`:** with checked detectors, the macro has no effect if individual detectors are used instead.
2. **SET actions:** the dialog produces `set_entries`, and `test_compute_script_set_actions.py` expects them to be emitted with explicit `ValueError`s. Emission does **not** appear in the supplied `compute_script.py`. Check that the generator matches the tests.
3. **`multiMAILx`:** the checkbox and key `use_multiMAILx` exist, but the generator produces no `multiMAILx_*` call.
4. **3D detectors not emitted:** in 3D the generator only reads `SPSPx`, `SPCDx`, `SPPLx`, `CDCDx`, `CDPLx`, `PRPRx`. Boxes `CSASp`, `CSPRx`, `PRASp`, `PRPLx`, `SPDCx`, `SPPRx` are checkable but write nothing. `PTPT3` is only emitted via the `use_PT3Dx` path filled by the dialog.
5. **Aliases emitted as-is:** `use_DKMECAx`, `use_ALpMECAx`, `use_SPMECAx` are kept in parameters in addition to their real detector. The generator may therefore emit `chipy.DKMECAx_SelectProxTactors()` (name absent from the official list) as well as `DKALp_…`.
6. **`PTPT2` duplicated:** `PTPT2` is in the generator’s 2D list and added a second time via `use_PT2Dx` (derived from `use_PTPT2`). Check the preview: the call may appear twice.
7. **Obsolete help texts:**
   - the Steering note cites `chipy.SetStep(restart_step)` while the code generates `ReadIni(record=N)` + `OpenDisplayFiles(restart=N+1)`;
   - the 2D tab note cites `POLYR` for 2D polygons (the contactor is `POLYG`) and `ALpALp`.
8. **`_on_3d_toggled`** only greys out old boxes (`DKDKx`, `DKJCx`, `DKKDx`, `PLPLx`, `CLALp`, `SPSPx`…). New detectors are not disabled by dimension; auto-detection compensates.
9. **Compute tab summary** (`_update_chipy_summary`): still lists `ALpALp`, `PT2Dx`, `PT3Dx` and `NODES`. Should be replaced by the official list.
10. **`Norm` list:** the Compute tab offers `Maxm `, while this page documents `Maxim`.
11. **Integration test:** `test_chipy_script_enables_detectors_required_by_demo_visibility` expects `mhyp = 3`, `RBDY3_NewStep()` and `SetDimension(2)`, which differs from the supplied generator output (`mhyp = 0` in 3D, `SetDimension(dim, mhyp)`, `IncrementStep`/`ComputeFreeVelocity` loop). Tests or generator need realignment.
12. **Old preference `chipy_options` keys:** the dialog only reloads keys known in `DEFAULTS`; `use_mecaMAIL` / `use_therMAIL` / `use_poroMAIL` (old names) are migrated to `…MAILx`.

---

### 8.14 Logs

- **Compute tab:** process output.
- **Computation → Application journal** (`F7`): internal events (preparation, errors, repository fallback, group warnings).

The [Post-processing](postpro.md) page describes extraction commands; the [Visualisation](visualisation.md) page describes scene inspection before computation. The current application does not provide a full browser for computed result files.
