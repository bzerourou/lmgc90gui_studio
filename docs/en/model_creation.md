# Create a model

The **Models** tab associates a physics family and a finite element with a dimension suited to your avatars.

![](../captures/models.png)

## Create a model

1. Open **Tabs → Open → Models** (`Ctrl+2`).
2. Enter a **Name** of at most five characters. A name suggestion may appear automatically.
3. Choose **Physics**: `MECAx`, `THERx`, `POROx` or `MULTI`.
4. Choose **Element** from the list. It is updated according to the physics and the project dimension.
5. Check **Dimension (project)**. This dimension is inherited from the project; it is not set in the model form.
6. Click **Add**.
7. Verify that the model appears in the table.

> **Note:** A name that is already used does not create a second entry: select the existing model and choose **Update** to modify it.

## Edit or delete

1. Click the model row in the list.
2. The **Name**, **Physics** and **Element** fields are reloaded.
3. Change the values then click **Update**.
4. To delete the selected model, click **Delete**. First check that no avatar or configuration references it.
5. Use **Clear form** to drop the selection and prepare a new entry.

## Choose physics and element

All four physics are implemented in LMGC90_GUI Studio.

| Code | Full name | Description | Compatible materials |
|------|-----------|-------------|----------------------|
| `MECAx` | Solid mechanics | Deformation, stress, dynamics. | `RIGID`, `ELAS`, `ELAS_DILA`, `VISCO_ELAS`, `ELAS_PLAS` |
| `THERx` | Thermal | Heat diffusion, convection, radiation. | `THERMO_ELAS` |
| `POROx` | Poromechanics | Solid/fluid coupling according to Biot theory. | `PORO_ELAS` |
| `MULTI` | Thermo-hydro-mechanical (THM) | Full mechanical + thermal + hydraulic coupling. | `PORO_ELAS`, `THERMO_ELAS` |

> **Note:** The drop-down list is the reference for choices available with the installed version; it updates when you change the physics.

## Rigid model: examples

### Rigid body 2D

1. Ensure the project is 2D.
2. In **Models**, enter for example `rigid`.
3. Choose `MECAx`.
4. Choose `Rxx2D`.
5. Click **Add**.

### Rigid body 3D

1. Create or use a 3D project.
2. Enter a short name, for example `rig3D`.
3. Choose `MECAx`, then `Rxx3D`.
4. Click **Add**.

## Finite-element model

1. Create a project of the desired dimension.
2. In **Models**, choose a physics compatible with the planned analysis.
3. Select the offered element matching the type of mesh that will be built or imported.
4. Click **Add**.
5. Associate this model with a suitable material in **Materials**, then choose it when creating the body in **Avatars** or in the **Deformable** wizard.

> **Note:** The deformable-body wizard has extra options specific to its meshing workflow. They are not fields of the **Models** tab: see [Deformable body wizard](meshed.md).

## Elements available by physics

### MECAx — Mechanical elements 2D

| Element | Geometry | Nodes | Order | Description |
|---------|----------|-------|-------|-------------|
| `Rxx2D` | Point | 1 | — | Rigid body 2D. No option. |
| `T3xxx` | Triangle 3 nodes | 3 | 1 | Standard linear triangle. |
| `T3Lxx` | Triangle 3 nodes | 3 | 1 | Enriched linear triangle (incompatible). |
| `T6xxx` | Triangle 6 nodes | 6 | 2 | Quadratic triangle. |
| `DKTxx` | Triangle 3 nodes | 3 | 1 | Discrete Kirchhoff triangle (thin plates). |
| `Q4xxx` | Quadrangle 4 nodes | 4 | 1 | Standard bilinear quadrangle. |
| `Q4P0x` | Quadrangle 4 nodes | 4 | 1 | Bilinear quadrangle + constant pressure (quasi-incompressible). |
| `Q8xxx` | Quadrangle 8 nodes | 8 | 2 | Serendipity quadrangle. |
| `Q8Rxx` | Quadrangle 8 nodes | 8 | 2 | Serendipity quadrangle with reduced integration. |
| `Q9xxx` | Quadrangle 9 nodes | 9 | 2 | Biquadratic Lagrange quadrangle. |
| `BARxx` | Segment 2 nodes | 2 | 1 | Bar / 1D truss. |
| `SPRG2` | Segment 2 nodes | 2 | 1 | 2D spring (`discrete=yes__` added automatically). |
| `S2xth` | Segment 2 nodes | 2 | 1 | 1D thermal element also available in this family. |

### MECAx — Mechanical elements 3D

| Element | Geometry | Nodes | Order | Description |
|---------|----------|-------|-------|-------------|
| `Rxx3D` | Point | 1 | — | Rigid body 3D. No option. |
| `TE4xx` | Tetrahedron 4 nodes | 4 | 1 | Linear tetrahedron. |
| `TE4Lx` | Tetrahedron 4 nodes | 4 | 1 | Enriched linear tetrahedron (F-bar). |
| `TE10x` | Tetrahedron 10 nodes | 10 | 2 | Quadratic tetrahedron. |
| `H8xxx` | Hexahedron 8 nodes | 8 | 1 | Trilinear hexahedron. |
| `H20xx` | Hexahedron 20 nodes | 20 | 2 | Serendipity hexahedron. |
| `H20Rx` | Hexahedron 20 nodes | 20 | 2 | Serendipity hexahedron with reduced integration. |
| `PRI6x` | Prism 6 nodes | 6 | 1 | Linear prism. |
| `SHB6x` | Prism 6 nodes | 6 | 1 | SHB6 solid-shell prism. |
| `PRI15` | Prism 15 nodes | 15 | 2 | Quadratic prism. |
| `BARxx` | Segment 2 nodes | 2 | 1 | Bar / 1D truss. |
| `SPRG3` | Segment 2 nodes | 2 | 1 | 3D spring (`discrete=yes__` added automatically). |

> **Note:** If you need to change the project dimension, use **Project → Set dimension…** and read the warning before confirming. The change does not automatically convert existing models or avatars.

### THERx — Thermal elements 2D

| Element | Nodes | Order | Specific thermal options |
|---------|-------|-------|--------------------------|
| `Rxx2D` | 1 | — | none |
| `T3xxx` | 3 | 1 | `mass_storage`, `convection`, `radiation` |
| `T6xxx` | 6 | 2 | `mass_storage`, `convection`, `radiation` |
| `DKTxx` | 3 | 1 | `mass_storage`, `convection`, `radiation` |
| `Q4xxx` | 4 | 1 | `mass_storage`, `convection`, `radiation` |
| `Q4P0x` | 4 | 1 | `mass_storage`, `convection`, `radiation` |
| `Q8xxx` | 8 | 2 | `mass_storage`, `convection`, `radiation` |
| `Q8Rxx` | 8 | 2 | `mass_storage`, `convection`, `radiation` |
| `SPRG2` | 2 | 1 | `mass_storage` only |
| `S2xth` | 2 | 1 | `mass_storage` only — 1D thermal segment |

### THERx — Thermal elements 3D

| Element | Nodes | Order | Specific thermal options |
|---------|-------|-------|--------------------------|
| `Rxx3D` | 1 | — | none |
| `TE4xx` | 4 | 1 | `mass_storage`, `convection`, `radiation` |
| `TE10x` | 10 | 2 | `mass_storage`, `convection`, `radiation` |
| `H8xxx` | 8 | 1 | `mass_storage`, `convection`, `radiation` |
| `H20xx` | 20 | 2 | `mass_storage`, `convection`, `radiation` |
| `H20Rx` | 20 | 2 | `mass_storage`, `convection`, `radiation` |
| `PRI6x` | 6 | 1 | `mass_storage`, `convection`, `radiation` |
| `PRI15` | 15 | 2 | `mass_storage`, `convection`, `radiation` |
| `SPRG3` | 2 | 1 | `mass_storage` only |

### POROx — Poromechanical elements (mixed displacement-pressure)

| Element | Dim. | Geometry | Nodes | Order | Description |
|---------|------|----------|-------|-------|-------------|
| `T33xx` | 2D | Triangle | 3 | 1 | Mixed P1/P1 triangle. |
| `T63xx` | 2D | Triangle | 6 | 2 | Mixed P2/P1 triangle — satisfies the LBB condition. |
| `Q44xx` | 2D | Quadrangle | 4 | 1 | Mixed Q1/Q1 quadrangle. |
| `Q84xx` | 2D | Quadrangle | 8 | 2 | Mixed Q2/Q1 quadrangle — satisfies the LBB condition. |
| `TE44x` | 3D | Tetrahedron | 4 | 1 | Mixed P1/P1 tetrahedron. |
| `TE104` | 3D | Tetrahedron | 10 | 2 | Mixed P2/P1 tetrahedron — satisfies the LBB condition. |
| `H88xx` | 3D | Hexahedron | 8 | 1 | Mixed Q1/Q1 hexahedron. |
| `H208x` | 3D | Hexahedron | 20 | 2 | Mixed Q2/Q1 hexahedron — satisfies the LBB condition. |

### MULTI — THM elements 2D and 3D

Same mixed elements as POROx, plus `H8xxx` in 3D for uniform interpolation of the three coupled fields.

| Element | Dim. | Description |
|---------|------|-------------|
| `T33xx` | 2D | Mixed P1/P1 triangle. |
| `T63xx` | 2D | Mixed P2/P1 triangle. |
| `Q44xx` | 2D | Mixed Q1/Q1 quadrangle. |
| `Q84xx` | 2D | Mixed Q2/Q1 quadrangle. |
| `TE44x` | 3D | Mixed P1/P1 tetrahedron. |
| `TE104` | 3D | Mixed P2/P1 tetrahedron. |
| `H8xxx` | 3D | Trilinear hexahedron (uniform THM interpolation). |
| `H88xx` | 3D | Mixed Q1/Q1 hexahedron. |
| `H208x` | 3D | Mixed Q2/Q1 hexahedron. |

## Available model parameters

The tab displays options for the selected physics and element. Rigid elements `Rxx2D` and `Rxx3D` have no options. Springs `SPRG2` and `SPRG3` automatically receive `discrete="yes__"`. Additional options can be entered as `name=value`.

### MECAx

| Option | Offered values |
|--------|----------------|
| `kinematic` | `small`, `large` |
| `formulation` | `UpdtL`, `TotaL` |
| `mass_storage` | `lump_`, `coher` |
| `material` | `elas_`, `elasd`, `J2iso`, `J2mix`, `kvisc` |
| `anisotropy` | `iso__`, `ortho` |
| `external_model` | `MatL_`, `Demfi`, `Umat_`, `no___`, `yes__` |

The first three options depend on the element; the last three are common options for deformable elements.

### THERx

Deformable thermal elements offer `capacity_storage` (`coher`), `formulation` (`class`), and `convection_type` (`supg_`, `char_`, `center`). `SPRG2` and `SPRG3` offer only `capacity_storage`. `external_model` is common (`no___`, `yes__`). Rigid elements have no options.

### POROx

Poromechanical elements offer `kinematic` (`small`, `large`), `mass_storage` and `capacity_storage` (`lump_`, `coher`), and common `material`, `anisotropy`, `external_model`, `physical_type` (`fluid`, `solid`), and `convection_type` (`supg_`, `char_`, `center`) options.

### MULTI

THM elements offer `kinematic`, `mass_storage`, and `formulation`, with common `material`, `anisotropy`, `external_model`, `fluid_comp_storage` (`lump_`, `coher`), and `convection_type` (`supg_`, `char_`, `center`) options.

---

## Summary table by use

| Use | Dimension | Recommended elements | Note |
|-----|-----------|----------------------|------|
| Rigid bodies 2D (DEM) | 2D | `Rxx2D` | No option |
| Rigid bodies 3D (DEM) | 3D | `Rxx3D` | No option |
| Springs / bars 2D | 2D | `SPRG2`, `BARxx` | `discrete=yes__` auto |
| Springs / bars 3D | 3D | `SPRG3`, `BARxx` | `discrete=yes__` auto |
| 2D structures — standard precision | 2D | `Q4xxx`, `T3xxx` | Fast, suited to structured meshes |
| 2D structures — complex geometry | 2D | `T6xxx`, `Q8xxx` | Automatic unstructured meshes |
| Thin plates 2D | 2D | `DKTxx` | Kirchhoff formulation |
| Quasi-incompressibility 2D | 2D | `Q4P0x` | Constant pressure per element |
| 3D structures — structured mesh | 3D | `H8xxx`, `H20xx` | Hexahedra recommended |
| 3D structures — automatic mesh | 3D | `TE10x`, `TE4xx` | Adaptive tetrahedra |
| Thick shells 3D | 3D | `SHB6x`, `PRI6x` | Solid-shells |
| Thermal 2D | 2D | `Q4xxx`, `T3xxx` | Physics THERx |
| Thermal 3D | 3D | `H8xxx`, `TE4xx` | Physics THERx |
| 1D thermal segment | 2D / 3D | `S2xth` | THERx only |
| Poromechanics 2D (Biot) | 2D | `T63xx`, `Q84xx` | LBB satisfied — recommended |
| Poromechanics 3D (Biot) | 3D | `TE104`, `H208x` | LBB satisfied — recommended |
| Coupled THM 3D | 3D | `H8xxx`, `TE104` | Physics MULTI |

---

## Material / physics compatibility table

| Material | MECAx | THERx | POROx | MULTI |
|----------|-------|-------|-------|-------|
| `RIGID` | ✅ | ❌ | ❌ | ❌ |
| `ELAS` | ✅ | ✅ | ❌ | ❌ |
| `ELAS_DILA` | ✅ | ✅ | ❌ | ❌ |
| `VISCO_ELAS` | ✅ | ❌ | ❌ | ❌ |
| `ELAS_PLAS` | ✅ | ❌ | ❌ | ❌ |
| `THERMO_ELAS` | ✅ | ✅ | ❌ | ✅ |
| `PORO_ELAS` | ❌ | ❌ | ✅ | ✅ |
| `DISCRETE` | ✅ | ❌ | ❌ | ❌ |
| `USER_MAT` | ✅ | ❌ | ❌ | ❌ |
| `EXTERNAL` | ✅ | ❌ | ❌ | ❌ |

---

## Material / material-option compatibility table

| Material | `elas_` | `elasd` | `J2iso` | `J2mix` | `kvisc` |
|----------|---------|---------|---------|---------|---------|
| `RIGID` | ✅ | — | — | — | — |
| `ELAS` | ✅ | — | — | — | — |
| `ELAS_DILA` | ✅ | ✅ | — | — | — |
| `VISCO_ELAS` | — | — | — | — | ✅ |
| `ELAS_PLAS` | — | ✅ | ✅ | ✅ | — |
| `THERMO_ELAS` | ✅ | ✅ | — | — | — |
