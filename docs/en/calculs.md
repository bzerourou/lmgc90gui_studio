# Prepare and run a computation

The **Compute** tab configures the `command.py` computation script, prepares the working directory and can launch the chipy process. Availability of *pylmgc90* in the environment that runs LMGC90_GUI Studio determines which native functions are accessible.

![](../captures/calcul_tab.png)

## Open the Compute tab

- **Computation → Run computation** opens the **Compute** tab and starts the computation action.
- The `F5` shortcut from the main window also opens the tab and triggers computation.

From top to bottom the tab includes: the **model summary**, groups **Time parameters**, **Contact solver**, **Outputs**, **Chipy routines**, **Computation directory**, action buttons, a status line and the **computation log**.

## Set basic parameters

### 1. Time parameters

| Field | Key | Default | Description |
|---|---|---|---|
| **Time step (dt)** | `dt` | `1e-3` | integration step (s) |
| **Number of steps** | `nb_steps` | `1000` | number of steps; simulated duration = `dt × nb_steps` |
| **Integrator theta** | `theta` | `0.5` | θ-scheme parameter (`Integrator_InitTheta`): 0.5 = Crank–Nicolson, 1 = implicit Euler |

All fields are text; a **decimal comma** is accepted (`1e-3`, `0,5`). Expressions and dynamic variables are **not** accepted here.

**Choosing `dt`:** displacement per step should stay small compared with the smallest radius (e.g. `v_max × dt ≲ 0.1 × r_min`). Start small, then increase.

### 2. Contact solver

| Field | Key | Default | Description |
|---|---|---|---|
| **Tolerance** | `tol` | `1.666e-4` | contact solver convergence criterion |
| **Relaxation** | `relax` | `1.0` | relaxation factor |
| **Norm** | `norm` | `Quad ` | `Quad ` · `QM   ` · `Maxm ` (5-character strings including spaces) |
| **GS iterations 1** | `gs_it1` | `50` | Gauss–Seidel outer loop |
| **GS iterations 2** | `gs_it2` | `1000` | Gauss–Seidel inner loop |
| **Solver type** | `solver_type` | `Stored_Delassus_Loops` | `Stored_Delassus_Loops` · `Exchange_Local_Global` · `Conjugate_Gradient` |

### 3. Outputs

| Field | Key | Default | Description |
|---|---|---|---|
| **Write frequency** | `freq_write` | `50` | write every N steps |
| **Display frequency** | `freq_display` | `50` | display files every N steps |
| **Disable log** | `disable_log` | unchecked | calls `utilities_DisableLogMes()` |

### 4. Computation directory

Set the working directory where `command.py`, DATBOX and results are written. It can be stored in preferences.

## Chipy routines dialog

Open **Chipy routines** to configure advanced options used when generating `command.py`.

### Model tab

On open, contact detectors are **inferred from project visibility tables**. Mechanical hypothesis: plane stress (`mhyp=1`), plane strain (`mhyp=2`), 3D (`mhyp=0`). Deformable bodies: MAILx physics (`MECAx`, `THERx`, `POROx`, `THMx`), `Rloc_tol`.

Notes: 3D uses `mhyp = 0`. Checking **deformable** enables the matching MAILx writers.

### Routines tab

Only **interaction detectors** are checked (official `SelectProxTactors` modules). Contactors are loaded via `LoadTactors`.

Rigid: `RBDY2` (2D), `RBDY3` (3D).

2D detectors include `DKDKx`, `DKJCx`, `CLALp`, `PLPLx`, `PTPT2`, etc. 3D detectors include `SPSPx`, `CDCDx`, `PRPRx`, `PTPT3`, etc.

### Extraction / inspection / SET

Configure GetBodyVector, GET inspection and SET actions in the corresponding dialog tabs.

### Advanced options placement

* **Before the time loop**: `CircularSelection`, `SetContactRadius`, `SetDomainBoundary`, `SetPeriodicCondition`, `InitHDF5`, …
* **Inside the loop**: `Assemble*`, `WriteOutDof`, `FatalDamping`, `WriteHDF5`, …
* **After the loop**: `WriteLast*`, `WriteBodies`, `WriteBehaviours`, …

Configuration arguments are free Python literals validated with `ast.parse`.

## Generation workflow

1. Adjust time, solver and output parameters.
2. Configure chipy routines if needed.
3. Choose the computation directory.
4. `command.py` is written with form **and** chipy settings.
5. If DATBOX live is enabled and pylmgc90 is available: materialise `DATBOX/`.
6. Run chipy and follow the log.

## Troubleshooting

* Keep exact padded `norm` / `solver_type` strings.
* `mhyp` in 3D must be `0`.
* No contacts → check Visibility and detectors.
* Missing pylmgc90 → script generation still works; live DATBOX may be limited.

See also [Discover the interface](interface.md), [Contact laws](contact_laws.md), [Visibility tables](visibility.md).
