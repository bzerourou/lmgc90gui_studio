# Geometric avatar loops

The **Loops** tab clones a template avatar and distributes its copies according to a regular geometry. These loops are distinct from the multi-target parametric loops of the [ForLoop](for_loop.md) tab.

![](../captures/loops.png)

## Prepare the template

1. Create an avatar in **Avatars** with its material, model, colour and geometric parameters.
2. Check its initial position: it is the basis for cloning.
3. Open **Tabs → Open → Loops** (`Ctrl+4`).

## Define the generation

1. Choose **Type**: `circle`, `grid`, `line` or `spiral`.
2. Choose **Template avatar**.
3. Set **Count**, the number of copies to create.
4. Fill the fields suited to the pattern:
   - `circle`: **Radius** sets the placement radius; also use offsets to move the layout centre;
   - `grid`: **Step** sets the spacing; offsets move the grid;
   - `line`: **Step** sets the spacing; **Invert axis (line)** reverses the line orientation;
   - `spiral`: **Radius** and **Spiral factor** set the opening and progression, with position offsets.
5. In 3D, fill the required X, Y and Z offsets; in 2D, the Z offset has no geometric effect.
6. Fill **Group** to register generated avatars in a group.
7. Click **Apply loop**.
8. Read the confirmation of the number of bodies created and check the result in **Avatars** or the 3D viewer after **Refresh scene**.

## Delete a loop

Select the loop in the list, then click **Delete selected loop** and confirm. The loop and the avatars it generated are removed; other project avatars stay in place. This action can be undone or redone with **Undo** and **Redo**.

## Result and repetition

Each copy is added to the project as an independent avatar. Applying a loop again adds a new series; it does not replace the previous generation. Give a distinct group name if you need to distinguish several series.

Geometric loops do not directly change the physical properties of the template. To vary materials, models, DOF, visibility or granulometric parameters with an iteration expression, use **ForLoop**.
