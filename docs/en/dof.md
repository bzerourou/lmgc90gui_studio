# Boundary conditions and DOF operations

The **DOF** tab records kinematic operations that will be applied to the targeted bodies at computation time. An operation is defined by a law, a target and a parameter string.

![](../captures/DOF.png)

## Add an operation

1. Create the relevant avatars. To target several bodies together, create a group in **Groups**.
2. Open **Tabs → Open → DOF** (`Ctrl+9`).
3. Choose **Law**.
4. Choose **Target type**: `avatar`, `group` or `color`.
5. Select or enter **Target value**. The list is filled from project avatars, groups and colours; the field can also be edited.
6. Fill **Params**, adapting components and values to the project dimension.
7. Click **Add**. The operation should appear in the list.

## Available operations

| Law | Role | Example of proposed parameters |
|---|---|---|
| `imposeDrivenDof` | Impose a driven degree of freedom | `component=[1, 2, 3], dofty='vlocy', ct=0.0` |
| `imposeInitValue` | Set an initial value | `component=[1, 2, 3], dofty='vlocy', values=[0.0, 0.0, 0.0]` |
| `translate` | Apply a geometric translation | `dx=0.0, dy=0.0, dz=0.0` |
| `rotate` | Apply a rotation about an axis | `description='axis', axis=[0, 0, 1], alpha=0.0` |

These strings are syntax examples shown by the interface. Use components that exist for the body and its dimension; do not provide a Z component in a 2D case. Parameters are passed to the corresponding operation type, so respect the expected names (`component`, `dofty`, `ct`, `values`, `dx`, etc.).

## Choose the target

- **avatar**: targets a particular avatar; choose its entry in the list, which shows a short identifier and its type.
- **group**: targets all avatars registered under the group name.
- **color**: targets avatars carrying that colour code. The list offers colours present on avatars/populations and a few usual LMGC90 codes.

The `avatar` target uses the body's stable identifier, not its position in the table. If an avatar was deleted then recreated, select the new avatar in the list.

## Edit and delete

1. Select the operation in the upper list.
2. Edit **Law**, **Target type**, **Target value** or **Params**.
3. Click **Update**.
4. To remove it, select its row then click **Delete**.
5. Click **Clear form** before creating an independent operation.

## Check the effect visually

Open **3D Visualisation**, click **Refresh scene**, then enable **DOF** to see indications corresponding to the configured operations. Symbols are a visual check; they do not replace verifying computation parameters or the simulation log.
