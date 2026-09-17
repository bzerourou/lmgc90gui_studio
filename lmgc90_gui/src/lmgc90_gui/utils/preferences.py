"""User preferences (JSON file under user home or project)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Preferences:
    # computation
    dt: float = 1e-3
    nb_steps: int = 1000
    theta: float = 0.5
    tol: float = 1.666e-4
    relax: float = 1.0
    gs_it1: int = 50
    gs_it2: int = 1000
    freq_write: int = 50
    freq_display: int = 50
    solver_type: str = "Stored_Delassus_Loops         "
    # environment
    python_executable: str = "python"
    work_directory: str = ""
    auto_write_datbox: bool = True
    journal_to_file: bool = False
    journal_path: str = ""
    # UI
    default_dimension: int = 2
    confirm_run: bool = True

    def chipy_params(self) -> dict[str, Any]:
        return {
            "dt": self.dt,
            "nb_steps": self.nb_steps,
            "theta": self.theta,
            "tol": self.tol,
            "relax": self.relax,
            "gs_it1": self.gs_it1,
            "gs_it2": self.gs_it2,
            "freq_write": self.freq_write,
            "freq_display": self.freq_display,
            "solver_type": self.solver_type,
        }

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Preferences:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        return cls(**{k: v for k, v in data.items() if k in known})


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
