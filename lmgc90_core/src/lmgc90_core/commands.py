"""Command history — undo that a DEM researcher can actually use.

Granularity:
  - one entity (material, avatar, law, DOF) = one command
  - a whole ParticlePopulation = one command (never N avatars)
  - a Loop or ForLoop expansion = one command
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from .entities import (
    Avatar, ContactLaw, DOFOperation, ForLoop, GranuloConfig, Loop, Material,
    Model, PostProCommand, VisibilityRule,
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
class UpdateAvatar:
    old: Avatar
    new: Avatar

    def apply(self, project: Project) -> None:
        project._replace_avatar(self.old.avatar_id, self.new)

    def revert(self, project: Project) -> None:
        project._replace_avatar(self.new.avatar_id, self.old)

    def describe(self) -> str:
        return f"update avatar {self.old.avatar_id[:8]}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "update_avatar", "payload": {
            "old": self.old.to_dict(), "new": self.new.to_dict(),
        }}


@dataclass
class AddAvatarBatch:
    avatars: list[Avatar]
    group_name: str | None = None
    previous_group: list[str] | None = None
    _captured: bool = False

    def apply(self, project: Project) -> None:
        for avatar in self.avatars:
            project._insert_avatar(avatar)
        if self.group_name:
            if not self._captured:
                previous = project.avatar_groups.get(self.group_name)
                self.previous_group = list(previous) if previous is not None else None
                self._captured = True
            project.avatar_groups.setdefault(self.group_name, []).extend(
                avatar.avatar_id for avatar in self.avatars
            )

    def revert(self, project: Project) -> None:
        for avatar in reversed(self.avatars):
            project._drop_avatar(avatar.avatar_id)
        if self.group_name:
            if self.previous_group is None:
                project.avatar_groups.pop(self.group_name, None)
            else:
                project.avatar_groups[self.group_name] = list(self.previous_group)

    def describe(self) -> str:
        return f"add {len(self.avatars)} masonry avatars"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "add_avatar_batch", "payload": {
            "avatars": [avatar.to_dict() for avatar in self.avatars],
            "group_name": self.group_name,
            "previous_group": self.previous_group,
            "captured": self._captured,
        }}


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
                "population": self.population.to_meta_dict(),
                "config": self.config.to_dict() if self.config is not None else None,
            },
        }


@dataclass
class AddGranuloConfig:
    config: GranuloConfig
    index: int = -1

    def apply(self, project: Project) -> None:
        self.index = len(project.granulo)
        project.granulo.append(self.config)

    def revert(self, project: Project) -> None:
        if 0 <= self.index < len(project.granulo):
            project.granulo.pop(self.index)

    def describe(self) -> str:
        return f"add granulo distribution n={self.config.nb_particles}"

    def to_journal(self) -> dict[str, Any]:
        return {
            "op": "add_granulo_config",
            "payload": {"config": self.config.to_dict(), "index": self.index},
        }


@dataclass
class AddLaw:
    law: ContactLaw

    def apply(self, project: Project) -> None:
        project._insert_law(self.law)

    def revert(self, project: Project) -> None:
        project._drop_law(self.law.name)

    def describe(self) -> str:
        return f"add law {self.law.name} ({self.law.law_type_name})"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "add_law", "payload": self.law.to_dict()}


@dataclass
class UpdateMaterial:
    old: Material
    new: Material

    def apply(self, project: Project) -> None:
        project._replace_material(self.old.name, self.new)

    def revert(self, project: Project) -> None:
        project._replace_material(self.new.name, self.old)

    def describe(self) -> str:
        return f"update material {self.old.name} -> {self.new.name}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "update_material", "payload": {
            "old": self.old.to_dict(), "new": self.new.to_dict(),
        }}


@dataclass
class RemoveMaterial:
    material: Material
    index: int = -1

    def apply(self, project: Project) -> None:
        self.index = next(
            (i for i, item in enumerate(project.materials) if item.name == self.material.name),
            -1,
        )
        if self.index < 0:
            raise HistoryError(f"material {self.material.name!r} not found")
        project.materials.pop(self.index)

    def revert(self, project: Project) -> None:
        project.materials.insert(self.index, self.material)

    def describe(self) -> str:
        return f"remove material {self.material.name}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "remove_material", "payload": {
            "material": self.material.to_dict(), "index": self.index,
        }}


@dataclass
class UpdateModel:
    old: Model
    new: Model

    def apply(self, project: Project) -> None:
        project._replace_model(self.old.name, self.new)

    def revert(self, project: Project) -> None:
        project._replace_model(self.new.name, self.old)

    def describe(self) -> str:
        return f"update model {self.old.name} -> {self.new.name}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "update_model", "payload": {
            "old": self.old.to_dict(), "new": self.new.to_dict(),
        }}


@dataclass
class RemoveModel:
    model: Model
    index: int = -1

    def apply(self, project: Project) -> None:
        self.index = next(
            (i for i, item in enumerate(project.models) if item.name == self.model.name),
            -1,
        )
        if self.index < 0:
            raise HistoryError(f"model {self.model.name!r} not found")
        project.models.pop(self.index)

    def revert(self, project: Project) -> None:
        project.models.insert(self.index, self.model)

    def describe(self) -> str:
        return f"remove model {self.model.name}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "remove_model", "payload": {
            "model": self.model.to_dict(), "index": self.index,
        }}


@dataclass
class UpdateLaw:
    old: ContactLaw
    new: ContactLaw

    def apply(self, project: Project) -> None:
        project._replace_law(self.old.name, self.new)

    def revert(self, project: Project) -> None:
        project._replace_law(self.new.name, self.old)

    def describe(self) -> str:
        return f"update law {self.old.name} -> {self.new.name}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "update_law", "payload": {
            "old": self.old.to_dict(), "new": self.new.to_dict(),
        }}


@dataclass
class RemoveLaw:
    law: ContactLaw
    index: int = -1

    def apply(self, project: Project) -> None:
        self.index = next(
            (i for i, item in enumerate(project.laws) if item.name == self.law.name),
            -1,
        )
        if self.index < 0:
            raise HistoryError(f"law {self.law.name!r} not found")
        project.laws.pop(self.index)

    def revert(self, project: Project) -> None:
        project.laws.insert(self.index, self.law)

    def describe(self) -> str:
        return f"remove law {self.law.name}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "remove_law", "payload": {
            "law": self.law.to_dict(), "index": self.index,
        }}


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
class UpdateSeeTable:
    index: int
    old: VisibilityRule
    new: VisibilityRule

    def apply(self, project: Project) -> None:
        project._replace_see(self.index, self.new)

    def revert(self, project: Project) -> None:
        project._replace_see(self.index, self.old)

    def describe(self) -> str:
        return f"update see table {self.index}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "update_see", "payload": {
            "index": self.index,
            "old": self.old.to_dict(),
            "new": self.new.to_dict(),
        }}


@dataclass
class RemoveSeeTable:
    rule: VisibilityRule
    index: int = -1

    def apply(self, project: Project) -> None:
        if self.index < 0:
            self.index = next(
                (i for i, item in enumerate(project.visibility) if item is self.rule),
                -1,
            )
        if self.index < 0 or self.index >= len(project.visibility):
            raise HistoryError("visibility rule not found")
        project._drop_see(self.index)

    def revert(self, project: Project) -> None:
        project.visibility.insert(min(self.index, len(project.visibility)), self.rule)

    def describe(self) -> str:
        return f"remove see table {self.index}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "remove_see", "payload": {
            "rule": self.rule.to_dict(), "index": self.index,
        }}


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
class UpdateDOF:
    index: int
    old: DOFOperation
    new: DOFOperation

    def apply(self, project: Project) -> None:
        project._replace_dof(self.index, self.new)

    def revert(self, project: Project) -> None:
        project._replace_dof(self.index, self.old)

    def describe(self) -> str:
        return f"update DOF {self.index}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "update_dof", "payload": {
            "index": self.index,
            "old": self.old.to_dict(),
            "new": self.new.to_dict(),
        }}


@dataclass
class RemoveDOF:
    operation: DOFOperation
    index: int = -1

    def apply(self, project: Project) -> None:
        if self.index < 0:
            self.index = next(
                (i for i, item in enumerate(project.operations)
                 if item is self.operation),
                -1,
            )
        if self.index < 0 or self.index >= len(project.operations):
            raise HistoryError("DOF operation not found")
        project._drop_dof(self.index)

    def revert(self, project: Project) -> None:
        project.operations.insert(min(self.index, len(project.operations)), self.operation)

    def describe(self) -> str:
        return f"remove DOF {self.index}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "remove_dof", "payload": {
            "operation": self.operation.to_dict(), "index": self.index,
        }}


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
class AddForLoop:
    for_loop: ForLoop

    def apply(self, project: Project) -> None:
        if not any(item.loop_id == self.for_loop.loop_id for item in project.for_loops):
            project.for_loops.append(self.for_loop)

    def revert(self, project: Project) -> None:
        project.for_loops[:] = [
            item for item in project.for_loops
            if item.loop_id != self.for_loop.loop_id
        ]

    def describe(self) -> str:
        return f"add ForLoop [{self.for_loop.target_kind}]"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "add_for_loop", "payload": self.for_loop.to_dict()}


@dataclass
class RemoveLoop:
    loop: Loop
    generated: list[Avatar]
    avatar_positions: list[tuple[int, Avatar]] = field(default_factory=list)
    loop_index: int = -1
    groups_touched: dict[str, list[str]] = field(default_factory=dict)
    operations_touched: list[tuple[int, DOFOperation]] = field(default_factory=list)
    _captured: bool = False

    def apply(self, project: Project) -> None:
        generated_ids = set(self.loop.generated_ids)
        if not self._captured:
            self.avatar_positions = [
                (index, avatar)
                for index, avatar in enumerate(project.avatars)
                if avatar.avatar_id in generated_ids
            ]
            self.loop_index = next(
                (
                    index for index, loop in enumerate(project.loops)
                    if loop.loop_id == self.loop.loop_id
                ),
                -1,
            )
            self.groups_touched = {
                name: list(ids)
                for name, ids in project.avatar_groups.items()
                if generated_ids.intersection(ids)
            }
            self.operations_touched = [
                (index, operation)
                for index, operation in enumerate(project.operations)
                if operation.target_type == "avatar"
                and operation.target_value in generated_ids
            ]
            self._captured = True

        for avatar_id in generated_ids:
            project._drop_avatar(avatar_id)
        project._drop_loop(self.loop.loop_id)

    def revert(self, project: Project) -> None:
        for index, avatar in self.avatar_positions:
            project.avatars.insert(min(index, len(project.avatars)), avatar)
        if self.loop_index >= 0:
            project.loops.insert(min(self.loop_index, len(project.loops)), self.loop)
        for name, ids in self.groups_touched.items():
            project.avatar_groups[name] = list(ids)
        for index, operation in self.operations_touched:
            project.operations.insert(min(index, len(project.operations)), operation)

    def describe(self) -> str:
        return f"remove loop {self.loop.loop_type} × {self.loop.count}"

    def to_journal(self) -> dict[str, Any]:
        return {
            "op": "remove_loop",
            "payload": {
                "loop": self.loop.to_dict(),
                "generated": [avatar.to_dict() for avatar in self.generated],
                "avatar_positions": [
                    {"index": index, "avatar": avatar.to_dict()}
                    for index, avatar in self.avatar_positions
                ],
                "loop_index": self.loop_index,
                "groups_touched": {
                    name: list(ids) for name, ids in self.groups_touched.items()
                },
                "operations_touched": [
                    {"index": index, "operation": operation.to_dict()}
                    for index, operation in self.operations_touched
                ],
            },
        }


@dataclass
class RemoveForLoop:
    for_loop: ForLoop
    items: list[tuple[str, int, Any]] = field(default_factory=list)
    loop_index: int = -1
    avatar_groups_touched: dict[str, list[str]] = field(default_factory=dict)
    population_groups_touched: dict[str, list[str]] = field(default_factory=dict)
    granulo_touched: list[tuple[int, GranuloConfig]] = field(default_factory=list)
    operations_touched: list[tuple[int, DOFOperation]] = field(default_factory=list)
    _captured: bool = False

    def apply(self, project: Project) -> None:
        kind = self.for_loop.target_kind.lower().strip()
        collection_name = {
            "avatar": "avatars",
            "avatars": "avatars",
            "material": "materials",
            "materials": "materials",
            "model": "models",
            "models": "models",
            "law": "laws",
            "laws": "laws",
            "contact": "laws",
            "contact_law": "laws",
            "contact_laws": "laws",
            "dof": "operations",
            "dofs": "operations",
            "visibility": "visibility",
            "see": "visibility",
            "see_table": "visibility",
            "granulo": "populations",
            "granulo_dist": "granulo",
            "distribution": "granulo",
        }.get(kind)
        if collection_name is None:
            raise ValueError(f"unsupported ForLoop target kind {kind!r}")

        if not self._captured:
            self.loop_index = next(
                (
                    index for index, item in enumerate(project.for_loops)
                    if item.loop_id == self.for_loop.loop_id
                ),
                -1,
            )
            collection = getattr(project, collection_name)
            generated_ids = set(self.for_loop.generated_ids)
            if not generated_ids and self.for_loop._generated_items:
                for item in self.for_loop._generated_items:
                    if hasattr(item, "avatar_id"):
                        generated_ids.add(item.avatar_id)
                    elif hasattr(item, "name"):
                        generated_ids.add(item.name)
                    elif hasattr(item, "population_id"):
                        generated_ids.add(item.population_id)
                    elif hasattr(item, "target_value"):
                        generated_ids.add(str(item.target_value))

            def is_generated(item: Any, index: int) -> bool:
                if hasattr(item, "avatar_id"):
                    return item.avatar_id in generated_ids
                if hasattr(item, "name"):
                    return item.name in generated_ids
                if hasattr(item, "population_id"):
                    return item.population_id in generated_ids
                if hasattr(item, "target_value"):
                    return (
                        str(item.target_value) in generated_ids
                        or str(index) in generated_ids
                    )
                return str(index) in generated_ids

            self.items = [
                (collection_name, index, item)
                for index, item in enumerate(collection)
                if is_generated(item, index)
            ]
            if collection_name == "avatars":
                generated_ids = {item.avatar_id for _, _, item in self.items}
                self.avatar_groups_touched = {
                    name: list(ids)
                    for name, ids in project.avatar_groups.items()
                    if generated_ids.intersection(ids)
                }
                emptied_groups = {
                    name for name, ids in self.avatar_groups_touched.items()
                    if not set(ids).difference(generated_ids)
                }
                self.operations_touched = [
                    (index, operation)
                    for index, operation in enumerate(project.operations)
                    if (
                        operation.target_type == "avatar"
                        and operation.target_value in generated_ids
                    ) or (
                        operation.target_type == "group"
                        and operation.target_value in emptied_groups
                    )
                ]
            elif collection_name == "populations":
                generated_ids = {item.population_id for _, _, item in self.items}
                self.avatar_groups_touched = {
                    name: list(ids)
                    for name, ids in project.avatar_groups.items()
                    if generated_ids.intersection(ids)
                }
                self.population_groups_touched = {
                    name: list(ids)
                    for name, ids in project.population_groups.items()
                    if generated_ids.intersection(ids)
                }
                self.granulo_touched = [
                    (index, config)
                    for index, config in enumerate(project.granulo)
                    if config.population_id in generated_ids
                ]
            self._captured = True

        if collection_name == "avatars":
            for _, _, avatar in self.items:
                project._drop_avatar(avatar.avatar_id)
            touched_operation_ids = {id(operation) for _, operation in self.operations_touched}
            project.operations[:] = [
                operation for operation in project.operations
                if id(operation) not in touched_operation_ids
            ]
        elif collection_name == "populations":
            for _, _, population in self.items:
                project._drop_population(population.population_id)
        else:
            collection = getattr(project, collection_name)
            for _, index, _ in reversed(self.items):
                collection.pop(index)
        if collection_name != "populations":
            for index, config in reversed(self.granulo_touched):
                project.granulo.pop(index)
        project.for_loops[:] = [
            item for item in project.for_loops
            if item.loop_id != self.for_loop.loop_id
        ]

    def revert(self, project: Project) -> None:
        for collection_name, index, item in self.items:
            collection = getattr(project, collection_name)
            collection.insert(min(index, len(collection)), item)
        self.for_loop._generated_items = [item for _, _, item in self.items]
        for index, config in self.granulo_touched:
            project.granulo.insert(min(index, len(project.granulo)), config)
        if self.loop_index >= 0:
            project.for_loops.insert(
                min(self.loop_index, len(project.for_loops)), self.for_loop
            )
        project.avatar_groups.update({
            name: list(ids) for name, ids in self.avatar_groups_touched.items()
        })
        project.population_groups.update({
            name: list(ids) for name, ids in self.population_groups_touched.items()
        })
        for index, operation in self.operations_touched:
            project.operations.insert(min(index, len(project.operations)), operation)

    def describe(self) -> str:
        return f"remove ForLoop [{self.for_loop.target_kind}]"

    def to_journal(self) -> dict[str, Any]:
        type_names = {
            Avatar: "Avatar",
            Material: "Material",
            Model: "Model",
            ContactLaw: "ContactLaw",
            DOFOperation: "DOFOperation",
            VisibilityRule: "VisibilityRule",
            ParticlePopulation: "ParticlePopulation",
            GranuloConfig: "GranuloConfig",
        }
        return {
            "op": "remove_for_loop",
            "payload": {
                "for_loop": self.for_loop.to_dict(),
                "items": [
                    {
                        "collection": collection,
                        "index": index,
                        "type": type_names[type(item)],
                        "item": (
                            item.to_meta_dict()
                            if isinstance(item, ParticlePopulation)
                            else item.to_dict()
                        ),
                    }
                    for collection, index, item in self.items
                ],
                "loop_index": self.loop_index,
                "avatar_groups_touched": {
                    name: list(ids) for name, ids in self.avatar_groups_touched.items()
                },
                "population_groups_touched": {
                    name: list(ids)
                    for name, ids in self.population_groups_touched.items()
                },
                "granulo_touched": [
                    {"index": index, "config": config.to_dict()}
                    for index, config in self.granulo_touched
                ],
                "operations_touched": [
                    {"index": index, "operation": operation.to_dict()}
                    for index, operation in self.operations_touched
                ],
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


@dataclass
class RemoveGroup:
    name: str
    avatar_ids: list[str] | None = None
    population_ids: list[str] | None = None
    _captured: bool = False

    def apply(self, project: Project) -> None:
        if not self._captured:
            avatar_ids = project.avatar_groups.get(self.name)
            population_ids = project.population_groups.get(self.name)
            self.avatar_ids = list(avatar_ids) if avatar_ids is not None else None
            self.population_ids = (
                list(population_ids) if population_ids is not None else None
            )
            self._captured = True
        project.avatar_groups.pop(self.name, None)
        project.population_groups.pop(self.name, None)

    def revert(self, project: Project) -> None:
        if self.avatar_ids is not None:
            project.avatar_groups[self.name] = list(self.avatar_ids)
        if self.population_ids is not None:
            project.population_groups[self.name] = list(self.population_ids)

    def describe(self) -> str:
        return f"remove group {self.name}"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "remove_group", "payload": {
            "name": self.name,
            "avatar_ids": self.avatar_ids,
            "population_ids": self.population_ids,
            "captured": self._captured,
        }}


@dataclass
class CompositeCommand:
    commands: list[Command]

    def apply(self, project: Project) -> None:
        applied: list[Command] = []
        try:
            for command in self.commands:
                command.apply(project)
                applied.append(command)
        except Exception:
            for command in reversed(applied):
                command.revert(project)
            raise

    def revert(self, project: Project) -> None:
        reverted: list[Command] = []
        try:
            for command in reversed(self.commands):
                command.revert(project)
                reverted.append(command)
        except Exception:
            for command in reversed(reverted):
                command.apply(project)
            raise

    def describe(self) -> str:
        return self.commands[-1].describe() if self.commands else "empty transaction"

    def to_journal(self) -> dict[str, Any]:
        return {"op": "composite", "payload": {
            "commands": [command.to_journal() for command in self.commands],
        }}


class CommandHistory:
    def __init__(self, limit: int = 200) -> None:
        self._undo: list[Command] = []
        self._redo: list[Command] = []
        self.limit = limit

    def do(self, cmd: Command, project: Project) -> Command:
        cmd.apply(project)
        self.record_applied(cmd)
        return cmd

    def record_applied(self, cmd: Command) -> None:
        self._undo.append(cmd)
        if len(self._undo) > self.limit:
            self._undo.pop(0)
        self._redo.clear()

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


def command_from_journal(
    entry: dict[str, Any],
    population_arrays: dict[str, tuple[Any, Any]] | None = None,
    populations: dict[str, ParticlePopulation] | None = None,
) -> Command:
    """Rebuild a Command from a journal entry (for save/load). Does not apply it."""
    op = entry.get("op") or entry.get("type") or ""
    payload = entry.get("payload") or {}

    def population_from_data(data: dict[str, Any]) -> ParticlePopulation:
        if "centers" in data and "radii" in data:
            return ParticlePopulation.from_dict(data)
        population_id = str(data.get("population_id", ""))
        if populations and population_id in populations:
            return populations[population_id]
        arrays = (population_arrays or {}).get(population_id)
        if arrays is not None:
            return ParticlePopulation.from_meta_and_arrays(data, *arrays)
        raise HistoryError(
            f"population arrays for history entry {population_id!r} are missing"
        )

    if op == "add_material":
        return AddMaterial(Material.from_dict(payload))
    if op == "add_model":
        return AddModel(Model.from_dict(payload))
    if op == "update_material":
        return UpdateMaterial(
            Material.from_dict(payload["old"]), Material.from_dict(payload["new"]),
        )
    if op == "remove_material":
        return RemoveMaterial(
            Material.from_dict(payload["material"]), int(payload.get("index", -1)),
        )
    if op == "update_model":
        return UpdateModel(
            Model.from_dict(payload["old"]), Model.from_dict(payload["new"]),
        )
    if op == "remove_model":
        return RemoveModel(
            Model.from_dict(payload["model"]), int(payload.get("index", -1)),
        )
    if op == "add_avatar":
        return AddAvatar(Avatar.from_dict(payload))
    if op == "update_avatar":
        return UpdateAvatar(
            Avatar.from_dict(payload["old"]), Avatar.from_dict(payload["new"]),
        )
    if op == "add_avatar_batch":
        return AddAvatarBatch(
            avatars=[Avatar.from_dict(item) for item in payload.get("avatars") or []],
            group_name=payload.get("group_name"),
            previous_group=(
                list(payload["previous_group"])
                if payload.get("previous_group") is not None else None
            ),
            _captured=bool(payload.get("captured", False)),
        )
    if op == "remove_avatar":
        av_data = payload.get("avatar") or payload
        groups = payload.get("groups_touched") or {}
        return RemoveAvatar(Avatar.from_dict(av_data), groups_touched={k: list(v) for k, v in groups.items()})
    if op == "add_population":
        pop_data = payload.get("population") or payload
        cfg_data = payload.get("config")
        cfg = GranuloConfig.from_dict(cfg_data) if cfg_data else None
        return AddPopulation(population_from_data(pop_data), cfg)
    if op == "add_granulo_config":
        return AddGranuloConfig(
            GranuloConfig.from_dict(payload["config"]),
            int(payload.get("index", -1)),
        )
    if op == "add_law":
        return AddLaw(ContactLaw.from_dict(payload))
    if op == "update_law":
        return UpdateLaw(
            ContactLaw.from_dict(payload["old"]), ContactLaw.from_dict(payload["new"]),
        )
    if op == "remove_law":
        return RemoveLaw(
            ContactLaw.from_dict(payload["law"]), int(payload.get("index", -1)),
        )
    if op == "add_see":
        return AddSeeTable(VisibilityRule.from_dict(payload))
    if op == "update_see":
        return UpdateSeeTable(
            int(payload["index"]),
            VisibilityRule.from_dict(payload["old"]),
            VisibilityRule.from_dict(payload["new"]),
        )
    if op == "remove_see":
        return RemoveSeeTable(
            VisibilityRule.from_dict(payload["rule"]),
            int(payload.get("index", -1)),
        )
    if op == "add_dof":
        return AddDOF(DOFOperation.from_dict(payload))
    if op == "update_dof":
        return UpdateDOF(
            int(payload["index"]),
            DOFOperation.from_dict(payload["old"]),
            DOFOperation.from_dict(payload["new"]),
        )
    if op == "remove_dof":
        return RemoveDOF(
            DOFOperation.from_dict(payload["operation"]),
            int(payload.get("index", -1)),
        )
    if op == "add_postpro":
        return AddPostPro(PostProCommand.from_dict(payload))
    if op == "add_loop":
        loop_data = payload.get("loop") or payload
        gens = [Avatar.from_dict(a) for a in (payload.get("generated") or [])]
        return AddLoop(Loop.from_dict(loop_data), gens)
    if op == "add_for_loop":
        return AddForLoop(ForLoop.from_dict(payload))
    if op == "composite":
        return CompositeCommand([
            command_from_journal(item, population_arrays, populations)
            for item in payload.get("commands") or []
        ])
    if op == "remove_loop":
        loop_data = payload.get("loop") or {}
        gens = [Avatar.from_dict(a) for a in (payload.get("generated") or [])]
        avatar_positions = [
            (int(item["index"]), Avatar.from_dict(item["avatar"]))
            for item in payload.get("avatar_positions") or []
        ]
        operations_touched = [
            (int(item["index"]), DOFOperation.from_dict(item["operation"]))
            for item in payload.get("operations_touched") or []
        ]
        return RemoveLoop(
            loop=Loop.from_dict(loop_data),
            generated=gens,
            avatar_positions=avatar_positions,
            loop_index=int(payload.get("loop_index", -1)),
            groups_touched={
                name: list(ids)
                for name, ids in (payload.get("groups_touched") or {}).items()
            },
            operations_touched=operations_touched,
            _captured=True,
        )
    if op == "remove_for_loop":
        from .entities import ForLoop

        item_types = {
            "Avatar": Avatar.from_dict,
            "Material": Material.from_dict,
            "Model": Model.from_dict,
            "ContactLaw": ContactLaw.from_dict,
            "DOFOperation": DOFOperation.from_dict,
            "VisibilityRule": VisibilityRule.from_dict,
            "GranuloConfig": GranuloConfig.from_dict,
        }
        items = [
            (
                str(item["collection"]),
                int(item["index"]),
                (
                    population_from_data(item["item"])
                    if item["type"] == "ParticlePopulation"
                    else item_types[item["type"]](item["item"])
                ),
            )
            for item in payload.get("items") or []
        ]
        return RemoveForLoop(
            for_loop=ForLoop.from_dict(payload.get("for_loop") or {}),
            items=items,
            loop_index=int(payload.get("loop_index", -1)),
            avatar_groups_touched={
                name: list(ids)
                for name, ids in (payload.get("avatar_groups_touched") or {}).items()
            },
            population_groups_touched={
                name: list(ids)
                for name, ids in (payload.get("population_groups_touched") or {}).items()
            },
            granulo_touched=[
                (int(item["index"]), GranuloConfig.from_dict(item["config"]))
                for item in payload.get("granulo_touched") or []
            ],
            operations_touched=[
                (int(item["index"]), DOFOperation.from_dict(item["operation"]))
                for item in payload.get("operations_touched") or []
            ],
            _captured=True,
        )
    if op == "set_group":
        cmd = SetGroup(str(payload.get("name", "")), list(payload.get("ids") or []))
        prev = payload.get("previous")
        cmd.previous = list(prev) if prev is not None else None
        return cmd
    if op == "remove_group":
        return RemoveGroup(
            name=str(payload.get("name", "")),
            avatar_ids=(
                list(payload["avatar_ids"])
                if payload.get("avatar_ids") is not None else None
            ),
            population_ids=(
                list(payload["population_ids"])
                if payload.get("population_ids") is not None else None
            ),
            _captured=bool(payload.get("captured", False)),
        )
    raise HistoryError(f"unknown journal op {op!r}")


# bind methods onto CommandHistory
def _history_to_dict(self) -> dict[str, Any]:
    return {
        "limit": self.limit,
        "undo": [c.to_journal() for c in self._undo],
        "redo": [c.to_journal() for c in self._redo],
    }


def _history_load_stacks(
    self,
    data: dict[str, Any] | None,
    population_arrays: dict[str, tuple[Any, Any]] | None = None,
    populations: dict[str, ParticlePopulation] | None = None,
) -> None:
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
            self._undo.append(
                command_from_journal(entry, population_arrays, populations)
            )
        except Exception as exc:
            # skip unreadable entries rather than fail the whole load
            print(f"WARNING: skip history undo entry: {exc}")
    for entry in redo_entries:
        try:
            self._redo.append(
                command_from_journal(entry, population_arrays, populations)
            )
        except Exception as exc:
            print(f"WARNING: skip history redo entry: {exc}")


CommandHistory.to_dict = _history_to_dict  # type: ignore[attr-defined]
CommandHistory.load_stacks = _history_load_stacks  # type: ignore[attr-defined]
