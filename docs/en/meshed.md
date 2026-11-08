# Deformable body wizard

**Tools → Deformable mesh wizard…** (`Ctrl+Shift+D`) creates a meshed avatar with its model and material. Assign contactors and boundary groups as offered, then complete Contact, Visibility, DOF and Compute configuration.

## Geometry and generated meshes

The 2D rectangle and H8 box use pylmgc90's structured mesh builders. The 2D disk, 3D sphere and 3D cylinder are generated with the **gmsh** geometry API and then read by pylmgc90. The Python `gmsh` package must be installed in the environment that prepares the DATBOX or runs `pre.py`. These primitives produce unstructured meshes (triangles in 2D and tetrahedra in 3D); choose a compatible finite-element model.

External `.brep`, `.step`, `.iges` and `.geo` geometry files are also meshed with gmsh during materialization. Existing mesh files (`.msh`, `.vtk`, `.vtu`, `.mesh`) are read directly. The project stores the primitive geometry and its parameters, and the generated `pre.py` recreates gmsh primitive meshes when run.

**Browse…** stores a file path; it does not preview the imported mesh. Inspect the avatar in the project and verify it during calculation preparation.
