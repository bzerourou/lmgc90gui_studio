# Scene visualisation

LMGC90_GUI Studio offers two ways to inspect the model: the **built-in 3D viewer** (PyVista) and the native pylmgc90 viewer launched with **pre.visuAvatars**. These tools show the prepared scene; they do not replace a tool for analysing computation results.

![](../captures/interface.png)

## Open and refresh the built-in viewer

1. Open **Tabs → Open → 3D Visualisation**.
2. Check that the project contains avatars or a population.
3. Click **Refresh scene**. Transfer to the viewer is manual: after a project change, run this action again.
4. The indicator on the viewer bar signals whether the displayed scene needs updating and shows the number of objects sent.

The built-in viewer requires the `pyvista` and `pyvistaqt` modules. If either is missing, the panel shows an unavailability message instead of the scene.

## Navigate the scene

- **Nav.**: camera mode. Drag with the left button to orbit, use the wheel to zoom and the right button to pan the camera.
- **XY**, **XZ**, **Iso**: predefined views. The `XY` view generally suits 2D projects. The `YZ` view is not offered in this version.
- **🔄 Reset camera**: restores the initial framing.
- **Edges**: show or hide geometry edges.
- **Opacity slider**: makes avatars more or less transparent.
- **🗑️ Clear**: removes objects from the current view. Click **Refresh scene** again to repopulate the viewer from the project.

## Select and measure

1. Click **Select**.
2. Click an avatar in the scene. It is highlighted and its information is shown in the status bar.
3. To measure a distance, click **Ruler**.
4. Click once on a first point in the scene (A), then on the second point (B). The distance is displayed by the viewer.
5. Return to **Nav.** mode to resume navigation.

Selection applies to objects represented by the viewer. If the scene is empty or objects are too small on screen, reset the camera or zoom before selecting.

## Read colours and annotations

1. Choose the mode in the colour list: **LMGC90**, **By type**, **By material** or **By origin**.
2. Enable **DOF** to show visual markers for kinematic operations configured in the DOF tab.
3. Enable **Laws** to visualise links from visibility tables (candidate colour toward antagonist colour).
4. Open the group filter and choose a group to isolate its avatars. **All groups** shows the whole scene again.

Material and origin colours are for visual inspection; they change neither the colours stored on avatars nor the visibility rules.

## Export an image

1. Frame the scene with the camera and choose the filters, colours and annotations to include.
2. Click **📷 Export as PNG**.
3. Choose the location and file name in the dialog.

## Launch native pylmgc90 visualisation

1. In the **3D Visualisation** tab, click **pre.visuAvatars**.
2. If pylmgc90 is available, the application materialises the scene then opens the native viewer.
3. If the button indicates that `pylmgc90` is unavailable, check that the Python environment used to launch LMGC90_GUI Studio actually contains that library.

This mode uses real pylmgc90 objects and is distinct from the parametric PyVista rendering. It is unavailable without pylmgc90 and may disable individual selection in the built-in viewer while in use.

## Common issues

| Symptom | Check |
|---|---|
| Scene does not reflect the latest change | Click **Refresh scene**. |
| Viewer shows “pyvista + pyvistaqt missing” | Install these dependencies in the application environment then restart it. |
| `pre.visuAvatars` reports pylmgc90 unavailable | Check the interpreter/env used by `lmgc90-gui`, not only another terminal. |
| No avatar appears after refresh | Check that the project contains avatars/populations, then reset the camera. |
