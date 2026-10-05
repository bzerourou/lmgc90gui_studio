# Contactors

Contactors define the shapes through which an avatar takes part in contact detection. They are distinct from the main geometry, the contact law and the visibility table: for usable contact, check all three.

![](../captures/contactors.png)

## Add a contactor

1. First create the avatar in **Avatars**. An empty or meshed avatar is a common case, but rigid bodies can also receive additional compatible contactors.
2. Open **Tabs → Open → Contactors**.
3. In **Select avatar**, choose the body to modify.
4. In **Shape**, choose one of the offered shapes. The list depends on the avatar type and project dimension; do not use a contactor from another dimension.
5. Enter **Color**. The colour code identifies the contactor in visibility tables; use the same code in both places.
6. For a meshed body, optionally fill **by group** to limit the contactor to a node or face group.
7. Click **Add contactor**. The new shape appears under **Contactors on avatar**.
8. Repeat the steps to add several contactors if the model needs them.

## Remove a contactor

1. Select its row under **Contactors on avatar**.
2. Click **Remove selected**.

This removes the contactor definition from the selected avatar; it does not delete the avatar.

## Common shape families

| Body / dimension | Often proposed contactors |
|---|---|
| Rigid 2D | `DISKx`, `xKSID`, `JONCx`, `POLYG`, `PT2Dx` |
| Rigid 3D | `SPHER`, `PLANx`, `CYLND`, `POLYR`, `PT3Dx` |
| Meshed 2D | `CLxxx`, `ALpxx`, `PT2Dx` |
| Meshed 3D | `CSpxx`, `ASpxx`, `PT3Dx` |

## Parameter details by shape

### DISKx / xKSID / SPHER — Disk, discrete disk, sphere

```
byrd=0.3
```

| Parameter | Description |
|-----------|-------------|
| `byrd` | Contactor radius (m). Corresponds to the contact radius used in detectors. |

---

### JONCx — Rod / 2D ellipse

```
axe1=1.0, axe2=0.1
```

| Parameter | Description |
|-----------|-------------|
| `axe1` | Major semi-axis (m) — long axis of the ellipse. |
| `axe2` | Minor semi-axis (m) — short axis of the ellipse. |

---

### POLYG — 2D polygon

```
nb_vertices=4, vertices=[[-1.,-1.],[1.,-1.],[1.,1.],[-1.,1.]]
```

| Parameter | Description |
|-----------|-------------|
| `nb_vertices` | Number of polygon vertices. |
| `vertices` | List of local vertex coordinates `[[x1,y1],[x2,y2],…]`. Coordinates are relative to the body centre. Vertices must be in trigonometric (counter-clockwise) order. |

---

### PLANx — 3D plane

```
axe1=1.0, axe2=1.0, axe3=0.1
```

| Parameter | Description |
|-----------|-------------|
| `axe1` | Size along the first plane axis (m). |
| `axe2` | Size along the second plane axis (m). |
| `axe3` | Plane thickness (m) — used for inertial property computation. |

---

### CYLND / DNLYC — 3D cylinder

```
byrd=0.5, High=1.0
```

| Parameter | Description |
|-----------|-------------|
| `byrd` | Cylinder radius (m). |
| `High` | Height (axial length) of the cylinder (m). Note the capital H. |

---

### POLYR — 3D polyhedron

```
nb_vertices=8, vertices=[[-1.,-1.,-1.],[1.,-1.,-1.],[1.,1.,-1.],[-1.,1.,-1.],
                          [-1.,-1.,1.],[1.,-1.,1.],[1.,1.,1.],[-1.,1.,1.]]
```

| Parameter | Description |
|-----------|-------------|
| `nb_vertices` | Number of polyhedron vertices. |
| `vertices` | List of 3D coordinates of each vertex `[[x,y,z],…]`. Local coordinates relative to the centre. |

> For a convex polyhedron, vertices may be given in any order — pylmgc90 computes the convex hull. For a non-convex polyhedron, face order must be consistent.

---

### PT2Dx / PT3Dx — Point nodes

No parameters. These contactors represent a contact point at a node.

```
(empty Params field)
```

---


The effective list is computed by the application according to the avatar. It may be shorter than this table. Shapes also depend on the intended role: grain contactors are often candidates, while a wall often acts as antagonist.

## Link the contactor to interactions

After creating the contactor:

1. Check its colour and shape in **Contactors**.
2. Open **Contact** and create the appropriate law if it does not exist yet.
3. Open **Visibility**. Select the matching body, contactor and colour in the candidate/antagonist fields.
4. Choose the created law and set the **Alert** distance.
5. Click **Add**, then **Verify** to spot colours or laws that are not associated.

Colours and shapes actually present are suggested in **Visibility**. If the chosen combination does not exist on a project avatar, the application asks for confirmation before saving the table.
