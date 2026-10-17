# Boundary conditions and DOF operations

The **DOF** tab records kinematic operations: driven DOF, initial values, geometric translation or rotation.

![](../captures/DOF.png)

## Add an operation

1. Open **Tabs → Open → DOF** (`Ctrl+9`).
2. Choose **Law**, **Target type** (`avatar` / `group` / `color`) and **Target value**.
3. Fill **Params**.
4. Click **Add**.

Laws include `imposeDrivenDof`, `imposeInitValue`, `translate`, `rotate`.

Use only components valid for the project dimension.
