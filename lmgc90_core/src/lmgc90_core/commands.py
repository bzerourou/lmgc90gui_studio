"""Command history — undo that a DEM researcher can actually use.

Granularity:
  - one entity (material, avatar, law, DOF) = one command
  - a whole ParticlePopulation = one command (never N avatars)
  - a Loop expansion = one command holding the generated avatar_ids
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from .entities import (
    Avatar, ContactLaw, DOFOperation, GranuloConfig, Loop, Material, Model,
    PostProCommand, VisibilityRule,
)
from .errors import HistoryError
from .population import ParticlePopulation

if TYPE_CHECKING:
    from .project import Project


class Command(Protocol):
    def apply(self, project: Project) -> None: ...
    def revert(self, project: Project) -> None: ...
    def describe(self) -> str: ...
    def to_journal(self) -> dict[str, Any]: ...


@dataclass
class AddMaterial:
    material: Material

    def apply(self, project: Project) -> None:
        project._insert_material(self.material)

    def revert(self, project: Project) -> None:
        project._drop_material(self.material.name)

    def describe(self) -> str:
        return f"add material {self.material.name} ({self.material.material_type.value})"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "add_material", "payload": self.material.to_dict()}


@dataclass
class AddModel:
    model: Model

    def apply(self, project: Project) -> None:
        project._insert_model(self.model)

    def revert(self, project: Project) -> None:
        project._drop_model(self.model.name)

    def describe(self) -> str:
        return f"add model {self.model.name} ({self.model.element})"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "add_model", "payload": self.model.to_dict()}


@dataclass
class AddAvatar:
    avatar: Avatar

    def apply(self, project: Project) -> None:
        project._insert_avatar(self.avatar)

    def revert(self, project: Project) -> None:
        project._drop_avatar(self.avatar.avatar_id)

    def describe(self) -> str:
        return f"add {self.avatar.avatar_type.value} {self.avatar.avatar_id[:8]}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "add_avatar", "payload": self.avatar.to_dict()}


@dataclass
class RemoveAvatar:
    avatar: Avatar
    groups_touched: dict[str, list[str]] = field(default_factory=dict)

    def apply(self, project: Project) -> None:
        self.groups_touched = project._drop_avatar(self.avatar.avatar_id)

    def revert(self, project: Project) -> None:
        project._insert_avatar(self.avatar)
        for name, ids in self.groups_touched.items():
            project.avatar_groups[name] = list(ids)

    def describe(self) -> str:
        return f"remove {self.avatar.avatar_type.value} {self.avatar.avatar_id[:8]}"

    def to_journal(self) -> dict[str, Any]:
        return {
            "op": "remove_avatar",
            "payload": {
                "avatar": self.avatar.to_dict(),
                "groups_touched": {k: list(v) for k, v in (self.groups_touched or {}).items()},
            },
        }


@dataclass
class AddPopulation:
    population: ParticlePopulation
    config: GranuloConfig | None = None

    def apply(self, project: Project) -> None:
        project._insert_population(self.population, self.config)

    def revert(self, project: Project) -> None:
        project._drop_population(self.population.population_id)

    def describe(self) -> str:
        return (
            f"add population {self.population.population_id[:12]} "
            f"n={len(self.population)} {self.population.avatar_type.value}"
        )

    def to_journal(self) -> dict[str, Any]:
        return {
            "op": "add_population",
            "payload": {
                "population": self.population.to_dict(),
                "config": self.config.to_dict() if self.config is not None else None,
            },
        }


@dataclass
class AddLaw:
    law: ContactLaw

    def apply(self, project: Project) -> None:
        project._insert_law(self.law)

    def revert(self, project: Project) -> None:
        project._drop_law(self.law.name)

    def describe(self) -> str:
        return f"add law {self.law.name} ({self.law.law_type.value})"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "add_law", "payload": self.law.to_dict()}


@dataclass
class AddSeeTable:
    rule: VisibilityRule
    index: int = -1

    def apply(self, project: Project) -> None:
        self.index = project._insert_see(self.rule)

    def revert(self, project: Project) -> None:
        project._drop_see(self.index)

    def describe(self) -> str:
        return (
            f"see {self.rule.candidate_contactor}/{self.rule.antagonist_contactor} "
            f"→ {self.rule.behavior_name}"
        )

    def to_journal(self) -> dict[str, Any]:
        return {"op": "add_see", "payload": self.rule.to_dict()}


@dataclass
class AddDOF:
    operation: DOFOperation
    index: int = -1

    def apply(self, project: Project) -> None:
        self.index = project._insert_dof(self.operation)

    def revert(self, project: Project) -> None:
        project._drop_dof(self.index)

    def describe(self) -> str:
        return f"{self.operation.operation_type} on {self.operation.target_type}:{self.operation.target_value}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "add_dof", "payload": self.operation.to_dict()}


@dataclass
class AddPostPro:
    command: PostProCommand
    index: int = -1

    def apply(self, project: Project) -> None:
        self.index = project._insert_postpro(self.command)

    def revert(self, project: Project) -> None:
        project._drop_postpro(self.index)

    def describe(self) -> str:
        return f"postpro {self.command.name} every {self.command.step}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "add_postpro", "payload": self.command.to_dict()}


@dataclass
class AddLoop:
    loop: Loop
    generated: list[Avatar]

    def apply(self, project: Project) -> None:
        for av in self.generated:
            project._insert_avatar(av)
        project._insert_loop(self.loop)
        if self.loop.group_name:
            project.avatar_groups.setdefault(self.loop.group_name, []).extend(
                self.loop.generated_ids
            )

    def revert(self, project: Project) -> None:
        for av in reversed(self.generated):
            project._drop_avatar(av.avatar_id)
        project._drop_loop(self.loop.loop_id)

    def describe(self) -> str:
        return f"loop {self.loop.loop_type} × {self.loop.count}"

    def to_journal(self) -> dict[str, Any]:
        return {
            "op": "add_loop",
            "payload": {
                "loop": self.loop.to_dict(),
                "generated": [a.to_dict() for a in self.generated],
            },
        }


@dataclass
class SetGroup:
    name: str
    ids: list[str]
    previous: list[str] | None = None

    def apply(self, project: Project) -> None:
        self.previous = list(project.avatar_groups.get(self.name, []))
        project.avatar_groups[self.name] = list(self.ids)

    def revert(self, project: Project) -> None:
        if self.previous:
            project.avatar_groups[self.name] = list(self.previous)
        else:
            project.avatar_groups.pop(self.name, None)

    def describe(self) -> str:
        return f"group {self.name} = {len(self.ids)} ids"

    def to_journal(self) -> dict[str, Any]:
        return {
            "op": "set_group",
            "payload": {
                "name": self.name,
                "ids": list(self.ids),
                "previous": list(self.previous) if self.previous is not None else None,
            },
        }


class CommandHistory:
    def __init__(self, limit: int = 200) -> None:
        self._undo: list[Command] = []
        self._redo: list[Command] = []
        self.limit = limit

    def do(self, cmd: Command, project: Project) -> Command:
        cmd.apply(project)
        self._undo.append(cmd)
        if len(self._undo) > self.limit:
            self._undo.pop(0)
        self._redo.clear()
        return cmd

    def undo(self, project: Project) -> Command:
        if not self._undo:
            raise HistoryError("nothing to undo")
        cmd = self._undo.pop()
        cmd.revert(project)
        self._redo.append(cmd)
        return cmd

    def redo(self, project: Project) -> Command:
        if not self._redo:
            raise HistoryError("nothing to redo")
        cmd = self._redo.pop()
        cmd.apply(project)
        self._undo.append(cmd)
        return cmd

    def journal(self) -> list[dict[str, Any]]:
        return [c.to_journal() for c in self._undo]

    def describe_stack(self) -> list[str]:
        return [c.describe() for c in self._undo]

    def __len__(self) -> int:
        return len(self._undo)


def command_from_journal(entry: dict[str, Any]) -> Command:
    """Rebuild a Command from a journal entry (for save/load). Does not apply it."""
    op = entry.get("op") or entry.get("type") or ""
    payload = entry.get("payload") or {}
    if op == "add_material":
        return AddMaterial(Material.from_dict(payload))
    if op == "add_model":
        return AddModel(Model.from_dict(payload))
    if op == "add_avatar":
        return AddAvatar(Avatar.from_dict(payload))
    if op == "remove_avatar":
        av_data = payload.get("avatar") or payload
        groups = payload.get("groups_touched") or {}
        return RemoveAvatar(Avatar.from_dict(av_data), groups_touched={k: list(v) for k, v in groups.items()})
    if op == "add_population":
        pop_data = payload.get("population") or payload
        cfg_data = payload.get("config")
        cfg = GranuloConfig.from_dict(cfg_data) if cfg_data else None
        return AddPopulation(ParticlePopulation.from_dict(pop_data), cfg)
    if op == "add_law":
        return AddLaw(ContactLaw.from_dict(payload))
    if op == "add_see":
        return AddSeeTable(VisibilityRule.from_dict(payload))
    if op == "add_dof":
        return AddDOF(DOFOperation.from_dict(payload))
    if op == "add_postpro":
        return AddPostPro(PostProCommand.from_dict(payload))
    if op == "add_loop":
        loop_data = payload.get("loop") or payload
        gens = [Avatar.from_dict(a) for a in (payload.get("generated") or [])]
        return AddLoop(Loop.from_dict(loop_data), gens)
    if op == "set_group":
        cmd = SetGroup(str(payload.get("name", "")), list(payload.get("ids") or []))
        prev = payload.get("previous")
        cmd.previous = list(prev) if prev is not None else None
        return cmd
    raise HistoryError(f"unknown journal op {op!r}")


# bind methods onto CommandHistory
def _history_to_dict(self) -> dict[str, Any]:
    return {
        "limit": self.limit,
        "undo": [c.to_journal() for c in self._undo],
        "redo": [c.to_journal() for c in self._redo],
    }


def _history_load_stacks(self, data: dict[str, Any] | None) -> None:
    """Restore undo/redo from saved journal without re-applying commands."""
    if not data:
        self._undo.clear()
        self._redo.clear()
        return
    if "limit" in data:
        self.limit = int(data["limit"])
    undo_entries = list(data.get("undo") or [])
    redo_entries = list(data.get("redo") or [])
    self._undo = []
    self._redo = []
    for entry in undo_entries:
        try:
            self._undo.append(command_from_journal(entry))
        except Exception as exc:
            # skip unreadable entries rather than fail the whole load
            print(f"WARNING: skip history undo entry: {exc}")
    for entry in redo_entries:
        try:
            self._redo.append(command_from_journal(entry))
        except Exception as exc:
            print(f"WARNING: skip history redo entry: {exc}")


CommandHistory.to_dict = _history_to_dict  # type: ignore[attr-defined]
CommandHistory.load_stacks = _history_load_stacks  # type: ignore[attr-defined]
