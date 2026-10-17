# Create, open and organise a project

A project gathers materials, models, avatars, contacts, visibility rules, DOF and computation settings. It is stored in a `.lmgc90` file.

## Create a project

1. Choose **File → New** (`Ctrl+N`) or the **New** toolbar button.
2. Set the dimension (`2` or `3`) and the project name.

![](../captures/titre_projet.png)

3. Confirm. The main window shows an empty scene ready for modelling.

## Open and save

| Action | Shortcut | Description |
|---|---|---|
| **Open** | `Ctrl+O` | Open an existing `.lmgc90` project |
| **Save** | `Ctrl+S` | Save the current project in place |
| **Save as…** | `Ctrl+Shift+S` | Save under a new name or location |

![](../captures/ouvrir_projet.png)

![](../captures/save_projet.png)

Save before running a computation and before loading an example in replace mode.

## Choose and change dimension

1. Set `2` or `3` at creation time.
2. To change later, choose **Project → Set dimension…**.

![](../captures/dimension.png)

3. Select the new dimension and read the warning if existing models no longer match.
4. Confirm only after checking models and avatars. Changing dimension does not automatically convert existing objects.

## First modelling sequence

1. Create a material in **Materials**.
2. Create a model in **Models**.
3. Create bodies in **Avatars**, or use **Granulo**.
4. Create parametric and formal loops as needed.
5. Define contact laws in **Contact**, then associations in **Visibility**.
6. Add **DOF** and **Groups** if useful.
7. Save, configure **Compute**, then run.

![](../captures/onglets_list.png)

Wizards: **Deformable mesh** (`Ctrl+Shift+D`), **Masonry** (`Ctrl+Shift+M`) from **Tools**.

## Tab organisation

Use **Tabs → Open** to show a function. Shortcuts `Ctrl+1`…`Ctrl+9`: Materials, Models, Avatars, Loops, ForLoop, Granulo, Contact, Visibility, DOF. **Tabs → Default tabs** (`Ctrl+Alt+D`) restores the layout.

See [Discover the interface](interface.md) and the [index](overview.md).
