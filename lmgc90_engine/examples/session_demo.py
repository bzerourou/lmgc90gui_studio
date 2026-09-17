"""Demo: build a Project with core, drive it with EngineSession.

Works without pylmgc90 (script emission only).
With pylmgc90 installed, also materializes and writes DATBOX.

Run from repo root:
    PYTHONPATH=lmgc90_core/src:lmgc90_engine/src python lmgc90_engine/examples/session_demo.py
"""
from __future__ import annotations

from pathlib import Path

from lmgc90_core import Project, pre
from lmgc90_engine import EngineSession

OUT = Path(__file__).resolve().parent / "_out_session"


def build() -> Project:
    p = Project(name="engine_demo", dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800.0))
    p.add(pre.material(name="BETON", materialType="RIGID", density=2400.0))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))

    floor = pre.smoothWall(
        l=2.0, h=0.1, center=[0.0, -0.05],
        model="rigid", material="STEEL", color="GRAYx", nb_polyg=16,
    )
    p.add(floor)

    for i, x in enumerate((-0.4, 0.0, 0.4)):
        d = pre.rigidDisk(
            r=0.08, center=[x, 0.2 + 0.05 * i],
            model="rigid", material="BETON", color="BLUEx",
        )
        p.add(d)

    p.add(pre.tact_behav(name="st_bt", law="IQS_CLB", fric=0.3))
    p.add(pre.see_table(
        CorpsCandidat="RBDY2", candidat="DISKx", colorCandidat="BLUEx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="GRAYx",
        behav="st_bt", alert=0.05,
    ))
    return p


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    p = build()
    session = EngineSession(p)
    print(session)
    print(f"pylmgc available: {session.available()}")

    paths = session.export_all(OUT, dt=1e-3, nb_steps=2000, try_datbox=True)
    for kind, path in paths.items():
        print(f"  wrote {kind}: {path}")

    if session.available():
        scene = session.materialize()
        print(f"materialized: {len(scene.body_by_avatar_id)} avatars")
        for aid, body in session.body_map.items():
            print(f"  {aid[:8]}… → {type(body).__name__}")
    else:
        print("skip materialize (install pylmgc90 for live DATBOX)")


if __name__ == "__main__":
    main()
