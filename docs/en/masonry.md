# Masonry assistant

The **Masonry** assistant builds an assembly of polygonal bricks and can create the associated group, contact law and visibility table. Open it from **Tools → Masonry assistant…** (`Ctrl+Shift+M`) or from the **Masonry** tab.

![](../captures/maçon_page1.png)

## Follow the assistant

1. On **Introduction**, click **Next**.
2. **Dimension**: choose 2D or 3D. Stretcher patterns are reserved for 3D.

![](../captures/maçon_page2.png)

3. **Material**: create a `RIGID` material with its density or select an existing material.
![](../captures/maçon_page3.png)

4. **Model**: create a rigid model or reuse one of compatible dimension (`Rxx2D` in 2D, `Rxx3D` in 3D).
![](../captures/maçon_page4.png)

5. **Brick dimensions**: enter the name (maximum five characters), `lx`, `ly` and depth `lz` in 3D.
![](../captures/maçon_page5.png)

6. **Bond and layout**: choose the pattern, courses, columns, joint width, offsets and colour.
7. Choose whether to register a **group** and set its name.
8. The option **Add IQS_CLB law + see-table** is checked by default. Adjust the law name and friction, or uncheck it if you will configure interactions yourself.
9. **Transformations**: enable **Global translation** and fill `tx`, `ty`, `tz` if needed. To duplicate the assembly, enable **Additional copies**, enter the number of copies and their offset `dx`, `dy`, `dz`.
![](../captures/maçon_page6.png)

10. **Summary and generation**: check dimensions, material, model, pattern, assembly size, group, law and transformations.
11. Click **Generate**. A confirmation shows the number of bricks created.
![](../captures/maçon_page7.png)

The **Back**, **Next** and **Cancel** buttons let you navigate the assistant before final confirmation.

## Available patterns

| Pattern | General layout |
|---|---|
| `Standard` | Half-brick offset on alternating courses; option for half-bricks at ends. |
| `Running Bond` | Progressive joint offset between courses. |
| `Stack Bond` | Joints aligned vertically. |
| `Flemish Bond` | Alternating stretchers and headers. |
| `Single stretcher (pylmgc90)` | Specialised 3D bond, options in the stretcher group. |
| `Double stretcher (pylmgc90)` | Two 3D leaves, options in the stretcher group. |

Pattern-specific choices appear at the layout step: stretcher layout, first brick, length mode and no half-bricks option.

## Limits and result

- Pure rotation is not applied in the current version; the interface states this at the **Transformations** step.
- A new generation adds bricks to the project and does not replace previous ones.
- If the assistant creates the law and see-table, check the colour and contactor used in **Visibility** after generation.
- Bricks are project avatars. You can inspect the group in **Groups** and refresh the scene in **3D Visualisation**.
