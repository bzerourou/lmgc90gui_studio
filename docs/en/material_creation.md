# Create a material

The **Materials** tab holds the list of materials in the project and a create/edit form. The properties shown change with the selected type; this is not a free-text field.

All tabs in LMGC90_GUI Studio are made of two sections:

* **List**: lists all elements you have created;
* **Form**: fill in parameters through text fields, drop-down lists or checkboxes.

![](../captures/onglet_sections.png)

## Add a material

1. Open **Tabs → Open → Materials** (`Ctrl+1`).
2. Enter a **Name** of at most five characters. A name may be suggested automatically according to the type.
3. Choose **Type**.
4. Fill in **Density** if the field is enabled. Density is used by LMGC90 for the types that support it.
5. Complete the fields under **Properties (by type / anisotropy)**. Choices and numeric fields adapt to the selected material.
6. Click **Add**. A validation error appears if a required name or property is invalid.
7. Select a row in the table to reload its values. Edit them then click **Update**.
8. To delete a material, select it and click **Delete**. If other objects reference it, fix those dependencies first.
9. Click **Clear form** to prepare a new entry.

Initial values are a starting point, not an automatic characterisation of the real material. Check units and physical constants before the computation.

## Parameters offered by type

LMGC90_GUI Studio offers **10 material types**, matching the types accepted by `pre.material(materialType=…)` in pylmgc90.

> **Note:** types marked *(advanced)* — `DISCRETE`, `USER_MAT`, `EXTERNAL` — have no automatic suggestion in the interface. Their parameters must be entered manually.

| Type | Main interface fields | Notes |
|---|---|---|
| `RIGID` | No type-specific field | Use **Density**. |
| `ELAS` | `elas`, `anisotropy`, `young`, `nu`, `G` or directional constants | Only type where the interface offers `orthotropic`. |
| `ELAS_DILA` | `elas`, isotropy, `young`, `nu`, `dilatation`, `T_ref_meca` | No `G` and no orthotropic fields. |
| `VISCO_ELAS` | `elas`, isotropy, `young`, `nu`, `viscous_model`, `viscous_young`, `viscous_nu` | No `viscosity` field and no `G`. |
| `ELAS_PLAS` | `young`, `nu`, `critere`, `isoh`, `iso_hard`, `isoh_coeff`, `cinh`, `visc` | Choices are provided by controlled lists. |
| `THERMO_ELAS` | `young`, `nu`, `dilatation`, `T_ref_meca`, `conductivity`, `specific_capacity` | `conductivity` and `specific_capacity` accept a value or `field`. |
| `PORO_ELAS` | `young`, `nu`, `hydro_cpl`, `conductivity`, `specific_capacity` | `conductivity` and `specific_capacity` accept a value or `field`. |
| `DISCRETE` | `masses`, `stiffnesses`, `viscosities` | Enter a 2D or 3D vector; the density field is disabled. |
| `USER_MAT` | `file_mat` | Give the path/name of the material law according to the LMGC90 configuration. |
| `EXTERNAL` | No property field | Density field is disabled; behaviour is handled outside. |

### Typical uses

| Type | Typical applications | Concrete examples | Domains |
|------|----------------------|-------------------|---------|
| `RIGID` | Discrete element method (DEM) | Grain stacks, granular flows, particle assemblies | Civil engineering, pharmacy, food industry |
| `ELAS` | Structures in the elastic regime | Buildings, bridges, mechanical parts, metal structures | Civil engineering, mechanics |
| `ELAS_DILA` | Unilateral thermal stresses | Structures under temperature changes, differential expansion | Building, mechanics, electronics |
| `VISCO_ELAS` | Materials with viscous behaviour | Polymers, asphalt, damping materials, seals | Roads, automotive, aeronautics |
| `ELAS_PLAS` | Permanent plastic deformations | Metal forming, impact, damage, machining | Metallurgy, automotive, aeronautics |
| `THERMO_ELAS` | Full thermo-mechanical coupling | Thermal dissipation, thermal shocks, braking | Electronics, automotive, nuclear |
| `PORO_ELAS` | Saturated porous media | Soil consolidation, oil reservoirs, aquifers, CO₂ storage | Geotechnics, hydrogeology, petroleum |
| `DISCRETE` | Mass–spring–damper systems | Seismic isolators, suspensions, discrete elastic links | Earthquake engineering, automotive |
| `USER_MAT` | Custom constitutive laws | Specific materials, laws from experiments | Research, innovative materials |
| `EXTERNAL` | Coupling with an external code | Interface with other simulation software | Multi-physics simulation |

### Isotropic and orthotropic elasticity

For `ELAS`, choose `isotropic` to fill in **Young** and **Poisson**. For an orthotropic law, choose `orthotropic`: isotropic properties are replaced; `G` is also offered.

- In 2D: `young1`, `young2`, `nu12`, `G12`.
- In 3D: `young1`, `young2`, `young3`, `nu12`, `nu13`, `nu23`, `G12`, `G13`, `G23`.

Fields that are 3D-only are hidden in a 2D project. Types `ELAS_DILA`, `VISCO_ELAS`, `ELAS_PLAS`, `THERMO_ELAS` and `PORO_ELAS` remain isotropic in this form: do not try to add orthotropic properties to them.

### Viscous options

For `VISCO_ELAS`, use `viscous_model` (`none` or `KelvinVoigt`) then the properties `viscous_young` and `viscous_nu` if the viscous model is active. Old properties named `eta` or `viscosity` are not accepted by this version of pylmgc90 and must not be entered.

### Elasto-plasticity

`ELAS_PLAS` offers among others the criterion `Von-Mises` or `none`, isotropic/kinematic hardening models and their parameters. Choose consistent values among `isoh`, `cinh` and `visc`; pylmgc90 validates the choices at materialisation time.

## Special numeric parameters

- Numeric values are entered in the dedicated fields. Interface controls expose properties according to the selected type.
- For `THERMO_ELAS` and `PORO_ELAS`, enter `field` in the conductivity/capacity fields when they are carried by the finite-element model rather than by a scalar.
- For `DISCRETE`, enter components separated by commas, for example `1, 1` in 2D or `1, 1, 1` in 3D. Each vector must have the same dimension as the project.
- `RIGID` has no extra property; fill in density.

## Example: elastic steel material

1. Open **Materials**.
2. Choose `ELAS`.
3. Enter a name such as `STEEL` (5 characters maximum).
4. Keep `isotropic`.
5. Set **Density** to about `7850` kg/m³, **Young** to `2.1e11` Pa and **Poisson** to `0.3`.
6. Click **Add**.
7. Then create a mechanical model and assign this material to an avatar.

## Update and delete

Select the material in the list before clicking **Update**; this loads all of its information into the form. Check the name: if you enter a name that is already used, either add a new material with **Add** or explicitly update the selected entry.

> **Note:** Deletion is not a way to rename or automatically replace all references. Reassign the affected avatars to another material first if the application reports a dependency.

## Dynamic variables

Numeric fields that support expressions can use project variables. Open **Tools → Dynamic variables…** (`Ctrl+V`) to create them, see their resolved value and edit them. The dialog and expression limits are detailed in [Dynamic variables](dynam_variables.md).
