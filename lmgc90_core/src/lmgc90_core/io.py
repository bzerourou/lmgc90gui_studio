"""`.lmgc90` JSON + `.populations.npz` sidecar. Schema v2 compatible with the GUI."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .entities import (
    Avatar, ContactLaw, DOFOperation, GranuloConfig, Loop, Material, Model,
    PostProCommand, VisibilityRule,
)
from .errors import ValidationError
from .population import ParticlePopulation
from .project import Project
from .types import UnitSystem

SCHEMA_VERSION = 2


def sidecar_path_for(project_filepath: Path) -> Path:
    return project_filepath.with_suffix("").with_suffix(".populations.npz")


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
    np.savez_compressed(npz_path, **arrays)


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
    avatars = [a.to_dict() for a in project.avatars if a.origin.value == "manual"]
    return {
        "schema_version": SCHEMA_VERSION,
        "project_name": project.name,
        "dimension": project.dimension,
        "units": project.units.value,
        "materials": [m.to_dict() for m in project.materials],
        "models": [m.to_dict() for m in project.models],
        "avatars": avatars,
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
        "granulo_generations": [g.to_dict() for g in project.granulo],
        "dynamic_vars": dict(project.dynamic_vars),
        "journal": project.journal(),
    }


def save_project(project: Project, filepath: Path) -> Path:
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    data = project_to_dict(project)
    npz = sidecar_path_for(filepath)
    save_populations_sidecar(project.populations, npz)
    if project.populations:
        data["particle_populations_sidecar"] = npz.name
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filepath


def load_project(filepath: Path) -> Project:
    filepath = Path(filepath)
    with filepath.open(encoding="utf-8") as f:
        data = json.load(f)
    _validate_schema(data, filepath)
    if int(data.get("schema_version", 1)) < 2:
        data = _migrate_v1_to_v2(data)

    pops_meta = list(data.get("particle_populations") or [])
    sidecar = data.get("particle_populations_sidecar")
    if sidecar and pops_meta:
        arrays = load_populations_sidecar(filepath.parent / sidecar)
        merged = []
        for meta in pops_meta:
            pid = meta.get("population_id")
            if pid in arrays:
                centers, radii = arrays[pid]
                item = dict(meta)
                item["centers"] = centers.tolist()
                item["radii"] = radii.tolist()
                merged.append(item)
        pops_meta = merged

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
    for meta in pops_meta:
        if "centers" in meta:
            record_off.populations.append(ParticlePopulation.from_dict(meta))
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
    for raw in data.get("granulo_generations") or []:
        record_off.granulo.append(GranuloConfig.from_dict(raw))
    record_off.dynamic_vars = dict(data.get("dynamic_vars") or {})
    record_off.record = True
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
    from .ids import new_avatar_id

    avatars = data.get("avatars") or []
    idx_to_id: dict[int, str] = {}
    for i, av in enumerate(avatars):
        av.setdefault("avatar_id", new_avatar_id())
        idx_to_id[i] = av["avatar_id"]
    for loop in data.get("loops") or []:
        if "model_avatar_index" in loop:
            loop["model_avatar_id"] = idx_to_id.get(loop.pop("model_avatar_index"), "")
        loop.pop("generated_indices", None)
        loop.setdefault("generated_ids", [])
    for gen in data.get("granulo_generations") or []:
        gen.pop("generated_indices", None)
        gen.setdefault("generated_ids", [])
    groups = {}
    for name, refs in (data.get("avatar_groups") or {}).items():
        mapped = []
        for ref in refs:
            if isinstance(ref, int) and ref in idx_to_id:
                mapped.append(idx_to_id[ref])
            elif isinstance(ref, str):
                mapped.append(ref)
        groups[name] = mapped
    data["avatar_groups"] = groups
    data["schema_version"] = 2
    data["_migrated_from"] = "v1"
    return data
