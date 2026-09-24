"""EngineSession — the main façade for researchers and for the GUI.

Holds:
  - a reference to the pure Project
  - optional MaterializedScene (live pylmgc objects)
  - identity maps (avatar_id → body, population_id → list[body])
  - a dirty flag so the GUI can defer materialize() off the UI thread
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Union

from lmgc90_core.chipy_script import emit_chipy
from lmgc90_core.entities import GranuloConfig
from lmgc90_core.population import ParticlePopulation
from lmgc90_core.numpy_compat import patch_numpy_cross
from lmgc90_core.pre_script import emit_pre
from lmgc90_core.project import Project
from lmgc90_core.types import AvatarType

from . import datbox as datbox_mod
from .errors import PylmgcNotAvailable, UnknownBodyError
from .granulo import deposit_population
from .materialize import MaterializedScene, materialize_project


class EngineSession:
    """Runtime session bound to one Project.

    Typical flow
    ------------
    session = EngineSession(project)
    session.materialize()                 # needs pylmgc90
    session.write_datbox("DATBOX")
    # or always:
    session.emit_pre_script("pre.py")
    session.emit_chipy_script("command.py", dt=1e-3, nb_steps=5000)
    """

    def __init__(self, project: Project):
        self.project = project
        self._scene: Optional[MaterializedScene] = None
        self._dirty: bool = True

    # ------------------------------------------------------------------ state
    @property
    def is_materialized(self) -> bool:
        return self._scene is not None and not self._dirty

    @property
    def dirty(self) -> bool:
        return self._dirty

    def mark_dirty(self) -> None:
        """Call after any Project mutation so the next materialize rebuilds."""
        self._dirty = True

    @property
    def body_map(self) -> dict[str, Any]:
        """avatar_id → pre body. Empty until materialize()."""
        if self._scene is None:
            return {}
        return dict(self._scene.body_by_avatar_id)

    @property
    def population_map(self) -> dict[str, list[Any]]:
        if self._scene is None:
            return {}
        return dict(self._scene.bodies_by_population_id)

    def get_body(self, avatar_id: str) -> Any:
        if self._scene is None:
            raise UnknownBodyError("session not materialized")
        body = self._scene.body_by_avatar_id.get(avatar_id)
        if body is None:
            raise UnknownBodyError(f"avatar_id={avatar_id!r} not in body map")
        return body

    # ------------------------------------------------------------------ materialize
    def materialize(self, *, force: bool = False) -> MaterializedScene:
        """Build (or rebuild) live pylmgc containers from the Project.

        Safe to call from a worker thread; does not touch Qt.
        """
        patch_numpy_cross()
        if self.is_materialized and not force:
            return self._scene  # type: ignore[return-value]
        self._scene = materialize_project(self.project)
        self._dirty = False
        return self._scene

    def clear_live(self) -> None:
        """Drop live objects (e.g. before a long Project edit session)."""
        self._scene = None
        self._dirty = True

    # ------------------------------------------------------------------ I/O
    def visu_avatars(self, *, force: bool = True) -> None:
        """Materialize live pylmgc bodies and call ``pre.visuAvatars(bodies)``.

        Opens the native pylmgc90 / VTK-style viewer (same as legacy GUI).
        Requires an interactive display and ``pylmgc90`` installed.
        """
        scene = self.materialize(force=force)
        from .materialize import _pre
        pre = _pre()
        bodies = scene.bodies_container
        if bodies is None:
            raise RuntimeError("no bodies container after materialize")
        # API: pre.visuAvatars(avatars) — container or list
        try:
            pre.visuAvatars(bodies)
        except TypeError:
            # some builds expect a list
            try:
                lst = list(bodies)
            except TypeError:
                lst = [scene.body_by_avatar_id[k] for k in scene.body_by_avatar_id]
            pre.visuAvatars(lst)

    def write_datbox(self, path: Union[str, Path]) -> Path:
        """Materialize if needed, then pre.writeDatbox."""
        patch_numpy_cross()
        scene = self.materialize()
        out = datbox_mod.write_datbox(scene, path)
        try:
            datbox_mod._maybe_write_evolution_files(self.project, Path(out))
        except Exception:
            pass
        return out

    def write_cell_dual_datbox(self, base_path: Union[str, Path]) -> dict:
        """Export DATBOX_SPRD + DATBOX_STBL (+ PHASES.json) for cell adhesion."""
        patch_numpy_cross()
        scene = self.materialize()
        return datbox_mod.write_cell_dual_datbox(scene, self.project, base_path)

    def emit_pre_script(self, path: Optional[Union[str, Path]] = None) -> str:
        """Always available — delegates to lmgc90_core (no pylmgc required)."""
        text = emit_pre(self.project)
        if path is not None:
            datbox_mod.export_pre_script(self.project, path)
        return text

    def emit_chipy_script(
        self,
        path: Optional[Union[str, Path]] = None,
        *,
        dt: float = 1e-3,
        nb_steps: int = 5000,
        **kwargs: Any,
    ) -> str:
        text = emit_chipy(self.project, dt=dt, nb_steps=nb_steps, **kwargs)
        if path is not None:
            Path(path).write_text(text, encoding="utf-8")
        return text

    def export_all(
        self,
        directory: Union[str, Path],
        *,
        dt: float = 1e-3,
        nb_steps: int = 5000,
        try_datbox: bool = True,
    ) -> dict[str, Path]:
        """Write pre.py, command.py, and optionally DATBOX into *directory*."""
        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)
        paths: dict[str, Path] = {}
        paths["pre"] = Path(datbox_mod.export_pre_script(self.project, out / "pre.py"))
        chipy = self.emit_chipy_script(out / "command.py", dt=dt, nb_steps=nb_steps)
        paths["command"] = out / "command.py"
        if try_datbox:
            try:
                paths["datbox"] = self.write_datbox(out / "DATBOX")
            except PylmgcNotAvailable:
                pass
        return paths

    # ------------------------------------------------------------------ granulo
    def run_granulo(
        self,
        config: GranuloConfig,
        *,
        material_name: Optional[str] = None,
        model_name: Optional[str] = None,
        color: Optional[str] = None,
        avatar_type: Optional[AvatarType] = None,
        add_to_project: bool = True,
    ) -> ParticlePopulation:
        """Deposit via pylmgc (or fallback grid) and optionally project.add(pop)."""
        pop = deposit_population(
            config,
            material_name=material_name,
            model_name=model_name,
            color=color,
            avatar_type=avatar_type,
        )
        if add_to_project:
            self.project.add(pop)
            if config.group_name:
                pid = pop.population_id
                self.project.population_groups.setdefault(config.group_name, []).append(pid)
                self.project.avatar_groups.setdefault(config.group_name, []).append(pid)
            if config not in self.project.granulo:
                # keep intent list in sync when deposit was triggered from pending config
                pass
            self.mark_dirty()
        return pop

    # ------------------------------------------------------------------ helpers
    def available(self) -> bool:
        """True if pylmgc90 can be imported in this process."""
        try:
            import pylmgc90  # noqa: F401
            return True
        except ImportError:
            return False

    def __repr__(self) -> str:
        state = "live" if self.is_materialized else ("dirty" if self._dirty else "empty")
        n = self.project.n_bodies if hasattr(self.project, "n_bodies") else "?"
        return f"EngineSession(project={self.project.name!r}, bodies={n}, state={state})"
