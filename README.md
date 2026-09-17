# LMGC90 GUI Studio

Monorepo to build, visualise and export **LMGC90** scenes (DEM / contact) with a decoupled architecture:

| Package | Role | Heavy dependencies |
|---------|------|--------------------|
| **`lmgc90_core`** | Pure data model (materials, models, avatars, laws, loops, granulo SoA, masonry) + `pre.py` script generation | **none** (Python + NumPy) |
| **`lmgc90_engine`** | Bridge to **pylmgc90**: live materialisation, DATBOX, `pre.visuAvatars`, workers | **pylmgc90 optional** |
| **`lmgc90_gui`** | **PyQt6** client (MVC): CRUD tabs, wizards, Viewer3D, journal, compute | Qt; PyVista optional |

You can **install core only**, build a dataset (`.lmgc90` project / scripts), then add engine + GUI later — without rewriting the scene.

```
lmgc90gui_studio/
├── lmgc90_core/          # pure scientific core
├── lmgc90_engine/        # pylmgc90 bridge
├── lmgc90_gui/           # Qt interface
├── examples/             # demo scenes (if present)
├── docs/                 # notes / documented examples
├── install.ps1           # quick Windows install
├── pyproject.toml        # meta (does not replace the 3 packages)
└── README.md             # this file
```

---

## Architecture

```text
                    ┌─────────────────────────────────────┐
                    │           lmgc90_gui (Qt)           │
                    │  ProjectController · tabs · UI      │
                    └───────────────┬─────────────────────┘
                                    │
                    ┌───────────────▼─────────────────────┐
                    │         lmgc90_engine               │
                    │  EngineSession · materialize        │
                    │  writeDatbox · visuAvatars          │
                    └───────────────┬─────────────────────┘
                                    │  (if pylmgc90 available)
                    ┌───────────────▼─────────────────────┐
                    │         lmgc90_core                 │
                    │  Project · entities · ForLoop       │
                    │  granulo SoA · masonry · emit pre   │
                    └─────────────────────────────────────┘
```

- **Core** is the source of truth: project serialisation, LMGC90 5-char names, dimension, expressions / loops.
- **Engine** does not own the scene; it **materialises** a `Project` into `pylmgc90.pre` objects when the library is importable.
- **GUI** does not store pylmgc bodies in the controller; the engine session holds live objects after `materialize()`.

Without pylmgc90 you still get: project editing, `pre.py` / `command.py` export, **parametric** Viewer3D (PyVista).  
With pylmgc90: real DATBOX, `pre.visuAvatars`, native granulo deposit, etc.

---

## Requirements

- **Python ≥ 3.10**
- **NumPy**
- **Optional GUI**: `PyQt6`
- **Optional 3D viewer**: `pyvista`, `pyvistaqt`
- **Optional LMGC90 compute**: **pylmgc90** (from **source** / **conda** env — not a typical public PyPI package)

---

## Progressive installation (recommended)

### Step A — Core only (data + scripts, headless)

```bash
cd lmgc90gui_studio
pip install -e ./lmgc90_core
```

Minimal example:

```python
from lmgc90_core import pre, Project

p = Project(name="demo", dimension=2)
p.add(pre.material(name="STEEL", materialType="RIGID", density=7800.0))
p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
p.add(pre.rigidDisk(r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL"))

print(p.summary())
```

You can **create and version a dataset** (scene) before installing Qt or pylmgc90.

### Step B — Engine (pylmgc90 bridge)

```bash
pip install -e ./lmgc90_engine
```

- If `import pylmgc90` succeeds → `EngineSession.materialize()`, DATBOX write, `visu_avatars()`.
- Otherwise → script generation still works; live materialisation is disabled.

### Step C — GUI

```bash
pip install -e "./lmgc90_gui[qt]"
# 3D viewer (PyVista):
pip install -e "./lmgc90_gui[viz]"
# or:
pip install pyvista pyvistaqt

lmgc90-gui
```

### Windows (PowerShell) — all at once

```powershell
cd C:\Users\DELL\Documents\lmgc90gui_studio

pip install -e .\lmgc90_core
pip install -e .\lmgc90_engine
pip install -e ".\lmgc90_gui[qt,viz]"
```

Helper script:

```powershell
.\install.ps1
```

> **Important**: a plain `pip install -e .` at the **monorepo root is not enough**. Each subdirectory has its own `pyproject.toml`; install **core**, then **engine**, then **gui**.

---

## pylmgc90 + conda environment

`pylmgc90` is usually built/installed **from source** (or a prepared conda env). It is **not** a required pip dependency of this monorepo.

### Recommended: same conda env for everything

```powershell
conda activate <env_where_pylmgc90_already_works>

# Check
python -c "import pylmgc90; from pylmgc90 import pre; print(pylmgc90.__file__)"

# Install the studio INTO that env
cd C:\path\to\lmgc90gui_studio
pip install -e .\lmgc90_core -e .\lmgc90_engine -e ".\lmgc90_gui[qt,viz]"

python -c "from lmgc90_gui import ProjectController; c=ProjectController(); print('pylmgc:', c.pylmgc_available())"
lmgc90-gui
```

### Install pylmgc90 from source into the GUI’s Python

```powershell
cd C:\path\to\lmgc90_sources   # tree that provides pylmgc90
pip install -e .
python -c "import pylmgc90; print(pylmgc90.__file__)"
```

### Last resort: `PYTHONPATH` to the conda site-packages

```powershell
# Adjust the path
$env:PYTHONPATH = "C:\Users\DELL\miniconda3\envs\<env>\Lib\site-packages;$env:PYTHONPATH"
python -c "import pylmgc90; print(pylmgc90.__file__)"
```

Less robust (native DLLs, version clashes). Prefer the **same conda interpreter**.

### Useful checks

```powershell
where python
python -c "import sys; print(sys.executable)"
python -c "import pylmgc90, lmgc90_core, lmgc90_engine, lmgc90_gui; print('all OK')"
```

In the GUI: **👁 pre.visuAvatars** (materialise then native LMGC90 viewer) when `pylmgc_available()` is true.

---

## Running the GUI

```bash
lmgc90-gui
# equivalent:
python -m lmgc90_gui
```

Main tabs (evolving): Materials, Models, Avatars, Contact, Visibility, DOF, Groups, Contactors, Granulo, Loops, deformable / masonry assistants, **3D Visualisation**, etc.

- **Refresh scene**: parametric PyVista render (manual, for large projects).
- **pre.visuAvatars**: real pylmgc90 bodies (if the library is present).


---

## Tests

```bash
cd lmgc90_core && python -m pytest -q
cd ../lmgc90_engine && python -m pytest -q
cd ../lmgc90_gui && python -m pytest -q
```

**Core / engine** tests stay headless (no Qt / no mandatory pylmgc90 where possible).

---

## Development

1. Fork / clone this repository.
2. Python 3.10+ env (ideally conda if you rely on pylmgc90).
3. Editable install of the three packages (order: core → engine → gui).
4. Prefer PRs scoped by layer (`core`, `engine`, `gui`).

Useful conventions:

- LMGC90 names are often constrained (e.g. 5 characters for some identifiers).
- The GUI must not reintroduce `_pylmgc_*` containers in the controller.
- Scientific geometry lives in **core**; the legacy 3D viewer is ported in `lmgc90_gui/views/viewer_3d.py`.

---

## Quick troubleshooting

| Symptom | Hint |
|---------|------|
| Root `pip install -e .` does not install the apps | Install each sub-package (`lmgc90_core`, …) |
| `No module named 'lmgc90_gui.views.viewer_3d'` | Missing file or bad install → check `views\viewer_3d.py`, then `UPDATE_VIEWER.ps1` |
| Import path under `lmgc90_engine\src\lmgc90_gui\...` | Wrong tree / duplicate copy → reinstall from `lmgc90_gui\` |
| `pylmgc_available() == False` | Wrong Python env; reinstall the GUI inside the conda env that has pylmgc90 |
| Empty 3D viewer | Create avatars then **Refresh scene**; install `pyvista pyvistaqt` |
| Locale decimals `0,5` (FR) | Numeric fields accept a comma; prefer a dot in scripts |

---

## Licence / author

Open Source — **Bachir Zerourou**.  
Related to the [LMGC90](https://git-xen.lmgc.univ-montp2.fr/lmgc90) ecosystem and the historical [LMGC90_MVC_GUI](https://github.com/bzerourou/LMG90_GUI_MVC/).

---

## Package READMEs

- `lmgc90_core/README.md` — Project / pre / populations API  
- `lmgc90_engine/README.md` — EngineSession / materialize / DATBOX  
- `lmgc90_gui/README.md` — GUI launch / extras `[qt]` `[viz]`  
