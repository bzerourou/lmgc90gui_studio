"""`.lmgc90` JSON + `.populations.npz` sidecar. Schema v2 compatible with the GUI.

"""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import tempfile
from typing import Any

import numpy as np

from .entities import (
    Avatar, ContactLaw, DOFOperation, ForLoop, GranuloConfig, Loop, Material,
    Model, PostProCommand, VisibilityRule, jsonable,
)
from .errors import ValidationError
from .commands import AddPopulation, RemoveForLoop, RemovePopulation
from .population import ParticlePopulation
from .project import Project
from .types import UnitSystem

SCHEMA_VERSION = 2


def _array_sha256(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def sidecar_path_for(project_filepath: Path) -> Path:
    return project_filepath.with_suffix(".populations.npz")


def save_populations_sidecar(populations: list[ParticlePopulation], npz_path: Path) -> None:
    if not populations:
        if npz_path.exists():
            npz_path.unlink()
        return
    arrays = {}
    for pop in populations:
        arrays[f"{pop.population_id}__centers"] = pop.centers
        arrays[f"{pop.population_id}__radii"] = pop.radii
    npz_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{npz_path.name}.", suffix=".tmp", dir=npz_path.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            np.savez_compressed(stream, **arrays)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, npz_path)
    finally:
        temp_path.unlink(missing_ok=True)


def load_populations_sidecar(npz_path: Path) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    if not npz_path.exists():
        return {}
    result: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    with np.load(npz_path) as data:
        ids = {
            key.rsplit("__", 1)[0]
            for key in data.files
            if key.endswith("__centers") or key.endswith("__radii")
        }
        for pop_id in ids:
            ck, rk = f"{pop_id}__centers", f"{pop_id}__radii"
            if ck in data.files and rk in data.files:
                result[pop_id] = (data[ck], data[rk])
    return result


def project_to_dict(project: Project) -> dict[str, Any]:
    return jsonable({
        "schema_version": SCHEMA_VERSION,
        "project_name": project.name,
        "dimension": project.dimension,
        "units": project.units.value,
        "materials": [m.to_dict() for m in project.materials],
        "models": [m.to_dict() for m in project.models],
        # Every avatar is written: loops, ForLoops and masonry are NOT
        # re-expanded at load time, so filtering on ``origin`` lost them.
        "avatars": [a.to_dict() for a in project.avatars],
        "particle_populations": [p.to_meta_dict() for p in project.populations],
        "avatar_groups": {
            k: v for k, v in project.avatar_groups.items() if v
        },
        "populations_groups": dict(project.population_groups),
        "contact_laws": [l.to_dict() for l in project.laws],
        "visibility_rules": [v.to_dict() for v in project.visibility],
        "operations": [o.to_dict() for o in project.operations],
        "postpro_commands": [p.to_dict() for p in project.postpro],
        "loops": [lp.to_dict() for lp in project.loops],
        "for_loops": [fl.to_dict() for fl in project.for_loops],
        "granulo_generations": [g.to_dict() for g in project.granulo],
        "history": project.history.to_dict(),
        "dynamic_vars": jsonable(project.dynamic_vars),
    })


def save_project(project: Project, filepath: Path) -> Path:
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    data = project_to_dict(project)
    npz = sidecar_path_for(filepath)
    populations = {pop.population_id: pop for pop in project.populations}
    for command in (*project.history._undo, *project.history._redo):
        if isinstance(command, AddPopulation):
            populations.setdefault(command.population.population_id, command.population)
        elif isinstance(command, RemovePopulation):
            if command.population is not None:
                populations.setdefault(
                    command.population.population_id, command.population,
                )
        elif isinstance(command, RemoveForLoop):
            for _, _, item in command.items:
                if isinstance(item, ParticlePopulation):
                    populations.setdefault(item.population_id, item)
    if populations:
        data["particle_populations_sidecar"] = npz.name
        data["population_sidecar_integrity"] = {
            population_id: {
                "centers_sha256": _array_sha256(population.centers),
                "radii_sha256": _array_sha256(population.radii),
            }
            for population_id, population in populations.items()
        }
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{filepath.name}.", suffix=".tmp", dir=filepath.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        if populations:
            save_populations_sidecar(list(populations.values()), npz)
        os.replace(temp_path, filepath)
    finally:
        temp_path.unlink(missing_ok=True)
    if not populations and npz.exists():
        npz.unlink()
    return filepath


def check_references(project: Project) -> list[str]:
    """Describe references that point to entities absent from *project*."""
    warnings: list[str] = []
    avatar_ids = {a.avatar_id for a in project.avatars}
    population_ids = {p.population_id for p in project.populations}
    populations = {p.population_id: p for p in project.populations}

    def is_known_body(body_id: str) -> bool:
        if body_id in avatar_ids or body_id in population_ids:
            return True
        from .ids import parse_particle_id
        particle = parse_particle_id(body_id)
        return (
            particle is not None
            and particle[0] in populations
            and 0 <= particle[1] < len(populations[particle[0]])
        )

    operation_ids = {op.operation_id for op in project.operations}
    visibility_ids = {rule.visibility_id for rule in project.visibility}
    generation_ids = {config.generation_id for config in project.granulo}
    material_names = {m.name for m in project.materials}
    model_names = {m.name for m in project.models}

    for loop in project.loops:
        missing = [i for i in loop.generated_ids if i not in avatar_ids]
        if missing:
            warnings.append(
                f"loop {loop.loop_id[:8]}: {len(missing)} generated avatar(s) "
                "missing from the file"
            )
        if loop.model_avatar_id and loop.model_avatar_id not in avatar_ids:
            warnings.append(
                f"loop {loop.loop_id[:8]}: template avatar "
                f"{loop.model_avatar_id[:8]} is missing"
            )

    pools = {
        "avatar": avatar_ids, "avatars": avatar_ids,
        "material": material_names, "materials": material_names,
        "model": model_names, "models": model_names,
        "granulo": population_ids,
        "granulo_dist": generation_ids, "distribution": generation_ids,
        "dof": operation_ids, "dofs": operation_ids,
        "visibility": visibility_ids, "see": visibility_ids,
        "see_table": visibility_ids,
    }
    for for_loop in project.for_loops:
        kind = (for_loop.target_kind or "avatar").lower().strip()
        pool = pools.get(kind)
        if pool is None:
            continue
        legacy_ids = (
            kind in ("dof", "dofs", "visibility", "see", "see_table")
            and bool(for_loop.generated_ids)
            and all(str(generated_id).isdigit() for generated_id in for_loop.generated_ids)
        ) or (
            kind in ("granulo_dist", "distribution")
            and bool(for_loop.generated_ids)
            and all(
                str(generated_id).startswith("dist")
                for generated_id in for_loop.generated_ids
            )
        )
        if legacy_ids:
            continue
        missing = [i for i in for_loop.generated_ids if i not in pool]
        if missing:
            warnings.append(
                f"ForLoop {for_loop.loop_id[:8]} [{kind}]: {len(missing)} "
                "generated item(s) missing from the file"
            )

    for name, ids in project.avatar_groups.items():
        missing = [i for i in ids if not is_known_body(i)]
        if missing:
            warnings.append(
                f"group {name!r}: {len(missing)} member(s) missing from the file"
            )

    for op in project.operations:
        if (
            op.target_type == "avatar"
            and not is_known_body(str(op.target_value))
        ):
            warnings.append(
                f"{op.operation_type}: target avatar "
                f"{str(op.target_value)[:8]} is missing"
            )
        elif op.target_type == "group" and op.target_value not in project.avatar_groups:
            warnings.append(
                f"{op.operation_type}: target group {op.target_value!r} is missing"
            )
    return warnings


def _read_sidecar(
    filepath: Path, data: dict, warnings: list[str],
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    name = data.get("particle_populations_sidecar")
    if not name:
        if data.get("particle_populations"):
            warnings.append("project populations are missing a sidecar reference")
        return {}
    # Only the file name counts: the sidecar always lives next to the project.
    npz = filepath.parent / Path(str(name)).name
    if not npz.exists():
        warnings.append(
            f"population sidecar {npz.name!r} not found next to {filepath.name!r}"
        )
        return {}
    try:
        return load_populations_sidecar(npz)
    except Exception as exc:  # corrupt archive: report, do not abort the load
        warnings.append(f"population sidecar {npz.name!r} is unreadable: {exc}")
        return {}


def _load_populations(
    metas: list[dict], arrays: dict[str, tuple[np.ndarray, np.ndarray]],
    warnings: list[str], integrity: dict[str, dict[str, str]] | None = None,
) -> list[ParticlePopulation]:
    populations: list[ParticlePopulation] = []
    for meta in metas:
        pop_id = meta.get("population_id", "?")
        if "centers" in meta:  # legacy: arrays stored inline
            try:
                inline = ParticlePopulation.from_dict(meta)
            except Exception as exc:
                warnings.append(f"population {pop_id}: inline arrays are invalid: {exc}")
                continue
            expected = meta.get("n_particles")
            if expected is not None and len(inline) != int(expected):
                warnings.append(
                    f"population {pop_id}: inline arrays do not match metadata "
                    f"(n_particles={expected}, found {len(inline)}), population skipped"
                )
                continue
            populations.append(inline)
            continue
        if pop_id not in arrays:
            warnings.append(f"population {pop_id}: arrays not found, population skipped")
            continue
        centers, radii = arrays[pop_id]
        expected = meta.get("n_particles")
        if (
            centers.ndim != 2
            or radii.ndim != 1
            or centers.shape[0] != radii.shape[0]
            or (expected is not None and int(expected) != centers.shape[0])
            or (
                meta.get("dimension") is not None
                and int(meta["dimension"]) != centers.shape[1]
            )
        ):
            warnings.append(
                f"population {pop_id}: arrays do not match the metadata "
                f"(n_particles={expected}, centers={centers.shape}, "
                f"radii={radii.shape}), population skipped"
            )
            continue
        fingerprints = (integrity or {}).get(str(pop_id))
        if fingerprints is None:
            warnings.append(
                f"population {pop_id}: sidecar integrity fingerprint missing"
            )
        elif (
            fingerprints.get("centers_sha256") != _array_sha256(centers)
            or fingerprints.get("radii_sha256") != _array_sha256(radii)
        ):
            warnings.append(
                f"population {pop_id}: sidecar integrity check failed, population skipped"
            )
            continue
        populations.append(ParticlePopulation.from_meta_and_arrays(meta, centers, radii))
    return populations


def load_project(filepath: Path) -> Project:
    filepath = Path(filepath)
    with filepath.open(encoding="utf-8") as f:
        data = json.load(f)
    _validate_schema(data, filepath)
    if int(data.get("schema_version", 1)) < 2:
        data = _migrate_v1_to_v2(data)

    warnings: list[str] = list(data.pop("_migration_warnings", []) or [])
    arrays = _read_sidecar(filepath, data, warnings)
    populations = _load_populations(
        list(data.get("particle_populations") or []), arrays, warnings,
        data.get("population_sidecar_integrity"),
    )

    record_off = Project(
        name=data.get("project_name") or "untitled",
        dimension=int(data["dimension"]),
        units=UnitSystem(data.get("units", "SI")),
        record=False,
    )
    for m in data.get("materials") or []:
        record_off.materials.append(Material.from_dict(m))
    for m in data.get("models") or []:
        record_off.models.append(Model.from_dict(m))
    for a in data.get("avatars") or []:
        record_off.avatars.append(Avatar.from_dict(a))
    record_off.populations.extend(populations)
    record_off.avatar_groups = {
        k: list(v) for k, v in (data.get("avatar_groups") or {}).items()
    }
    record_off.population_groups = {
        k: list(v) for k, v in (data.get("populations_groups") or {}).items()
    }
    for raw in data.get("contact_laws") or data.get("tacts") or []:
        record_off.laws.append(ContactLaw.from_dict(raw))
    for raw in data.get("visibility_rules") or data.get("sees") or []:
        record_off.visibility.append(VisibilityRule.from_dict(raw))
    for raw in data.get("operations") or []:
        record_off.operations.append(DOFOperation.from_dict(raw))
    for raw in data.get("postpro_commands") or data.get("postpro_creations") or []:
        record_off.postpro.append(PostProCommand.from_dict(raw))
    for raw in data.get("loops") or []:
        record_off.loops.append(Loop.from_dict(raw))
    for raw in data.get("for_loops") or []:
        record_off.for_loops.append(ForLoop.from_dict(raw))
    for raw in data.get("granulo_generations") or []:
        record_off.granulo.append(GranuloConfig.from_dict(raw))
    _restore_legacy_granulo(record_off, data, warnings)
    record_off.dynamic_vars = dict(data.get("dynamic_vars") or {})
    # Restore undo/redo stacks (commands already reflected in loaded state)
    hist = data.get("history")
    if hist:
        record_off.history.load_stacks(
            hist,
            population_arrays=arrays,
            populations={pop.population_id: pop for pop in populations},
        )
    record_off.record = True
    record_off.load_warnings = warnings + check_references(record_off)
    return record_off


def _validate_schema(data: Any, filepath: Path) -> None:
    if not isinstance(data, dict):
        raise ValidationError(f"{filepath.name} is not a LMGC90 project dict")
    missing = {"project_name", "dimension", "materials", "models", "avatars"} - data.keys()
    if missing:
        raise ValidationError(
            f"{filepath.name} is not a valid .lmgc90 (missing {sorted(missing)})"
        )
    version = int(data.get("schema_version", 1))
    if version > SCHEMA_VERSION:
        raise ValidationError(
            f"{filepath.name} uses schema v{version}, this core speaks v{SCHEMA_VERSION}"
        )
    if data["dimension"] not in (2, 3):
        raise ValidationError(f"invalid dimension {data['dimension']}")


def _migrate_v1_to_v2(data: dict) -> dict:
    from .entities import Avatar, Loop
    from .generate import expand_loop
    from .ids import new_avatar_id, new_population_id, particle_id

    avatars = data.get("avatars") or []
    warnings: list[str] = []
    for i, av in enumerate(avatars):
        av.setdefault("avatar_id", new_avatar_id())

    loops = data.get("loops") or []
    generated_slots: set[int] = set()
    for loop in loops:
        indices = loop.get("generated_indices") or []
        loop["_legacy_generated_indices"] = [
            int(index) for index in indices
            if isinstance(index, int) and not isinstance(index, bool) and index >= 0
        ]
        generated_slots.update(loop["_legacy_generated_indices"])
    for generation in data.get("granulo_generations") or []:
        if generation.get(
            "create_avatars", generation.get("use_particle_population", True),
        ):
            generated_slots.update(
                int(index) for index in generation.get("generated_indices") or []
                if isinstance(index, int)
                and not isinstance(index, bool)
                and index >= 0
            )

    # V1 omitted generated loop avatars. Reconstruct the old body-index layout
    # by placing serialized manual avatars in the slots not owned by a loop.
    slot_count = max(len(avatars) + len(generated_slots), max(generated_slots, default=-1) + 1)
    manual_slots = (
        index for index in range(slot_count) if index not in generated_slots
    )
    index_to_id: dict[int, str] = {}
    for avatar, index in zip(avatars, manual_slots):
        index_to_id[index] = avatar["avatar_id"]

    legacy_dimension = int(data.get("dimension", 2))
    next_generated_slot = slot_count
    claimed_generated_slots: set[int] = set()
    for loop_data in loops:
        loop = Loop.from_dict({
            **loop_data,
            "model_avatar_id": "",
            "generated_ids": [],
        })
        model_index = loop_data.get(
            "model_avatar_index", loop_data.get("model_avatar_id"),
        )
        if isinstance(model_index, int):
            template_id = index_to_id.get(model_index)
        else:
            template_id = str(model_index) if model_index else None
        template_data = next(
            (item for item in avatars if item.get("avatar_id") == template_id),
            None,
        )
        if template_data is None:
            warnings.append(
                f"loop {loop_data.get('loop_id', '?')}: template avatar index "
                f"{model_index!r} could not be resolved; generated avatars were not restored"
            )
            loop_data["model_avatar_id"] = template_id or ""
            loop_data["generated_ids"] = []
            loop_data.pop("model_avatar_index", None)
            loop_data.pop("generated_indices", None)
            loop_data.pop("_legacy_generated_indices", None)
            continue

        loop.model_avatar_id = template_id
        generated = expand_loop(
            loop, Avatar.from_dict(template_data), dimension=legacy_dimension,
        )
        old_indices = loop_data["_legacy_generated_indices"]
        if len(old_indices) != len(generated):
            warnings.append(
                f"loop {loop.loop_id[:8]}: regenerated {len(generated)} avatars; "
                f"legacy file listed {len(old_indices)} generated indices"
            )
        for offset, avatar in enumerate(generated):
            if offset < len(old_indices):
                old_index = old_indices[offset]
            else:
                while next_generated_slot in index_to_id:
                    next_generated_slot += 1
                old_index = next_generated_slot
                next_generated_slot += 1
            if old_index in index_to_id or old_index in claimed_generated_slots:
                warnings.append(
                    f"loop {loop.loop_id[:8]}: legacy body index {old_index} "
                    "was already assigned"
                )
                continue
            index_to_id[old_index] = avatar.avatar_id
            claimed_generated_slots.add(old_index)
            avatars.append(avatar.to_dict())
        loop_data["model_avatar_id"] = loop.model_avatar_id
        loop_data["generated_ids"] = list(loop.generated_ids)
        loop_data.pop("model_avatar_index", None)
        loop_data.pop("generated_indices", None)
        loop_data.pop("_legacy_generated_indices", None)

    for generation in data.get("granulo_generations") or []:
        indices = generation.pop("generated_indices", None) or []
        population_id = generation.get("population_id")
        if generation.get("create_avatars", generation.get("use_particle_population", True)):
            population_id = population_id or new_population_id()
            generation["population_id"] = population_id
            for index, particle_index in enumerate(indices):
                if (
                    isinstance(particle_index, int)
                    and not isinstance(particle_index, bool)
                    and particle_index >= 0
                ):
                    if particle_index in index_to_id:
                        warnings.append(
                            f"granulo population {population_id}: legacy body index "
                            f"{particle_index} conflicts with another migrated body"
                        )
                    else:
                        index_to_id[particle_index] = particle_id(population_id, index)
        generation.pop("_legacy_generated_indices", None)

    migrated_operations = []
    for operation in data.get("operations") or []:
        if "body_index" not in operation:
            migrated_operations.append(operation)
            continue
        body_index = operation.pop("body_index")
        try:
            body_index = int(body_index)
        except (TypeError, ValueError):
            body_index = -1
        avatar_id = index_to_id.get(body_index)
        if avatar_id is None:
            warnings.append(
                f"{operation.get('type', 'DOF operation')}: legacy body index "
                f"{body_index} could not be resolved; operation was skipped"
            )
            continue
        operation["target"] = "avatar"
        operation["target_value"] = avatar_id
        migrated_operations.append(operation)
    data["operations"] = migrated_operations

    groups = {}
    for name, refs in (data.get("avatar_groups") or {}).items():
        mapped = []
        for ref in refs:
            if isinstance(ref, int) and ref in index_to_id:
                mapped.append(index_to_id[ref])
            elif isinstance(ref, str):
                mapped.append(ref)
            else:
                warnings.append(
                    f"group {name!r}: legacy member index {ref!r} could not be resolved"
                )
        groups[name] = mapped
    data["avatar_groups"] = groups
    data["schema_version"] = 2
    data["_migrated_from"] = "v1"
    data["_migration_warnings"] = warnings
    return data


def _restore_legacy_granulo(
    project: Project, data: dict[str, Any], warnings: list[str],
) -> None:
    if data.get("_migrated_from") != "v1":
        return
    from .generate import NumpyGranulo, sample_radii
    from .ids import new_population_id

    populations = {population.population_id for population in project.populations}
    for config in project.granulo:
        if not config.create_avatars:
            if config.radii is None:
                try:
                    config.radii = [
                        float(radius) for radius in sample_radii(config)
                    ]
                    warnings.append(
                        f"granulo {config.generation_id[:8]}: distribution radii "
                        "were regenerated from the stored configuration"
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    warnings.append(
                        f"granulo {config.generation_id[:8]}: distribution could "
                        f"not be regenerated: {exc}"
                    )
            continue

        population_id = config.population_id
        if population_id in populations:
            continue
        expected_id = population_id or new_population_id()
        try:
            result = NumpyGranulo().deposit(config)
            result.population.population_id = expected_id
            config.population_id = expected_id
            project.populations.append(result.population)
            populations.add(expected_id)
            if config.group_name:
                project.population_groups.setdefault(
                    config.group_name, [],
                ).append(expected_id)
                project.avatar_groups.setdefault(config.group_name, []).append(
                    expected_id,
                )
            warnings.append(
                f"population {expected_id}: regenerated from stored granulo "
                "configuration because its saved arrays were unavailable"
            )
        except (KeyError, TypeError, ValueError) as exc:
            warnings.append(
                f"population {expected_id}: could not be regenerated from "
                f"granulo configuration: {exc}"
            )