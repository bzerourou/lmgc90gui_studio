# Prepare and run a computation

The **Compute** tab configures the `command.py` computation script, prepares the working directory and can launch the chipy process. Availability of pylmgc90 in the environment that runs LMGC90_GUI determines which native functions are accessible.

## Open the Compute tab

- Choose **Tabs → Open → Compute** when that entry is available in your application build.
- The `F5` shortcut from the main window also opens the tab and triggers the computation action.

The tab shows a summary of dimension, number of avatars and particles, laws, visibility tables, DOF and detected deformable bodies. Check that it matches the prepared project.

## Set basic parameters

1. Under **Time parameters**, set **Time step (dt)**, **Number of iterations** and **Integrator Theta**.
2. Under **Contact solver**, set **Tolerance**, **Relaxation**, **Norm**, **GS1 iterations**, **GS2 iterations** and **Solver type**.
3. Under **Outputs**, set **WriteOut** and **Display** frequencies.
4. Enable or disable **Disable chipy log messages** depending on whether you want to reduce standard output.
5. Enable **ReadDatbox(deformable=True)** if the scene has deformable bodies. The summary may also detect a mesh.

The interface initial values are starting parameters, not a guarantee of stability or convergence. Adapt the time step, solver and frequencies to the problem scale.

## Configure chipy routines

1. Click **Configure chipy routines…**.
2. Under **Model**, check the hypothesis, physics and proposed model parameters.
3. Under **Routines**, enable the body families and detectors needed for the project's contact pairs. For deformable bodies, also enable the relevant FEM routines and mixed contactors.
4. Under **Extraction**, choose visualisation, avatar visibility, state vectors, forces and energies required.
5. Under **Control**, configure restart, stop criterion and multiple time steps if needed.
6. Set the **Inspect. 2D**, **Inspect. 3D** and **Inspect. Interact.** tabs if inspection functions are needed.
7. Use **Preview command.py script** to examine the generated script.
8. Confirm with **OK** or cancel with **Cancel**. **Restore Defaults** restores the dialog default values.

Checked detectors must cover the contactor types actually present and the project's visibility tables. A table is not enough if the corresponding detector is not enabled.

## Choose the directory and prepare files

1. Under **Computation directory**, enter the working path or click **Browse…**.
2. Click **💾 Save → preferences** if you want to reuse these settings later.
3. Click **📦 Prepare DATBOX / scripts**.
4. The application writes `pre.py` and `command.py` in the selected directory.
5. Creation of `DATBOX` depends on automatic write preferences and pylmgc90 availability.
6. Check the confirmation message and the preparation log.

The **Computation → Generate DATBOX / scripts…** menu (`Ctrl+F5`) also offers a prepare/export action. To export only scripts or everything from save dialogs, use **Tools → Generate pre.py…**, **Generate command.py…** or **Export all…**.

## Run and stop the computation

1. Check the working directory path.
2. Click **▶ Run computation (F5)** or use `F5`.
3. If `command.py` is missing, accept its preparation if you want to continue.
4. Confirm the directory and command if launch confirmation is enabled in preferences.
5. Follow the log lines in the Compute tab.
6. Click **⏹ Stop** to request process termination.
7. At the end, check the status and return code (`rc`).

The process runs separately so the interface stays responsive. A launch requires a working Python interpreter and LMGC90 dependencies in the selected environment.

## Preferences and diagnostics

- **📥 Load preferences** reloads saved parameters.
- **💾 Save → preferences** stores computation parameters and the working directory.
- The computation log contains process outputs.
- **Computation → Application journal** (`F7`) provides the application internal log.

The [Post-processing](postpro.md) page describes extraction commands; the [Visualisation](visualisation.md) page describes scene inspection before computation. The current application does not provide a full browser for computed result files.
