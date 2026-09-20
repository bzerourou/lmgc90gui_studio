"""Project — the unit of work a researcher imports.

No Qt. No pylmgc90 objects. Mutations go through CommandHistory so Ctrl+Z
is a library feature, not a GUI feature.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from .commands import (
    AddAvatar, AddDOF, AddLaw, AddLoop, AddMaterial, AddModel, AddPopulation,
    AddPostPro, AddSeeTable, CommandHistory, RemoveAvatar, SetGroup,
)
from .entities import (
    Avatar, ContactLaw, DOFOperation, ForLoop, GranuloConfig, Loop, Material, Model,
    PostProCommand, VisibilityRule,
)
from .errors import UnknownReferenceError, ValidationError
from .generate import NumpyGranulo, expand_for_loop, expand_loop
from .masonry import MasonryConfig, expand_masonry
from .population import ParticlePopulation
from .types import UnitSystem
from .validate import (
    validate_avatar, validate_contact_law, validate_material, validate_model,
    validate_visibility,
)

Entity = Union[
    Material, Model, Avatar, ParticlePopulation, ContactLaw,
    VisibilityRule, DOFOperation, PostProCommand, Loop, ForLoop, GranuloConfig,
]


@dataclass
class Project:
    name: str = "untitled"
    dimension: int = 2
    units: UnitSystem = UnitSystem.SI
    materials: list[Material] = field(default_factory=list)
    models: list[Model] = field(default_factory=list)
    avatars: list[Avatar] = field(default_factory=list)
    populations: list[ParticlePopulation] = field(default_factory=list)
    laws: list[ContactLaw] = field(default_factory=list)
    visibility: list[VisibilityRule] = field(default_factory=list)
    operations: list[DOFOperation] = field(default_factory=list)
    postpro: list[PostProCommand] = field(default_factory=list)
    loops: list[Loop] = field(default_factory=list)
    for_loops: list[ForLoop] = field(default_factory=list)
    granulo: list[GranuloConfig] = field(default_factory=list)
    avatar_groups: dict[str, list[str]] = field(default_factory=dict)
    population_groups: dict[str, list[str]] = field(default_factory=dict)
    dynamic_vars: dict[str, Any] = field(default_factory=dict)
    history: CommandHistory = field(default_factory=CommandHistory, repr=False)
    record: bool = True

    # ------------------------------------------------------------------ API
    def add(self, obj: Entity):
        """Validate, apply, journal. Returns the entity (or generated result)."""
        if isinstance(obj, Material):
            validate_material(obj)
            if any(m.name == obj.name for m in self.materials):
                raise ValidationError(f"material {obj.name!r} already exists")
            return self._run(AddMaterial(obj), obj)
        if isinstance(obj, Model):
            validate_model(obj)
            if obj.dimension != self.dimension:
                raise ValidationError(
                    f"model {obj.name!r} is {obj.dimension}D, project is {self.dimension}D"
                )
            if any(m.name == obj.name for m in self.models):
                raise ValidationError(f"model {obj.name!r} already exists")
            return self._run(AddModel(obj), obj)
        if isinstance(obj, Avatar):
            self._check_avatar(obj)
            return self._run(AddAvatar(obj), obj)
        if isinstance(obj, ParticlePopulation):
            self._check_population(obj)
            return self._run(AddPopulation(obj), obj)
        if isinstance(obj, ContactLaw):
            validate_contact_law(obj)
            if any(l.name == obj.name for l in self.laws):
                raise ValidationError(f"law {obj.name!r} already exists")
            return self._run(AddLaw(obj), obj)
        if isinstance(obj, VisibilityRule):
            validate_visibility(obj, {l.name for l in self.laws})
            cmd = AddSeeTable(obj)
            self._run(cmd, obj)
            return obj
        if isinstance(obj, DOFOperation):
            self._check_dof(obj)
            cmd = AddDOF(obj)
            self._run(cmd, obj)
            return obj
        if isinstance(obj, PostProCommand):
            cmd = AddPostPro(obj)
            self._run(cmd, obj)
            return obj
        if isinstance(obj, Loop):
            return self.apply_loop(obj)
        if isinstance(obj, ForLoop):
            return self.apply_for_loop(obj)
        if isinstance(obj, GranuloConfig):
            return self.deposit(obj)
        raise TypeError(f"cannot add {type(obj).__name__}")

    def group(self, name: str, ids: Iterable[str]) -> None:
        self._run(SetGroup(name, list(ids)))

    def remove_avatar(self, avatar_id: str) -> Avatar:
        av = self.avatar(avatar_id)
        self._run(RemoveAvatar(av))
        return av

    def deposit(self, config: GranuloConfig) -> ParticlePopulation:
        if config.dimension != self.dimension:
            config.dimension = self.dimension
        result = NumpyGranulo().deposit(config)
        self._check_population(result.population)
        self._run(AddPopulation(result.population, config))
        if config.group_name:
            pid = result.population.population_id
            self.population_groups.setdefault(config.group_name, []).append(pid)
            self.avatar_groups.setdefault(config.group_name, []).append(pid)
        return result.population

    def apply_loop(self, loop: Loop, template: Optional[Avatar] = None) -> list[Avatar]:
        tmpl = template or self.avatar(loop.model_avatar_id)
        generated = expand_loop(loop, tmpl, dimension=self.dimension)
        for av in generated:
            self._check_avatar(av)
        self._run(AddLoop(loop, generated))
        return generated

    def apply_for_loop(self, for_loop: ForLoop, template: Optional[Avatar] = None) -> list[Avatar]:
        tmpl = template or self.avatar(for_loop.model_avatar_id)
        generated = expand_for_loop(for_loop, tmpl, dimension=self.dimension)
        for av in generated:
            self._check_avatar(av)
        for av in generated:
            self.avatars.append(av)
        self.for_loops.append(for_loop)
        if for_loop.group_name:
            self.avatar_groups.setdefault(for_loop.group_name, []).extend(
                [a.avatar_id for a in generated]
            )
            for_loop.generated_ids = [a.avatar_id for a in generated]
        return generated

    def apply_masonry(self, config: MasonryConfig) -> list[Avatar]:
        if self.dimension != 2:
            raise ValidationError("masonry wall generator is 2D only")
        generated = expand_masonry(config)
        for av in generated:
            self._check_avatar(av)
        for av in generated:
            self.avatars.append(av)
        if config.group_name:
            self.avatar_groups.setdefault(config.group_name, []).extend(
                [a.avatar_id for a in generated]
            )
        return generated


    def undo(self):
        return self.history.undo(self)

    def redo(self):
        return self.history.redo(self)

    def journal(self) -> list[dict[str, Any]]:
        return self.history.journal()

    # ---------------------------------------------------------------- lookup
    def material(self, name: str) -> Material:
        for m in self.materials:
            if m.name == name:
                return m
        raise UnknownReferenceError(f"material {name!r}")

    def model(self, name: str) -> Model:
        for m in self.models:
            if m.name == name:
                return m
        raise UnknownReferenceError(f"model {name!r}")

    def avatar(self, avatar_id: str) -> Avatar:
        for a in self.avatars:
            if a.avatar_id == avatar_id:
                return a
        raise UnknownReferenceError(f"avatar {avatar_id!r}")

    def population(self, population_id: str) -> ParticlePopulation:
        for p in self.populations:
            if p.population_id == population_id:
                return p
        raise UnknownReferenceError(f"population {population_id!r}")

    def avatars_in(self, group_name: str) -> list[Avatar]:
        ids = self.avatar_groups.get(group_name, [])
        found = []
        for aid in ids:
            try:
                found.append(self.avatar(aid))
            except UnknownReferenceError:
                continue
        return found

    @property
    def n_bodies(self) -> int:
        return len(self.avatars) + sum(len(p) for p in self.populations)

    def summary(self) -> str:
        lines = [
            f"Project {self.name!r}  {self.dimension}D  {self.units.value}",
            f"  materials : {', '.join(m.name for m in self.materials) or '—'}",
            f"  models    : {', '.join(m.name for m in self.models) or '—'}",
            f"  avatars   : {len(self.avatars)} (AoS, individually editable)",
            f"  populations: {len(self.populations)} "
            f"({sum(len(p) for p in self.populations)} particles SoA)",
            f"  laws      : {', '.join(l.name for l in self.laws) or '—'}",
            f"  see tables: {len(self.visibility)}",
            f"  DOF       : {len(self.operations)}",
            f"  postpro   : {len(self.postpro)}",
            f"  bodies    : {self.n_bodies}  |  undo stack : {len(self.history)}",
        ]
        return "\n".join(lines)

    # ---------------------------------------------------------------- I/O
    def save(self, path) -> Path:
        from .io import save_project
        return save_project(self, Path(path))

    @classmethod
    def load(cls, path) -> Project:
        from .io import load_project
        return load_project(Path(path))

    def to_pre_script(self) -> str:
        from .pre_script import emit_pre
        return emit_pre(self)

    def to_chipy_script(self, **params) -> str:
        from .chipy_script import emit_chipy
        return emit_chipy(self, **params)

    def equivalent(self, obj: Entity) -> str:
        from .pre_script import emit_equivalent
        return emit_equivalent(self, obj)

    def sbatch(self, **slurm) -> str:
        from .pipeline import render_sbatch
        return render_sbatch(self, **slurm)

    # ---------------------------------------------------------- internals
    def _run(self, cmd, result=None):
        if self.record:
            self.history.do(cmd, self)
        else:
            cmd.apply(self)
        return result if result is not None else cmd

    def _check_avatar(self, avatar: Avatar) -> None:
        if any(a.avatar_id == avatar.avatar_id for a in self.avatars):
            raise ValidationError(f"avatar id {avatar.avatar_id!r} already present")
        model = self.model(avatar.model_name)
        self.material(avatar.material_name)
        validate_avatar(avatar, model)

    def _check_population(self, pop: ParticlePopulation) -> None:
        if any(p.population_id == pop.population_id for p in self.populations):
            raise ValidationError(f"population {pop.population_id!r} already present")
        if pop.dimension != self.dimension:
            raise ValidationError("population dimension ≠ project dimension")
        self.model(pop.model_name)
        self.material(pop.material_name)

    def _check_dof(self, op: DOFOperation) -> None:
        if op.target_type == "avatar":
            self.avatar(str(op.target_value))
        elif op.target_type == "group":
            if op.target_value not in self.avatar_groups:
                raise UnknownReferenceError(f"group {op.target_value!r}")

    def _insert_material(self, m: Material) -> None:
        self.materials.append(m)

    def _drop_material(self, name: str) -> None:
        self.materials[:] = [m for m in self.materials if m.name != name]

    def _insert_model(self, m: Model) -> None:
        self.models.append(m)

    def _drop_model(self, name: str) -> None:
        self.models[:] = [m for m in self.models if m.name != name]

    def _insert_avatar(self, a: Avatar) -> None:
        self.avatars.append(a)

    def _drop_avatar(self, avatar_id: str) -> dict[str, list[str]]:
        snapshot = {k: list(v) for k, v in self.avatar_groups.items() if avatar_id in v}
        self.avatars[:] = [a for a in self.avatars if a.avatar_id != avatar_id]
        for name, ids in list(self.avatar_groups.items()):
            self.avatar_groups[name] = [i for i in ids if i != avatar_id]
            if not self.avatar_groups[name]:
                del self.avatar_groups[name]
        self.operations[:] = [
            op for op in self.operations
            if not (op.target_type == "avatar" and op.target_value == avatar_id)
        ]
        return snapshot

    def _insert_population(self, pop: ParticlePopulation, config: GranuloConfig | None) -> None:
        self.populations.append(pop)
        if config is not None:
            config.population_id = pop.population_id
            self.granulo.append(config)
        if pop.group_name:
            self.population_groups.setdefault(pop.group_name, []).append(pop.population_id)

    def _drop_population(self, population_id: str) -> None:
        self.populations[:] = [p for p in self.populations if p.population_id != population_id]
        self.granulo[:] = [g for g in self.granulo if g.population_id != population_id]
        for name, ids in list(self.population_groups.items()):
            self.population_groups[name] = [i for i in ids if i != population_id]
            if not self.population_groups[name]:
                del self.population_groups[name]

    def _insert_law(self, law: ContactLaw) -> None:
        self.laws.append(law)

    def _drop_law(self, name: str) -> None:
        self.laws[:] = [l for l in self.laws if l.name != name]

    def _insert_see(self, rule: VisibilityRule) -> int:
        self.visibility.append(rule)
        return len(self.visibility) - 1

    def _drop_see(self, index: int) -> None:
        if 0 <= index < len(self.visibility):
            self.visibility.pop(index)

    def _insert_dof(self, op: DOFOperation) -> int:
        self.operations.append(op)
        return len(self.operations) - 1

    def _drop_dof(self, index: int) -> None:
        if 0 <= index < len(self.operations):
            self.operations.pop(index)

    def _insert_postpro(self, cmd: PostProCommand) -> int:
        self.postpro.append(cmd)
        return len(self.postpro) - 1

    def _drop_postpro(self, index: int) -> None:
        if 0 <= index < len(self.postpro):
            self.postpro.pop(index)

    def _insert_loop(self, loop: Loop) -> None:
        self.loops.append(loop)

    def _drop_loop(self, loop_id: str) -> None:
        self.loops[:] = [lp for lp in self.loops if lp.loop_id != loop_id]
