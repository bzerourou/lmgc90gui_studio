# Deformable body assistant

The **Deformable mesh** assistant guides creation of a meshed body and its edge contactors. It is available from **Tools → Deformable mesh assistant…** (`Ctrl+Shift+D`) or the **Deformable** tab.

## Open the assistant

1. Open **Deformable** from **Tabs → Open** and click **Open MeshWizard assistant…**, or choose the command in **Tools**.
2. Read the introduction then click **Next**. **Back** returns to the previous page; **Cancel** closes the assistant.

![](../captures/defor_page1.png)

## Page walkthrough

1. **Dimension**: select 2D or 3D consistent with the project. If avatars or models already exist, their dimension must stay consistent.

![](../captures/defor_page2.png)

2. **Material**: create an elastic material among the proposed types, or choose an existing material of the same use. For `ELAS`, the anisotropy choice (`isotropic` / `orthotropic`) adapts displayed parameters: `young`, `nu` and `G` for isotropic; `E1`, `E2`, `ν12` and `G12` for 2D orthotropic; the additional 3-direction constants (`E3`, `ν13`, `ν23`, `G13`, `G23`) for 3D orthotropic. Only applicable constants are stored.

![](../captures/defor_page3.png)

3. **FE model**: create a model or reuse a dimension-compatible model. If creating one, choose physics, element and proposed options (anisotropy, kinematics, formulation and mass storage).

![](../captures/defor_page4.png)

4. **Geometry**: choose an available shape:
   - in 2D: **Rectangle**, **Disk**, **External file**;
   - in 3D: **Box (H8)**, **Sphere**, **Cylinder**, **External file**.

![](../captures/defor_page5.png)

5. Fill centre and dimensions, radius or height required by the geometry.
6. For **External file**, click **Browse…** then choose a format shown in the selector, such as `.msh`, `.vtk`, `.brep`, `.step`, `.iges` or `.geo`.
7. **Refinement**: choose the proposed mesh type then set active subdivisions: `nx`, `ny`, `nz`, `nr`, `ntheta` or `nphi`. Higher values give more elements and may increase computation cost.

![](../captures/defor_page6.png)

8. **Edge contactors**: keep **Add an edge contactor** if the body must interact. Choose its shape compatible with the dimension and its colour. **by group** is optional.
![](../captures/defor_page7.png)

9. **Summary**: check dimension, material, model, geometry, refinement and contactors.
![](../captures/defor_page8.png)

10. Click **Generate mesh**. The assistant confirms creation or shows the error to fix.

## Shapes and mesh actually produced

The 2D rectangle uses the structured construction available in the application. For other geometries and external files, the assistant stores the mesh intent and its parameters in the project; full generation/materialisation depends on export and LMGC90 tools present in the environment.

The **Browse…** button records a path: it is not a preview of the imported mesh. After avatar generation, check the result in the project and when preparing the computation.

## After the assistant

- The deformable avatar appears in **Avatars**.
- Contactors can be checked or modified in **Contactors**.
- The law and interaction pairs are configured in **Contact** and **Visibility**.
- To apply conditions, use **DOF**.

See also [Contactors](contactors.md), [Visibility tables](visibility.md) and [Boundary conditions](dof.md).
