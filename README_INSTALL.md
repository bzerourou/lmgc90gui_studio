# Installation

Full documentation (architecture, progressive install core → engine → GUI, conda / pylmgc90) is in **[README.md](./README.md)**.

## Quick reminder

```powershell
cd lmgc90gui_studio
pip install -e .\lmgc90_core
pip install -e .\lmgc90_engine
pip install -e ".\lmgc90_gui[qt,viz]"
lmgc90-gui
```

**Do not** rely on root-only `pip install -e .`: install all **three** sub-packages.
