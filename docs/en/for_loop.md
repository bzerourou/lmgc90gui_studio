# Parametric generation with ForLoop

The **ForLoop** tab repeats an operation from a value range and expressions. Unlike **Loops**, which places avatar clones according to a geometric shape, ForLoop accepts different targets: avatars, materials, models, DOF operations, visibility tables, granulometric deposits or radius distributions.

![](../captures/for_loops.png)

## Prepare the loop

1. Create the base objects the target depends on. For example, an avatar loop needs a template avatar; a material loop needs an existing material.
2. Open **Tabs → Open → ForLoop**.
3. Choose **Loop target**.
4. Fill **Variable**. The name `i` is proposed by default; form expressions may use this variable.
5. Enter **start**, **stop (exclusive)** and **step**.
6. Select **Template** when the target type requires it.
7. Complete only the expressions corresponding to the target. Unused fields are disabled.
8. Click **Apply loop**. The application shows the number of elements produced or a message indicating an invalid value.

`stop` is exclusive. With `start=0`, `stop=5` and `step=1`, the variable runs through `0, 1, 2, 3, 4`: five repetitions.

## Delete a loop

Select the loop in the list, then click **Delete selected loop** and confirm. The loop and the elements it generated are deleted, without touching other project objects. Deletion can be undone or redone with **Undo** and **Redo**.

## Targets and expressions

| Target | Required template | Proposed variable fields |
|---|---|---|
| `avatar` | Template avatar | `expr X`, `expr Y`, `expr Z`, `expr radius` |
| `material` | Template material | `expr density (material)` |
| `model` | Template model | Copy of the selected model according to the range |
| `dof` | Existing DOF operation | Parameters of the selected operation |
| `visibility` | Existing see-table | `expr alert (see)` |
| `granulo` | Granulometric configuration, or Granulo tab parameters | `expr N`, `expr rmin`, `expr rmax` |
| `granulo_dist` | Granulometric configuration, or default values | `expr N`, `expr rmin`, `expr rmax` |

Fields use safe numeric expressions. A series may for example place avatars with `expr X = i * 0.1` and `expr Y = 0.0`. For an avatar, also choose a **Group** to gather creations if needed.

## Setup examples

### Avatar row

1. Choose target `avatar`.
2. Select the avatar to clone in **Template**.
3. Set `start=0`, `stop=10`, `step=1`.
4. Enter `i * 0.2` for `expr X`, `0.0` for `expr Y`, and `0.0` for `expr Z` in 3D.
5. Give a group name, e.g. `line1`.
6. Click **Apply loop** and check that 10 avatars were created.

### Material series with variable density

1. Choose target `material` and a template material.
2. Set the iteration range.
3. Enter a density expression such as `2500 + 100*i`.
4. Apply the loop and check names and densities in **Materials**.

### Radius distribution

1. Choose `granulo_dist` to produce a distribution alone, or `granulo` to create a population.
2. Set the range and expressions for particle count and radii.
3. Apply the loop; check the result in **Granulo** and in the viewer after refresh.

## Checks and precautions

- Ensure `step` is not zero and that the range direction is consistent.
- Since `stop` is exclusive, check the number of iterations before a large generation.
- Expressions depending on `i` must produce valid values for each iteration.
- The application adds results to the project; a new run does not replace previous creations.
- A target that depends on a template cannot be applied if no appropriate element is selected.

For strictly geometric arrangements (circle, grid, line, spiral), see [Geometric loops](loops.md).
