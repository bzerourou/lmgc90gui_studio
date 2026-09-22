"""ProjectController — thin Qt façade over lmgc90_core.Project + EngineSession.

Rules
-----
* Business mutations go through ``project.add`` / ``project.remove_*`` (undoable).
* Live pylmgc objects live only in ``session`` after ``materialize()``.
* Identity is always avatar_id / population_id — never list index in the public API.
* Views connect to ``state_changed`` and re-read ``controller.project``.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from lmgc90_core.numpy_compat import patch_numpy_cross
from lmgc90_core import (
    Avatar,
    ContactLaw,
    DOFOperation,
    GranuloConfig,
    MasonryConfig,
    Loop,
    Material,
    Model,
    ParticlePopulation,
    PostProCommand,
    Project,
    VisibilityRule,
    pre,
)
try:
    from lmgc90_core import ForLoop
except ImportError:  # pragma: no cover — outdated editable install
    try:
        from lmgc90_core.entities import ForLoop
    except ImportError as exc:
        raise ImportError(
            "lmgc90_core is outdated (missing ForLoop). Reinstall:\n"
            "  pip install -e .\\lmgc90_core -e .\\lmgc90_engine -e \".\\lmgc90_gui[qt]\""
        ) from exc
from lmgc90_core.errors import LMGC90Error, ValidationError
from lmgc90_engine import EngineSession
from lmgc90_engine.errors import PylmgcNotAvailable

from .signals import Signal, make_qobject_base
from ..utils.app_journal import get_journal
from ..utils.preferences import Preferences, load_preferences, save_preferences

_QObject = make_qobject_base()

Entity = Union[
    Material, Model, Avatar, ParticlePopulation, ContactLaw,
    VisibilityRule, DOFOperation, PostProCommand, Loop, GranuloConfig,
]


class ProjectController(_QObject):
    """Central controller used by every tab and dialog."""

    state_changed = Signal()
    project_loaded = Signal()
    error_occurred = Signal(str)  # message for QMessageBox

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project = Project(name="untitled", dimension=2)
        self._session = EngineSession(self._project)
        self._filepath: Optional[Path] = None
        self._batch_depth = 0
        self._is_loading = False
        self.prefs: Preferences = load_preferences()
        self.journal = get_journal()
        if self.prefs.journal_to_file and self.prefs.journal_path:
            self.journal.set_file(Path(self.prefs.journal_path))
        self._work_dir: Optional[Path] = None

    # ------------------------------------------------------------------ accessors
    @property
    def project(self) -> Project:
        return self._project

    @property
    def session(self) -> EngineSession:
        return self._session

    @property
    def filepath(self) -> Optional[Path]:
        return self._filepath

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    # ------------------------------------------------------------------ batch
    @contextmanager
    def batch(self):
        """Suppress intermediate state_changed; emit once on exit."""
        self._batch_depth += 1
        try:
            yield
        finally:
            self._batch_depth -= 1
            if self._batch_depth == 0 and not self._is_loading:
                self._emit()

    def _emit(self) -> None:
        if self._batch_depth == 0 and not self._is_loading:
            self.state_changed.emit()

    def _notify_error(self, msg: str) -> None:
        try:
            self.journal.error(str(msg))
        except Exception:
            pass
        self.error_occurred.emit(str(msg))

    # ------------------------------------------------------------------ project lifecycle
    def new_project(self, name: str = "untitled", dimension: int = 2) -> None:
        self._project = Project(name=name, dimension=int(dimension))
        self._session = EngineSession(self._project)
        self._filepath = None
        self._emit()
        self.project_loaded.emit()

    def apply_scene(self, builder, *, on_conflict: str = "error") -> None:
        """Run a pure core scene builder ``builder(project)`` then notify UI.

        Architecture: scene logic lives in ``lmgc90_core.scenes``; the GUI never
        mutates ``Project`` fields directly — only this entry point.

        Does **not** reset the project or the command history.

        on_conflict (passed to ``Project.add`` / ``group``):
          • ``error`` — fail on duplicate material/model/law names
          • ``skip`` / ``merge`` — reuse existing named entities; merge groups;
            skip duplicate visibility / post-pro (for *Ajouter au projet*)

        Pending ``GranuloConfig`` entries are resolved via ``deposit``.
        """
        if not callable(builder):
            raise TypeError("apply_scene expects a callable(project) -> None")
        prev = getattr(self._project, "_on_conflict", "error")
        self._project._on_conflict = on_conflict
        try:
            builder(self._project)
            for cfg in list(self._project.granulo):
                if getattr(cfg, "population_id", None):
                    continue
                try:
                    self.deposit(cfg)
                except Exception as dep_exc:
                    # duplicate population / deposit clash → skip when merging
                    if on_conflict in ("skip", "merge"):
                        try:
                            self.journal.warning(f"deposit skipped: {dep_exc}")
                        except Exception:
                            pass
                    else:
                        raise
        finally:
            self._project._on_conflict = prev
        self._session.mark_dirty()
        self._emit()

    def save_project(self, path: Optional[Union[str, Path]] = None) -> Path:
        target = Path(path) if path is not None else self._filepath
        if target is None:
            raise ValidationError("no path given and no previous filepath")
        out = self._project.save(target)
        self._filepath = out
        return out

    def load_project(self, path: Union[str, Path]) -> Project:
        self._is_loading = True
        try:
            self._project = Project.load(path)
            self._session = EngineSession(self._project)
            self._filepath = Path(path)
        finally:
            self._is_loading = False
        self._emit()
        self.project_loaded.emit()
        return self._project

    # ------------------------------------------------------------------ generic add
    def add(self, obj: Entity) -> Any:
        """Validate + journal via Project.add, mark session dirty, emit."""
        try:
            result = self._project.add(obj)
            self._session.mark_dirty()
            self._emit()
            return result
        except (ValidationError, LMGC90Error, TypeError, ValueError) as exc:
            self._notify_error(str(exc))
            raise

    # ------------------------------------------------------------------ materials / models
    def add_material(self, material: Material) -> Material:
        return self.add(material)

    def add_model(self, model: Model) -> Model:
        return self.add(model)


    def update_material(self, name: str, material: Material) -> None:
        """Replace material *name* with *material* (name may change)."""
        found = False
        for i, m in enumerate(self._project.materials):
            if m.name == name:
                self._project.materials[i] = material
                found = True
                break
        if not found:
            self._project.materials.append(material)
        self._session.mark_dirty()
        self._emit()

    def update_model(self, name: str, model: Model) -> None:
        found = False
        for i, m in enumerate(self._project.models):
            if m.name == name:
                self._project.models[i] = model
                found = True
                break
        if not found:
            self._project.models.append(model)
        self._session.mark_dirty()
        self._emit()

    def update_law(self, name: str, law: ContactLaw) -> None:
        found = False
        for i, l in enumerate(self._project.laws):
            if l.name == name:
                self._project.laws[i] = law
                found = True
                break
        if not found:
            self._project.laws.append(law)
        self._session.mark_dirty()
        self._emit()

    def update_avatar(self, avatar_id: str, avatar: Avatar) -> None:
        for i, a in enumerate(self._project.avatars):
            if a.avatar_id == avatar_id:
                # keep stable id
                avatar.avatar_id = avatar_id
                self._project.avatars[i] = avatar
                self._session.mark_dirty()
                self._emit()
                return
        raise ValidationError(f"avatar {avatar_id!r} not found")

    def update_visibility(self, index: int, rule: VisibilityRule) -> None:
        if 0 <= index < len(self._project.visibility):
            self._project.visibility[index] = rule
            self._session.mark_dirty()
            self._emit()

    def update_dof(self, index: int, op: DOFOperation) -> None:
        if 0 <= index < len(self._project.operations):
            self._project.operations[index] = op
            self._session.mark_dirty()
            self._emit()

    def remove_material(self, name: str) -> None:
        # keep API; core may grow remove later — for now filter + dirty
        self._project.materials[:] = [m for m in self._project.materials if m.name != name]
        self._session.mark_dirty()
        self._emit()

    def remove_model(self, name: str) -> None:
        self._project.models[:] = [m for m in self._project.models if m.name != name]
        self._session.mark_dirty()
        self._emit()

    # ------------------------------------------------------------------ avatars (by id)
    def add_avatar(self, avatar: Avatar) -> Avatar:
        return self.add(avatar)

    def remove_avatar(self, avatar_id: str) -> Avatar:
        try:
            av = self._project.remove_avatar(avatar_id)
            self._session.mark_dirty()
            self._emit()
            return av
        except (ValidationError, LMGC90Error) as exc:
            self._notify_error(str(exc))
            raise

    def get_avatar(self, avatar_id: str) -> Avatar:
        return self._project.avatar(avatar_id)

    def find_avatar_index(self, avatar_id: str) -> int:
        for i, a in enumerate(self._project.avatars):
            if a.avatar_id == avatar_id:
                return i
        return -1

    # ------------------------------------------------------------------ groups
    def group(self, name: str, ids: Iterable[str]) -> None:
        self._project.group(name, ids)
        self._session.mark_dirty()
        self._emit()

    def set_dynamic_var(self, name: str, expression: str) -> None:
        self._project.dynamic_vars[name] = expression
        self._session.mark_dirty()
        self._emit()

    def remove_dynamic_var(self, name: str) -> None:
        self._project.dynamic_vars.pop(name, None)
        self._session.mark_dirty()
        self._emit()

    def remove_group(self, name: str) -> None:
        """Delete a group (undoable via empty set + pop)."""
        if name not in self._project.avatar_groups:
            return
        self._project.group(name, [])
        self._project.avatar_groups.pop(name, None)
        self._session.mark_dirty()
        self._emit()

    # ------------------------------------------------------------------ populations / granulo
    def add_population(self, pop: ParticlePopulation) -> ParticlePopulation:
        return self.add(pop)

    def deposit(self, config: GranuloConfig) -> ParticlePopulation:
        """Deposit particles: **pylmgc90** when available, else core NumpyGranulo RSA.

        Architecture: engine ``run_granulo`` → ``pre.depositInBox2D``; fallback
        stays pure in ``Project.deposit`` (no pylmgc import in core).
        """
        try:
            if self.pylmgc_available():
                pop = self._session.run_granulo(config)
                self._emit()
                return pop
            pop = self._project.deposit(config)
            self._session.mark_dirty()
            self._emit()
            return pop
        except (ValidationError, LMGC90Error, ValueError) as exc:
            self._notify_error(str(exc))
            raise

    def run_granulo_pylmgc(self, config: GranuloConfig, **kwargs) -> ParticlePopulation:
        """Deposit via engine (pylmgc if available, else fallback grid)."""
        try:
            pop = self._session.run_granulo(config, **kwargs)
            self._emit()
            return pop
        except Exception as exc:
            self._notify_error(str(exc))
            raise

    def remove_population(self, population_id: str) -> None:
        self._project._drop_population(population_id)
        self._session.mark_dirty()
        self._emit()

    # ------------------------------------------------------------------ loops
    def apply_loop(self, loop: Loop, template: Optional[Avatar] = None) -> list[Avatar]:
        try:
            generated = self._project.apply_loop(loop, template)
            self._session.mark_dirty()
            self._emit()
            return generated
        except (ValidationError, LMGC90Error) as exc:
            self._notify_error(str(exc))
            raise

    def apply_for_loop(self, for_loop: ForLoop, template: Optional[Avatar] = None) -> list[Avatar]:
        try:
            generated = self._project.apply_for_loop(for_loop, template)
            self._session.mark_dirty()
            self._emit()
            return generated
        except (ValidationError, LMGC90Error, ValueError) as exc:
            self._notify_error(str(exc))
            raise

    def apply_masonry(self, config: MasonryConfig) -> list[Avatar]:
        try:
            generated = self._project.apply_masonry(config)
            self._session.mark_dirty()
            self._emit()
            return generated
        except (ValidationError, LMGC90Error, ValueError) as exc:
            self._notify_error(str(exc))
            raise

    # ------------------------------------------------------------------ laws / visibility / DOF / postpro
    def add_law(self, law: ContactLaw) -> ContactLaw:
        return self.add(law)

    def remove_law(self, name: str) -> None:
        self._project._drop_law(name)
        self._session.mark_dirty()
        self._emit()

    def add_visibility(self, rule: VisibilityRule) -> VisibilityRule:
        return self.add(rule)

    def remove_visibility(self, index: int) -> None:
        self._project._drop_see(index)
        self._session.mark_dirty()
        self._emit()

    def add_dof(self, op: DOFOperation) -> DOFOperation:
        return self.add(op)

    def remove_dof(self, index: int) -> None:
        self._project._drop_dof(index)
        self._session.mark_dirty()
        self._emit()

    def add_postpro(self, cmd: PostProCommand) -> PostProCommand:
        return self.add(cmd)

    def remove_postpro(self, index: int) -> None:
        self._project._drop_postpro(index)
        self._session.mark_dirty()
        self._emit()

    # ------------------------------------------------------------------ history
    def undo(self) -> None:
        self._project.undo()
        self._session.mark_dirty()
        self._emit()

    def redo(self) -> None:
        self._project.redo()
        self._session.mark_dirty()
        self._emit()

    # ------------------------------------------------------------------ export / engine
    def emit_pre_script(self, path: Optional[Union[str, Path]] = None) -> str:
        return self._session.emit_pre_script(path)

    def emit_chipy_script(self, path: Optional[Union[str, Path]] = None, **kw) -> str:
        """Full ``command.py`` via engine → core ``emit_chipy`` (all ChipyRoutines keys)."""
        params = dict(self.prefs.chipy_params())
        params.update(kw)
        return self._session.emit_chipy_script(path, **params)

    def materialize(self, *, force: bool = False):
        """Build live pylmgc objects (needs pylmgc90). Safe for worker thread."""
        try:
            patch_numpy_cross()
        except Exception:
            pass
        return self._session.materialize(force=force)

    def visu_avatars(self, *, force: bool = True) -> None:
        """Materialize pylmgc bodies then ``pre.visuAvatars(bodies)`` (native viewer)."""
        try:
            self._session.visu_avatars(force=force)
            self.journal.info("visuAvatars opened")
        except Exception as exc:
            self._notify_error(str(exc))
            self.journal.exception("visuAvatars failed", exc)
            raise

    def write_datbox(self, path: Union[str, Path]) -> Path:
        try:
            patch_numpy_cross()
        except Exception:
            pass
        return self._session.write_datbox(path)

    def export_all(self, directory: Union[str, Path], **kw) -> dict:
        return self._session.export_all(directory, **kw)

    def pylmgc_available(self) -> bool:
        return self._session.available()

    # ------------------------------------------------------------------ helpers for views
    def summary(self) -> str:
        return self._project.summary()

    def pre(self):
        """Expose lmgc90_core.pre factories for tabs that build entities."""
        return pre


    # ------------------------------------------------------------------ preferences / journal
    def save_preferences(self) -> Path:
        path = save_preferences(self.prefs)
        if self.prefs.journal_to_file and self.prefs.journal_path:
            self.journal.set_file(Path(self.prefs.journal_path))
        else:
            self.journal.set_file(None)
        self.journal.info(f"Preferences saved → {path}")
        return path

    def set_work_dir(self, path: Union[str, Path]) -> Path:
        self._work_dir = Path(path)
        self._work_dir.mkdir(parents=True, exist_ok=True)
        return self._work_dir

    @property
    def work_dir(self) -> Optional[Path]:
        if self._work_dir is not None:
            return self._work_dir
        if self.prefs.work_directory:
            return Path(self.prefs.work_directory)
        return None

    def prepare_run_directory(self, directory: Union[str, Path]) -> dict:
        """Write pre.py + command.py (+ optional DATBOX) into *directory*."""
        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)
        self._work_dir = out
        params = self.prefs.chipy_params()
        paths: dict = {}
        self.journal.info(f"Preparing run directory {out}")
        try:
            pre_path = out / "pre.py"
            self.emit_pre_script(pre_path)
            paths["pre"] = pre_path
            cmd_path = out / "command.py"
            self.emit_chipy_script(cmd_path, **params)
            paths["command"] = cmd_path
            if self.prefs.auto_write_datbox and self.pylmgc_available():
                self.materialize(force=True)
                paths["datbox"] = self.write_datbox(out / "DATBOX")
                self.journal.info("DATBOX written")
            else:
                self.journal.info("DATBOX skipped (no pylmgc or disabled in prefs)")
        except Exception as exc:
            self.journal.exception("prepare_run_directory failed", exc)
            raise
        return paths

    def __repr__(self) -> str:
        return (
            f"ProjectController(project={self._project.name!r}, "
            f"bodies={self._project.n_bodies}, "
            f"session={self._session!r})"
        )
