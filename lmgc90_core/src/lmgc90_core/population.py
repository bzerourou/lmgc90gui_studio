"""SoA particle population — the default for mass generation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from .entities import Avatar
from .ids import new_population_id, particle_id
from .types import POPULATION_TYPES, AvatarOrigin, AvatarType


@dataclass
class ParticlePopulation:
    population_id: str
    avatar_type: AvatarType
    material_name: str
    model_name: str
    color: str
    origin: AvatarOrigin
    dimension: int
    centers: np.ndarray = field(repr=False)
    radii: np.ndarray = field(repr=False)
    group_name: Optional[str] = None
    extra_params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        avatar_type: AvatarType | str,
        material_name: str,
        model_name: str,
        centers,
        radii,
        color: str = "BLUEx",
        origin: AvatarOrigin | str = AvatarOrigin.GRANULO,
        group_name: Optional[str] = None,
        population_id: Optional[str] = None,
        extra_params: Optional[dict[str, Any]] = None,
    ) -> ParticlePopulation:
        atype = avatar_type if isinstance(avatar_type, AvatarType) else AvatarType(avatar_type)
        origin_e = origin if isinstance(origin, AvatarOrigin) else AvatarOrigin(origin)
        centers_a = np.asarray(centers, dtype=np.float64)
        radii_a = np.asarray(radii, dtype=np.float64)

        if atype not in POPULATION_TYPES:
            raise ValueError(
                f"ParticlePopulation does not support {atype.value}. "
                f"Supported: {sorted(t.value for t in POPULATION_TYPES)}"
            )
        if centers_a.ndim != 2 or centers_a.shape[1] not in (2, 3):
            raise ValueError(f"centers must be (N, 2|3), got {centers_a.shape}")
        if radii_a.ndim != 1:
            raise ValueError(f"radii must be (N,), got {radii_a.shape}")
        if radii_a.shape[0] != centers_a.shape[0]:
            raise ValueError(
                f"centers ({centers_a.shape[0]}) and radii ({radii_a.shape[0]}) disagree"
            )
        if radii_a.size and np.any(radii_a <= 0):
            raise ValueError("all radii must be strictly positive")
        extra = extra_params or {}
        cls._validate_extra(atype, extra)
        return cls(
            population_id=population_id or new_population_id(),
            avatar_type=atype,
            material_name=material_name,
            model_name=model_name,
            color=color,
            origin=origin_e,
            dimension=int(centers_a.shape[1]),
            centers=np.ascontiguousarray(centers_a),
            radii=np.ascontiguousarray(radii_a),
            group_name=group_name,
            extra_params=dict(extra),
        )

    @staticmethod
    def _validate_extra(avatar_type: AvatarType, extra: dict[str, Any]) -> None:
        if avatar_type == AvatarType.RIGID_CLUSTER:
            nb = extra.get("nb_disk", 3)
            if not isinstance(nb, int) or nb < 2:
                raise ValueError("rigidCluster: extra_params['nb_disk'] must be int >= 2")
        elif avatar_type == AvatarType.RIGID_CYLINDER:
            h = extra.get("h")
            if h is None or float(h) <= 0:
                raise ValueError("rigidCylinder: extra_params['h'] required and > 0")
        elif avatar_type in (AvatarType.RIGID_POLYGON, AvatarType.RIGID_POLYHEDRON):
            nb_min = 3 if avatar_type == AvatarType.RIGID_POLYGON else 4
            nb = extra.get("nb_vertices")
            if not isinstance(nb, int) or nb < nb_min:
                raise ValueError(
                    f"{avatar_type.value}: extra_params['nb_vertices'] int >= {nb_min}"
                )

    def __len__(self) -> int:
        return int(self.centers.shape[0])

    def particle_avatar_id(self, i: int) -> str:
        if not (0 <= i < len(self)):
            raise IndexError(i)
        return particle_id(self.population_id, i)

    def as_avatar_view(self, i: int) -> Avatar:
        kwargs: dict[str, Any] = dict(
            avatar_id=self.particle_avatar_id(i),
            avatar_type=self.avatar_type,
            center=self.centers[i].tolist(),
            radius=float(self.radii[i]),
            material_name=self.material_name,
            model_name=self.model_name,
            color=self.color,
            origin=self.origin,
        )
        if self.avatar_type == AvatarType.RIGID_CLUSTER:
            kwargs["nb_vertices"] = self.extra_params.get("nb_disk", 3)
        elif self.avatar_type == AvatarType.RIGID_CYLINDER:
            kwargs["wall_params"] = {"h": self.extra_params.get("h", 1.0)}
        elif self.avatar_type in (AvatarType.RIGID_POLYGON, AvatarType.RIGID_POLYHEDRON):
            kwargs["generation_type"] = "regular"
            kwargs["nb_vertices"] = self.extra_params.get("nb_vertices", 6)
        return Avatar(**kwargs)

    def bounds(self) -> tuple[np.ndarray, np.ndarray]:
        if len(self) == 0:
            z = np.zeros(self.dimension)
            return z, z
        return self.centers.min(axis=0), self.centers.max(axis=0)

    def radius_stats(self) -> dict[str, float]:
        if len(self) == 0:
            return {"min": 0.0, "max": 0.0, "mean": 0.0}
        return {
            "min": float(self.radii.min()),
            "max": float(self.radii.max()),
            "mean": float(self.radii.mean()),
        }

    def to_meta_dict(self) -> dict:
        return {
            "population_id": self.population_id,
            "avatar_type": self.avatar_type.value,
            "material_name": self.material_name,
            "model_name": self.model_name,
            "color": self.color,
            "origin": self.origin.value,
            "dimension": self.dimension,
            "group_name": self.group_name,
            "n_particles": len(self),
            "extra_params": dict(self.extra_params),
        }

    def to_dict(self) -> dict:
        d = self.to_meta_dict()
        d["centers"] = self.centers.tolist()
        d["radii"] = self.radii.tolist()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> ParticlePopulation:
        centers = np.array(data["centers"], dtype=np.float64)
        radii = np.array(data["radii"], dtype=np.float64)
        if centers.size == 0:
            centers = centers.reshape(0, int(data.get("dimension", 2)))
        return cls._from_meta(data, centers, radii)

    @classmethod
    def from_meta_and_arrays(
        cls, meta: dict, centers: np.ndarray, radii: np.ndarray
    ) -> ParticlePopulation:
        return cls._from_meta(meta, centers, radii)

    @classmethod
    def _from_meta(cls, meta: dict, centers: np.ndarray, radii: np.ndarray) -> ParticlePopulation:
        return cls(
            population_id=meta["population_id"],
            avatar_type=AvatarType(meta["avatar_type"]),
            material_name=meta["material_name"],
            model_name=meta["model_name"],
            color=meta["color"],
            origin=AvatarOrigin(meta["origin"]),
            dimension=int(meta["dimension"]),
            centers=np.asarray(centers, dtype=np.float64),
            radii=np.asarray(radii, dtype=np.float64),
            group_name=meta.get("group_name"),
            extra_params=dict(meta.get("extra_params") or {}),
        )

    def __repr__(self) -> str:
        return (
            f"ParticlePopulation(id={self.population_id!r}, n={len(self)}, "
            f"type={self.avatar_type.value}, dim={self.dimension})"
        )
