"""Lecture des sorties DISPLAY/*.pvd de chipy — PyVista pur, sans pylmgc90."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import pyvista as pv


class DisplaySeries:
    """Un ou plusieurs .pvd (rigides, MAILx...) indexés sur la même frise temporelle.

    L'axe de référence est le .pvd qui a le plus de pas ; les autres sont lus
    au temps le plus proche.
    """

    def __init__(self, display_dir: Path | str):
        d = Path(display_dir)
        files = sorted(d.glob("*.pvd"))
        if not files:
            raise FileNotFoundError(f"Aucun .pvd dans {d}")
        self.readers: Dict[str, pv.PVDReader] = {}
        self.times: Dict[str, np.ndarray] = {}
        for f in files:
            r = pv.PVDReader(str(f))
            t = np.asarray(r.time_values, dtype=float)
            if t.size:
                self.readers[f.stem] = r
                self.times[f.stem] = t
        if not self.readers:
            raise ValueError(f"{d} : .pvd vides (calcul pas encore écrit ?)")
        self.ref = max(self.times, key=lambda k: len(self.times[k]))
        self.directory = d

    @property
    def names(self) -> List[str]:
        return list(self.readers)

    def __len__(self) -> int:
        return len(self.times[self.ref])

    def time(self, i: int) -> float:
        return float(self.times[self.ref][i])

    def frame(self, i: int) -> Dict[str, pv.DataSet]:
        """{nom_pvd: dataset} pour le pas i de l'axe de référence."""
        t = self.time(i)
        out: Dict[str, pv.DataSet] = {}
        for name, r in self.readers.items():
            j = int(np.argmin(np.abs(self.times[name] - t)))
            r.set_active_time_point(j)
            ds = r.read()
            if isinstance(ds, pv.MultiBlock):
                ds = ds.combine() if ds.n_blocks else None
            if ds is not None and ds.n_points:
                out[name] = ds
        return out

    def reload(self) -> int:
        """Relit les .pvd (calcul en cours). Renvoie le nouveau nombre de pas."""
        fresh = DisplaySeries(self.directory)
        self.__dict__.update(fresh.__dict__)
        return len(self)