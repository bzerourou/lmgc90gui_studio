# Create, open and organise a project

This section covers creating, opening and saving a project.

## Create a project

1. Choose **File → New** or press `Ctrl+N`.
2. In the **New project** dialog, choose dimension `2` or `3`.

![](../captures/dimension.png)

3. Enter a name and confirm. The project is created in the application; it is not yet saved to disk.

![](../captures/titre_projet.png)

To save your project:

4. Choose **File → Save As…** (`Ctrl+Shift+S`), select a folder and file name, then save. The `.lmgc90` extension is added if missing.

![](../captures/save_projet.png)

5. Check the name and dimension in the status bar.

## Save and resume work

Once the project is saved on disk:

- **File → Save** (`Ctrl+S`) writes changes to the current location.
- **File → Save As…** creates a copy under another name or in another folder.

You can open it again and edit it:

- **File → Open…** (`Ctrl+O`) opens a `.lmgc90` project file.

![](../captures/ouvrir_projet.png)

You can undo or redo operations on your models:

- **Edit → Undo** (`Ctrl+Z`) and **Edit → Redo** (`Ctrl+Y`) undo or redo the last actions when history allows.

> **Note:** Save the project after important operations, before running a computation, and before loading an example in replace mode.

## Choose and change the dimension

The project dimension determines which elements, avatars, contactors and bodies are offered in the forms.

1. Set `2` or `3` at creation time.
2. To change it later, choose **Project → Set dimension…**.

![](../captures/dimension.png)

3. Select the new dimension and read the warning if existing models no longer match.
4. Confirm only after checking models and avatars. Changing dimension does not automatically convert existing objects.

For a major switch between 2D and 3D, the clearest approach is often to create a new project with the correct dimension and rebuild or reload the appropriate scene.

## First modelling sequence

Once the project is created, the usual tab workflow is:

1. Create a material in **Materials**.
2. Create a model in **Models**.
3. Create one or more bodies in **Avatars**, or use **Granulo** for a granulometric generation.
4. Create **parametric loops** and **formal loops** on your elements.
5. Define contact laws in **Contact**, then their associations in **Visibility**.
6. Add boundary conditions in **DOF** and, if useful, create **Groups**.
7. Save the project, configure **Compute**, then prepare and run the computation.

![](../captures/onglets_list.png)

The **Deformable mesh assistant** (`Ctrl+Shift+D`) and **Masonry assistant** (`Ctrl+Shift+M`) are available from **Tools**.
The general project-configuration wizard and the granulometry assistant described in older pages are not part of the current menus.

## Tab organisation

Use **Tabs → Open** to show a feature. Materials and Models stay open as essential tabs. Closing a tab does not delete project elements.

![](../captures/onglets_open.png)

The first nine tabs have shortcuts `Ctrl+1` to `Ctrl+9` in this order: Materials, Models, Avatars, Loops, ForLoop, Granulo, Contact, Visibility and DOF. **Tabs → Default tabs** (`Ctrl+Alt+D`) restores the initial layout.

For menu, panel and shortcut details, see [Discovering the interface](interface.md). For creation procedures, use the specialised chapters listed in the [index](overview.md).
