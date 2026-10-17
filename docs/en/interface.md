# Discover the graphical interface

LMGC90_GUI Studio is a modern graphical interface designed to make it easier to build numerical models with the **pre** (pre-processor) module of **LMGC90**.

You can also configure and run computations directly from LMGC90_GUI Studio through the **chipy** module.

The interface is organised clearly and ergonomically to support the user from start to finish of the modelling process: creating elements, boundary conditions, post-processing, file generation and finally running computations.

The following video gives an overview of the different parts of the interface.

[![Introduction LMGC90_GUI Studio](https://img.youtube.com/vi/2lVIGg3VboA/0.jpg)](https://www.youtube.com/watch?v=WSS62MTns1w)


## Main window

![Global view of the interface](../captures/interface_sections.png)

The interface is divided into **six main areas**:

1. **Menu**
2. **Toolbar** (top)
3. **Model tree** (left)
4. **Creation tabs** (centre)
5. **Command history** (right)
6. **Status bar** (bottom)

The **command palette** is available from the **toolbar** or with the keyboard shortcut `Ctrl+K`.

![Command palette](../captures/palette_commandes.png)


---

## 1. Menu

### 1.1 File

| Action | Shortcut | Description |
|--------|----------|-------------|
| **New** | `Ctrl+N` | Creates a new project. A dialog asks for the dimension and the project name. |
| **Open** | `Ctrl+O` | Opens an existing project. A dialog lets you browse to the project `.lmgc90` file. |
| **Save** | `Ctrl+S` | Saves the current project at its current location. |
| **Save as…** | `Ctrl+Shift+S` | Saves the project under a new name or in a new location. |
| **Quit** | `Ctrl+Q` | Closes the application. |

**New project**

Click the **New** button on the toolbar, use **File → New**, or press `Ctrl+N`. A dialog opens to set the dimension then the project name.

  ![](../captures/titre_projet.png)

**Open a project**

Click the **Open** button on the toolbar, use **File → Open**, or press `Ctrl+O`. Then specify the path and name of your project.

  ![](../captures/ouvrir_projet.png)

**Save**

Saves your projects to disk: click **Save** on the toolbar, use **File → Save**, or the keyboard shortcut `Ctrl+S`.

  ![](../captures/save_projet.png)

---

#### 1.2 Project

**Set dimension**

To keep the same dimension throughout your project, use **Project → Set dimension…**.

![](../captures/dimension.png)

#### 1.3 Edit

| Action | Shortcut | Description |
|--------|----------|-------------|
| **Undo** | `Ctrl+Z` | Undo an action. |
| **Redo** | `Ctrl+Y` | Redo the undone action. |

#### 1.4 Tools

| Action | Shortcut | Description |
|--------|----------|-------------|
| **Generate pre.py** | — | Generates your model script (`pre.py`). |
| **Generate command.py** | — | Generates your computation script (`command.py`). |
| **Export all** | — | Exports model/computation scripts and DATBOX. |
| **Pipeline** | — | Generates an sbatch script for an HPC machine. |
| **Deformable wizard** | `Ctrl+Shift+D` | Guides creation or import of deformable elements (rectangle, disk, sphere, cylinder meshes or external `.msh` / `.geo` files, etc.). |
| **Masonry wizard** | `Ctrl+Shift+M` | Specialised in building 2D and 3D brick stacks (`brick2D` / `brick3D`) with various bonds (standard, running bond, single paneresse, double paneresse, etc.). |
| **Dynamic variables** | `Ctrl+V` | Opens a dialog to define reusable variables in numeric fields of the interface (radius, spacing, offset, etc.). It is also an inspection window for LMGC90 objects present in memory. See [Dynamic variables](dynam_variables.md). |
| **visuAvatars (pylmgc90)** | — | Visualises your model with the native LMGC90 function `visuAvatars`. |
| **Preferences** | `Ctrl+,` | Opens the application configuration dialog. See section [Preferences](#preferences). |

> **Note:** wizards can be run again at any time during the session. Each run **adds** the generated elements to the existing project without clearing what was created before.
> Duplicating elements that share the same name causes errors — use different names for your elements.

---

#### 1.5 Computation

| Action | Shortcut | Description |
|--------|----------|-------------|
| **Generate DATBOX and scripts** | `Ctrl+F5` | Generates DATBOX and the model/computation scripts. |
| **Run computation** | `F5` | Opens the Compute tab and runs the chipy computation directly from the interface, in a separate process so the UI is not blocked. |
| **Application journal** | `F7` | Shows the internal LMGC90_GUI Studio journal: unhandled errors, Python warnings, failed pylmgc90 calls. Useful to diagnose problems that do not show a visible message in the interface. |

![](../captures/journal.png)

---

#### 1.6 Tabs

| Action | Shortcut | Description |
|--------|----------|-------------|
| **Open** | — | Opens a specific tab from the full list. See section [Creation tabs](#4-creation-tabs-central-area). |
| **Close others** | — | Closes all open tabs except the active one. |
| **Close all (except essential)** | — | Closes all non-essential tabs. |
| **Default tabs** | `Ctrl+Alt+D` | Restores the default tab layout. |

---

#### 1.7 Examples

This menu has a single action, **Example library**, which opens a dialog where you can browse several examples under seven categories. Selecting an example loads its details in the right-hand pane.

![](../captures/biblio_exemples.png)

To load an example, select it and click **Load**. A further dialog lets you **replace**, **add to the project** (which may create duplicate elements) or **cancel**.

![](../captures/exemple_capture.png)

---

#### 1.8 Help

| Action | Description |
|--------|-------------|
| **Command palette** | Opens the command palette. |
| **About** | Shows LMGC90_GUI Studio version information and dependencies. |
| **Online help** | Opens the online documentation in the default browser. |

---

### 2. Toolbar

The toolbar groups the most frequent actions for quick access:

![](../captures/barre_outils.png)

| Button | Menu equivalent |
|--------|-----------------|
| **New** | File → New |
| **Open** | File → Open |
| **Run computation** | Computation → Run computation |
| **Save** | File → Save |
| **Generate DATBOX/scripts** | Computation → Generate DATBOX/scripts |
| **Dynamic variables** | Tools → Dynamic variables |
| **Command palette** | Help → Command palette |

---

### 3. Model tree (left)

Fixed area showing the **model tree**. It updates automatically after each creation, modification or deletion of an element.

![](../captures/model_tree.png)

#### Displayed sections

| Section | Content |
|---------|----------|
| **Materials** | List of all materials defined in the project. |
| **Models** | List of all finite-element models (physics, element, dimension). |
| **Avatars (AOS)** | List of all bodies in the project: rigid, empty, deformable, Loop, ForLoop, etc. |
| **Avatar population (SOA)** | Lists granulometry or wizard populations. |
| **Contact laws** | Contact behaviour laws defined (friction, cohesion, stiffness). |
| **Visibility tables** | Visibility rules between avatars during the computation. |
| **DOF** | Boundary conditions on avatars or avatar groups. |
| **Groups** | List of avatar groups. |

---

### 4. Creation tabs (central area)

Main work area. Each tab is dedicated to a modelling step. To open a tab, use **Tabs → Open** and choose the desired tab.

![](../captures/onglets.png)

| Tab | Shortcut | Description |
|-----|----------|-------------|
| **Materials** | `Ctrl+1` | Create and manage materials (RIGID, ELAS, ELAS_PLAS, THERMO_ELAS, PORO_ELAS, etc.). |
| **Models** | `Ctrl+2` | Define physical and finite-element models (MECAx, THERx, POROx, MULTI). |
| **Avatars** | `Ctrl+3` | Create standard rigid bodies: disk, jonc, polygon, rough wall, sphere, cylinder, polyhedron, etc. |
| **Loops** | `Ctrl+4` | Parametric generation of avatar series: circle, grid, line, spiral or manual placement. |
| **ForLoop** | `Ctrl+5` | Create For loops on your elements: materials, models, avatars, DOF, etc. |
| **Granulometry** | `Ctrl+6` | Generate deposits with statistical radius distribution and gravity deposition. |
| **Contact** | `Ctrl+7` | Define contact behaviour laws (Coulomb friction, cohesion, normal and tangential stiffness). |
| **Visibility** | `Ctrl+8` | Create visibility tables that govern how avatars interact during the computation. |
| **DOF** | `Ctrl+9` | Boundary conditions: imposed translations, locked rotations, imposed velocities, DOF couplings. |
| **Post-pro** | — | Configure post-processing commands: energy balance, body tracking, field extraction. |
| **3D Visualisation** | — | Interactive display of model avatars with navigation, selection and measurement modes. |
| **Groups** | — | Configure avatar groups. |
| **Contactors** | — | Add/remove contactors on your avatars. |
| **Deformable wizard** | — | Wizard for creating/importing deformable elements. |
| **Masonry wizard** | — | Wizard for creating and configuring masonry elements. |

> **Keyboard shortcuts:** keys `Ctrl+1` to `Ctrl+9` open the first nine tabs in the list directly.

---

### 5. Command history area (right)

Area dedicated to managing the command history.

![](../captures/historique.png)

---

### 6. Status bar (bottom)

Horizontal strip at the bottom of the window showing contextual messages about ongoing operations: avatar creation, script generation, result of a measurement in the 3D viewer, validation error, etc.

![](../captures/barre_etat.png)

---

### Interactive modes of the 3D viewer

| Mode | Description |
|------|-------------|
| **Navigation** | Default mode: rotate (left-click + drag), zoom (wheel), pan (right-click + drag). |
| **Selection** | Click an avatar to highlight it (yellow outline) and show its information in the status bar. |
| **Ruler** | Distance measurement: click a first point (A) then a second point (B) to display the distance in metres. |

Quick views **XY**, **XZ**, **YZ** and **Iso** are available from the viewer toolbar.

---

### Preferences

Accessible via **Tools → Preferences** or the shortcut `Ctrl+,`. The preferences dialog groups application configuration parameters.

![](../captures/preferences.png)

| Parameter | Description |
|-----------|-------------|
| **Computation** | Default computation values. |
| **Paths** | Default path used when opening and saving projects. |
| **Save** | Options to enable automatic save at regular intervals and on application close. |
| **Performance** | Enable or disable display of avatars in the model tree and in the Avatar tab table. |

---

## Keyboard shortcut summary

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New project |
| `Ctrl+O` | Open a project |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save as… |
| `Ctrl+Q` | Quit |
| `Ctrl+Shift+N` | Project configuration wizard |
| `Ctrl+Shift+G` | pylmgc90 granulometry wizard |
| `Ctrl+Shift+D` | Deformable wizard |
| `Ctrl+Shift+M` | Masonry wizard |
| `Ctrl+V` | Dynamic variables |
| `Ctrl+,` | Preferences |
| `Ctrl+F5` | Generate DATBOX / scripts |
| `F5` | Run computation |
| `F6` | View LMGC90 logs |
| `F7` | Application journal |
| `Ctrl+Alt+D` | Default tabs |
| `Ctrl+1` … `Ctrl+9` | Open the corresponding tab |
| `Ctrl+K` | Open the command palette |

---

LMGC90_GUI Studio is designed to be **intuitive** and **fully visual**, while remaining fully compatible with traditional LMGC90 Python scripts.

For specific operations, see the chapters in the [index](overview.md).
