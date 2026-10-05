# Empty avatar

`emptyAvatar` creates a body with no contact shape defined by default. Then add one or more contactors in the **Contactors** tab. The former independent “Empty Avatar” tab no longer exists.

## Create the empty body

1. Create the material and model compatible with the project dimension.
2. Open **Avatars** (`Ctrl+3`).
3. Choose `emptyAvatar` in **Type**.
4. Set its centre X/Y and, in 3D, Z.
5. Choose **Material** and **Model**, then set **Color**.
6. Click **Add**.

An empty avatar has no extra geometric field under **Type parameters**.
Without a contactor, it has no contact geometry to draw. `visuAvatars`
then ignores it; the log reports how many avatars were skipped. Add at
least one contactor to see its shape in the native viewer.

## Add its contactors

1. Open **Tabs → Open → Contactors**.
2. Select the empty avatar in **Select avatar**.
3. Choose a proposed shape in **Shape**. The list is filtered by body type and dimension.
4. Fill the geometric parameters shown for that shape (e.g. **byrd** for the radius of `DISKx`, or **axe1/axe2** for `JONCx`). The **shift** field offsets the contactor from the avatar centre; it takes two coordinates in 2D and three in 3D.
   For `POLYG` and `POLYR`, choose **generation_type**: **regular** asks for the number of vertices and the radius; **full** asks for the vertices, and for `POLYR` also the triangular face connectivity. Vertices of a complete `POLYG` must be given counter-clockwise.
5. Fill **Color**. Use a 5-character code consistent with the visibility tables to create.
6. For a meshed body, optionally set **Group** to limit the contactor to an element group.
7. Click **Add contactor** and check the added row.
8. To remove a shape, select it and click **Remove selected**.

After adding or removing, click **Refresh scene** in the 3D viewer.
The **pre.visuAvatars** button also rebuilds pylmgc90 bodies from the project;
a contactor without its required dimensions is not created.

# Mesh avatar

You can create a deformable avatar for rigid/deformable interaction. To do so, choose the **mesh** element.

### 2D deformable body — `mesh_shapes_2d`

These shapes are meant to be added on a 2D FEM mesh. They define surface contactors for rigid-deformable interactions.

| Shape | Description | Usage |
|-------|-------------|-------|
| `ALpxx` | Line contactor for 2D FEM masonry | `ALpMECAx` interactions (CLALp / MECAx) |
| `CLxx` | Continuous 2D line contactor | `DKMECAx` interactions (disk / MECAx) |
| `DISKL` | Disk on a 2D FEM node | Disk-disk interaction on mesh |
| `PT2TL` | 2D transmission point | FEM node-node coupling |

### 3D deformable body — `mesh_shapes_3d`

| Shape | Description | Usage |
|-------|-------------|-------|
| `ASpxx` | Surface contactor for 3D FEM spheres | `SPMECAx` interactions (sphere / MECAx 3D) |
| `CSpxx` | Continuous 3D surface contactor | Generic 3D rigid-deformable interactions |
| `PT3Dx` | 3D FEM point node | 3D FEM node-node coupling |

---

> **Note:** The same avatar may carry several contactors of distinct colours or shapes. Each shape/colour pair used in an interaction must be correctly reflected in **Visibility**.

## Configure contact

1. Create a law in **Contact**.
2. In **Visibility**, choose the body, shape and colour of the contactor as candidate or antagonist.
3. Associate the law and an **Alert** distance suited to the scene scale.
4. Click **Add**, then **Verify** to find colours without a table or unreferenced laws.


---

See [Contactors](contactors.md), [Contact laws](contact_laws.md) and [Visibility tables](visibility.md) for the corresponding forms.
