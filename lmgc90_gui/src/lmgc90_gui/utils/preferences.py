"""User preferences (JSON under ~/.lmgc90_gui/preferences.json).

Aligned with legacy LMGC90_GUI preferences (paths, autosave, recent files,
performance) plus Studio computation / environment settings.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Preferences:
    # --- computation (chipy defaults) ---
    dt: float = 1e-3
    nb_steps: int = 1000
    theta: float = 0.5
    tol: float = 1.666e-4
    relax: float = 1.0
    gs_it1: int = 50
    gs_it2: int = 1000
    norm: str = "Quad "
    deformable: bool = False
    disable_log: bool = True
    freq_write: int = 50
    freq_display: int = 50
    solver_type: str = "Stored_Delassus_Loops         "

    # --- environment ---
    python_executable: str = "python"
    work_directory: str = ""
    projects_directory: str = ""  # default Open/Save path (legacy "Paths")
    auto_write_datbox: bool = True
    journal_to_file: bool = False
    journal_path: str = ""
    default_dimension: int = 2
    confirm_run: bool = True

    # --- units (legacy; metadata for UI / docs) ---
    units: str = "SI"  # SI | CGS

    # --- autosave (legacy) ---
    auto_save: bool = False
    auto_save_interval_min: int = 10
    auto_save_on_quit: bool = True

    # --- recent projects (legacy) ---
    recent_max: int = 10
    recent_projects: list = field(default_factory=list)

    # --- performance / tree (legacy) ---
    show_avatars_in_tree: bool = True
    show_granulo_individually: bool = False  # hide AoS granulo clones in tree
    create_pylmgc_on_generate: bool = True
    max_tree_avatars: int = 2000  # soft limit when listing

    # --- scripts / viewer ---
    script_use_loop: bool = True  # compact for-loops in pre.py when possible
    auto_refresh_viewer: bool = False
    viewer_show_dof_default: bool = False
    viewer_show_laws_default: bool = False

    # --- UI language hint ---
    language: str = "fr"  # fr | en

    def chipy_params(self) -> dict[str, Any]:
        return {
            "dt": self.dt,
            "nb_steps": self.nb_steps,
            "theta": self.theta,
            "tol": self.tol,
            "relax": self.relax,
            "gs_it1": self.gs_it1,
            "gs_it2": self.gs_it2,
            "norm": self.norm,
            "freq_write": self.freq_write,
            "freq_display": self.freq_display,
            "solver_type": self.solver_type,
            "deformable": self.deformable,
            "disable_log": self.disable_log,
        }

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Preferences:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        cleaned = {k: v for k, v in data.items() if k in known}
        # ensure list type
        if "recent_projects" in cleaned and not isinstance(cleaned["recent_projects"], list):
            cleaned["recent_projects"] = list(cleaned["recent_projects"] or [])
        return cls(**cleaned)

    def remember_project(self, path: str | Path) -> None:
        """Push *path* to the front of recent_projects (dedup, capped)."""
        p = str(Path(path).resolve())
        rec = [x for x in (self.recent_projects or []) if x != p]
        rec.insert(0, p)
        self.recent_projects = rec[: max(1, int(self.recent_max))]


def default_prefs_path() -> Path:
    return Path.home() / ".lmgc90_gui" / "preferences.json"


def load_preferences(path: Optional[Path] = None) -> Preferences:
    p = path or default_prefs_path()
    if not p.is_file():
        return Preferences()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return Preferences.from_dict(data)
    except Exception:
        return Preferences()


def save_preferences(prefs: Preferences, path: Optional[Path] = None) -> Path:
    p = path or default_prefs_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(prefs.to_dict(), indent=2), encoding="utf-8")
    return p
