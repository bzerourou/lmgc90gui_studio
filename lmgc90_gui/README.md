# lmgc90_gui

PyQt6 client of **`lmgc90_core.Project`** + **`lmgc90_engine.EngineSession`**.

```
Views (PyQt6)
    │  signals
    ▼
ProjectController          ← thin Qt façade
    │
    ├── project: Project           (lmgc90_core — pure, undoable)
    └── session: EngineSession     (lmgc90_engine — materialize / DATBOX)
```

The controller **does not** own `_pylmgc_bodies` lists. Identity is always
`avatar_id` / `population_id`. Live Fortran objects live only inside the session
after `materialize()`.

## Install

```bash
pip install -e ../lmgc90_core
pip install -e ../lmgc90_engine
pip install -e .[qt]          # GUI
# optional:
pip install -e .[viz]         # + pyvista viewer
```

## Run

```bash
lmgc90-gui
# or
python -m lmgc90_gui
```

Headless / notebook:

```python
from lmgc90_gui.controller import ProjectController

ctrl = ProjectController()
ctrl.new_project("demo", dimension=2)
# ctrl.project is a full lmgc90_core.Project
# ctrl.session is an EngineSession
```

## Package layout

```
lmgc90_gui/
├── main.py
├── src/lmgc90_gui/
│   ├── app.py                 entry + QApplication
│   ├── controller/
│   │   ├── project_controller.py
│   │   └── signals.py         Qt signals or no-op stubs
│   ├── views/
│   │   ├── main_window.py
│   │   ├── tree_view.py
│   │   └── tabs/
│   ├── dialogs/
│   ├── workers/
│   └── utils/
├── tests/
└── examples/
```

## Rules

- No business logic in tabs: tabs call `controller.*` only.
- No `from pylmgc90 import pre` in the GUI package — engine owns that.
- `state_changed` is the only refresh trigger for views.
- Batch: `with controller.batch(): ...` → single signal at exit.
