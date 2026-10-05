# Configure post-processing

The **Post-pro** tab adds extraction commands to the computation. It configures what the computation should write; it is not used to open or analyse result files after execution.

![](../captures/postpro.png)

## Add a command

1. Open **Tabs → Open → Post-pro**.
2. Choose a **Command** value or enter the name of a command accepted by your LMGC90 installation.
3. Set **Step**, the write frequency.
4. Choose **Target type**: `global`, `avatar` or `group`.
5. For an `avatar` target, select the avatar; for `group`, choose the group. For `global`, no target is needed.
6. Click **Add**.
7. Check the command in the list: name, frequency and target.

Prefill names include notably `SOLVER INFORMATIONS`, `BODY TRACKING`, `TORQUE EVOLUTION`, `KINETIC ENERGY`, `COORDINATE` and `VAN_DER_WAALS`. Commands must be compatible with the configured data and computation.

## Remove a command

1. Select the command in the list.
2. Click **Remove**.

The tab does not offer in-place editing: remove a poorly defined command then recreate it with the correct parameters.

## Advanced chipy routine extractions

To set advanced outputs, open **Compute**, then **Configure chipy routines…**. The dialog includes notably the **Extraction**, **Inspect. 2D**, **Inspect. 3D** and **Inspect. Interact.** tabs. They configure state vectors, forces, energy, FEM fields, visibility and inspectors according to body type.

## View logs

- The **Compute** tab log shows the computation process output.
- **Computation → Application journal** (`F7`) shows internal LMGC90_GUI errors and events.

These logs are not a viewer of computed results. To inspect the preprocessing scene, use [Visualisation](visualisation.md).
