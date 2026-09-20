"""Shared pure-project helpers for demo scenes (no Qt, no engine)."""
from __future__ import annotations

from .. import pre
from ..project import Project


def ensure_rigid_2d(project: Project, *, density: float = 2500.0) -> None:
    if not any(m.name == "TDURx" for m in project.materials):
        project.add(pre.material(name="TDURx", materialType="RIGID", density=density))
    if not any(m.name == "rigid" for m in project.models):
        project.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))


def ensure_rigid_3d(project: Project, *, density: float = 2500.0) -> None:
    if not any(m.name == "TDURx" for m in project.materials):
        project.add(pre.material(name="TDURx", materialType="RIGID", density=density))
    if not any(m.name == "rigid" for m in project.models):
        project.add(pre.model(name="rigid", physics="MECAx", element="Rxx3D", dimension=3))


def iqs(project: Project, name: str = "iqsc0", fric: float = 0.3) -> None:
    if not any(l.name == name for l in project.laws):
        project.add(pre.tact_behav(name=name, law="IQS_CLB", fric=fric))


def see_dd(project: Project, law: str = "iqsc0", alert: float = 0.05) -> None:
    project.add(pre.see_table(
        CorpsCandidat="RBDY2", candidat="DISKx", colorCandidat="BLUEx",
        CorpsAntagoniste="RBDY2", antagoniste="DISKx", colorAntagoniste="BLUEx",
        behav=law, alert=alert,
    ))


def see_dw(project: Project, law: str = "iqsc0", alert: float = 0.05) -> None:
    project.add(pre.see_table(
        CorpsCandidat="RBDY2", candidat="DISKx", colorCandidat="BLUEx",
        CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="GRAYx",
        behav=law, alert=alert,
    ))
