"""Build a small project with the GUI controller — no Qt window.

Run:
  PYTHONPATH=lmgc90_core/src:lmgc90_engine/src:lmgc90_gui/src \\
    python lmgc90_gui/examples/headless_demo.py
"""
from __future__ import annotations

from pathlib import Path

from lmgc90_core import pre
from lmgc90_gui import ProjectController

OUT = Path(__file__).resolve().parent / "_out_gui"


def main() -> None:
    ctrl = ProjectController()
    ctrl.new_project("gui_headless", dimension=2)

    changes = []
    ctrl.state_changed.connect(lambda: changes.append("tick"))

    ctrl.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    ctrl.add(pre.material(name="SAND", materialType="RIGID", density=2500))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))

    with ctrl.batch():
        for i in range(3):
            ctrl.add(
                pre.rigidDisk(
                    r=0.08, center=[i * 0.25, 0.2],
                    model="rigid", material="SAND", color="BLUEx",
                )
            )
        wall = pre.smoothWall(
            l=1.2, h=0.08, center=[0.25, -0.04],
            model="rigid", material="STEEL", color="GRAYx", nb_polyg=12,
        )
        ctrl.add(wall)

    print(ctrl.summary())
    print(f"state_changed emissions after batch: {len(changes)}")

    OUT.mkdir(parents=True, exist_ok=True)
    paths = ctrl.export_all(OUT, dt=1e-3, nb_steps=500)
    for k, p in paths.items():
        print(f"  {k}: {p}")

    ctrl.save_project(OUT / "gui_headless.lmgc90")
    print(f"saved project → {OUT / 'gui_headless.lmgc90'}")


if __name__ == "__main__":
    main()
