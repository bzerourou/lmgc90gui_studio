# Example library

The example library provides demonstration scenes that can be loaded into a
project. The available entries, descriptions, dimensions, and categories are
shown by the application; the list changes as examples are added.

## Load an example

1. Open the example library from the **Examples** menu.
2. Select an entry to review its description and dimension, then choose
   **Load**.
3. Choose whether to replace the current project or append the scene.
4. Inspect the resulting project and save it if you want to keep your work.

**Replace** creates a new project for the example. Confirm any unsaved-work
prompt before proceeding. **Append to project** keeps the current project and
its command history; the example must have the same dimension as the current
project. Appending uses the merge conflict policy, so inspect names and groups
afterward.

## How the catalogue is implemented

Scene geometry and project construction belong to `lmgc90_core`, not to a
dialog or widget. A scene builder is a callable with the shape
`Callable[[Project], None]`; it uses core entities and APIs and does not
construct pylmgc90 or Qt objects.

The core registry `lmgc90_core.scenes.SCENE_BUILDERS` maps scene IDs to
builders. The GUI registry `lmgc90_gui.examples.EXAMPLES` contains
`ExampleSpec` metadata (ID, title, category, description, dimension,
difficulty, tags) and a reference to the builder. The GUI checks that each
metadata entry points to the builder registered under the same ID.

When adding an example:

1. Implement and export the builder in `lmgc90_core/scenes/`, then register
   its ID in `SCENE_BUILDERS`.
2. Add the corresponding `ExampleSpec` in `lmgc90_gui/examples/`.
3. Keep the metadata ID and builder registration identical.
4. Add or update focused scene/export tests.

`ProjectController.apply_scene` runs the builder against a `Project`. It
resolves pending granulo configurations and notifies the GUI afterward. The
replace/append decision is made by the loading UI, not by the scene builder.
