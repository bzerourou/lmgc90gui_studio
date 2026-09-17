"""Serializable domain entities. No controller, no pylmgc object, no Qt."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Optional

from .ids import new_avatar_id
from .types import AvatarOrigin, AvatarType, ContactLawType, MaterialType


def jsonable(obj: Any) -> Any:
    import numpy as np

    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(x) for x in obj]
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    return obj


@dataclass
class Material:
    name: str
    material_type: MaterialType
    density: float
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.material_type.value,
            "density": self.density,
            "props": jsonable(self.properties),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Material:
        return cls(
            name=data["name"],
            material_type=MaterialType(data["type"]),
            density=float(data["density"]),
            properties=dict(data.get("props") or {}),
        )


@dataclass
class Model:
    name: str
    physics: str
    element: str
    dimension: int
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "physics": self.physics,
            "element": self.element,
            "dimension": self.dimension,
        }
        d.update(self.options)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Model:
        base = {"name", "physics", "element", "dimension"}
        options = {k: v for k, v in data.items() if k not in base}
        return cls(
            name=data["name"],
            physics=data["physics"],
            element=data["element"],
            dimension=int(data["dimension"]),
            options=options,
        )


@dataclass
class Avatar:
    """Fine-grained body (AoS). Identity is `avatar_id`, never the list index."""

    avatar_type: AvatarType
    center: list[float]
    material_name: str
    model_name: str
    color: str = "BLUEx"
    origin: AvatarOrigin = AvatarOrigin.MANUAL
    avatar_id: str = field(default_factory=new_avatar_id)
    radius: Optional[float] = None
    axis: Optional[dict[str, float]] = None
    vertices: Optional[list[list[float]]] = None
    nb_vertices: Optional[int] = None
    generation_type: Optional[str] = None
    is_hollow: bool = False
    wall_params: Optional[dict[str, Any]] = None
    contactors: list[dict[str, Any]] = field(default_factory=list)
    mesh_params: Optional[dict[str, Any]] = None

    def copy(self) -> Avatar:
        return replace(
            self,
            center=list(self.center),
            axis=dict(self.axis) if self.axis else None,
            vertices=[list(v) for v in self.vertices] if self.vertices else None,
            wall_params=dict(self.wall_params) if self.wall_params else None,
            contactors=[dict(c) for c in self.contactors],
            mesh_params=dict(self.mesh_params) if self.mesh_params else None,
        )

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "type": self.avatar_type.value,
            "avatar_id": self.avatar_id,
            "center": jsonable(self.center),
            "material": self.material_name,
            "model": self.model_name,
            "color": self.color,
            "__origin": self.origin.value,
        }
        if self.radius is not None:
            key = "radius" if self.avatar_type in (
                AvatarType.RIGID_POLYGON, AvatarType.RIGID_POLYHEDRON,
            ) else "r"
            data[key] = self.radius
        if self.axis:
            data.update(self.axis)
        if self.vertices:
            data["vertices"] = jsonable(self.vertices)
        if self.nb_vertices is not None:
            data["nb_vertices"] = self.nb_vertices
        if self.generation_type:
            data["gen_type"] = self.generation_type
        if self.is_hollow:
            data["is_Hollow"] = True
        if self.wall_params:
            data.update(jsonable(self.wall_params))
        if self.contactors:
            data["contactors"] = jsonable(self.contactors)
        if self.mesh_params is not None:
            data["mesh_params"] = jsonable(self.mesh_params)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Avatar:
        axis = None
        if "axe1" in data and "axe2" in data:
            axis = {"axe1": data["axe1"], "axe2": data["axe2"]}
            if "axe3" in data:
                axis["axe3"] = data["axe3"]
        center = list(data.get("center") or [])
        wall_keys = (
            "l", "h", "r", "rmin", "rmax", "nb_vertex", "nb_polyg",
            "lx", "ly", "lz", "ra", "rb", "faces", "brick_name",
        )
        wall = {k: data[k] for k in wall_keys if k in data}
        return cls(
            avatar_type=AvatarType(data["type"]),
            center=center,
            material_name=data["material"],
            model_name=data["model"],
            color=data.get("color", "BLUEx"),
            origin=AvatarOrigin(data.get("__origin", "manual")),
            avatar_id=data.get("avatar_id") or new_avatar_id(),
            radius=data.get("r") if data.get("r") is not None else data.get("radius"),
            axis=axis,
            vertices=data.get("vertices"),
            nb_vertices=data.get("nb_vertices"),
            generation_type=data.get("gen_type"),
            is_hollow=bool(data.get("is_Hollow", False)),
            wall_params=wall or None,
            contactors=list(data.get("contactors") or []),
            mesh_params=data.get("mesh_params"),
        )


@dataclass
class ContactLaw:
    name: str
    law_type: ContactLawType
    friction: Optional[float] = None
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        data: dict[str, Any] = {"name": self.name, "law": self.law_type.value}
        if self.friction is not None:
            data["fric"] = self.friction
        data.update(self.properties)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> ContactLaw:
        skip = {"name", "law", "fric"}
        return cls(
            name=data["name"],
            law_type=ContactLawType(data["law"]),
            friction=data.get("fric"),
            properties={k: v for k, v in data.items() if k not in skip},
        )


@dataclass
class VisibilityRule:
    candidate_body: str
    candidate_contactor: str
    candidate_color: str
    antagonist_body: str
    antagonist_contactor: str
    antagonist_color: str
    behavior_name: str
    alert: float = 0.1

    def to_dict(self) -> dict:
        return {
            "CorpsCandidat": self.candidate_body,
            "candidat": self.candidate_contactor,
            "colorCandidat": self.candidate_color,
            "CorpsAntagoniste": self.antagonist_body,
            "antagoniste": self.antagonist_contactor,
            "colorAntagoniste": self.antagonist_color,
            "behav": self.behavior_name,
            "alert": self.alert,
        }

    @classmethod
    def from_dict(cls, data: dict) -> VisibilityRule:
        return cls(
            candidate_body=data["CorpsCandidat"],
            candidate_contactor=data["candidat"],
            candidate_color=data["colorCandidat"],
            antagonist_body=data["CorpsAntagoniste"],
            antagonist_contactor=data["antagoniste"],
            antagonist_color=data["colorAntagoniste"],
            behavior_name=data["behav"],
            alert=float(data.get("alert", 0.1)),
        )


@dataclass
class DOFOperation:
    operation_type: str
    target_type: str
    target_value: Any
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.operation_type,
            "target": self.target_type,
            "target_value": self.target_value,
            "params": jsonable(self.parameters),
        }

    @classmethod
    def from_dict(cls, data: dict) -> DOFOperation:
        if "body_index" in data:
            return cls(data["type"], "avatar", data["body_index"], data.get("params") or {})
        if "group_name" in data:
            return cls(data["type"], "group", data["group_name"], data.get("params") or {})
        return cls(
            data["type"],
            data.get("target", "avatar"),
            data.get("target_value", 0),
            data.get("params") or {},
        )


@dataclass
class PostProCommand:
    name: str
    step: int = 1
    target_type: str = "global"
    target_value: Any = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "step": self.step,
            "target_type": self.target_type,
            "target_value": self.target_value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PostProCommand:
        target = data.get("target_info") or {}
        return cls(
            name=data.get("name") or data.get("command") or "SOLVER INFORMATIONS",
            step=int(data.get("step", 1)),
            target_type=data.get("target_type") or target.get("type") or "global",
            target_value=data.get("target_value", target.get("value")),
        )


@dataclass
class Loop:
    loop_type: str
    model_avatar_id: str
    count: int
    radius: float = 0.0
    step: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    offset_z: float = 0.0
    spiral_factor: float = 0.0
    invert_axis: bool = False
    group_name: Optional[str] = None
    generated_ids: list[str] = field(default_factory=list)
    loop_id: str = field(default_factory=new_avatar_id)

    def to_dict(self) -> dict:
        return {
            "type": self.loop_type,
            "model_avatar_id": self.model_avatar_id,
            "count": self.count,
            "radius": self.radius,
            "step": self.step,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "offset_z": self.offset_z,
            "spiral_factor": self.spiral_factor,
            "invert_axis": self.invert_axis,
            "group_name": self.group_name,
            "generated_ids": list(self.generated_ids),
            "loop_id": self.loop_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Loop:
        return cls(
            loop_type=data.get("type") or data.get("loop_type", "circle"),
            model_avatar_id=data.get("model_avatar_id") or "",
            count=int(data.get("count", 0)),
            radius=float(data.get("radius", 0.0)),
            step=float(data.get("step", 0.0)),
            offset_x=float(data.get("offset_x", 0.0)),
            offset_y=float(data.get("offset_y", 0.0)),
            offset_z=float(data.get("offset_z", 0.0)),
            spiral_factor=float(data.get("spiral_factor", 0.0)),
            invert_axis=bool(data.get("invert_axis", False)),
            group_name=data.get("group_name"),
            generated_ids=list(data.get("generated_ids") or []),
            loop_id=data.get("loop_id") or new_avatar_id(),
        )


@dataclass
class ForLoop:
    """Generic parametric loop — expressions evaluated with a safe arithmetic AST.

    Variable ``var_name`` takes values from ``start`` to ``stop`` (exclusive) with
    ``step``. Expressions for centre / radius may reference the variable, e.g.
    ``\"0.1 * i\"``, ``\"cos(i * pi / 8)\"``.
    """

    var_name: str = "i"
    start: float = 0.0
    stop: float = 10.0
    step: float = 1.0
    model_avatar_id: str = ""
    expr_x: str = "i * 0.1"
    expr_y: str = "0.0"
    expr_z: str = "0.0"
    expr_radius: Optional[str] = None  # None → keep template radius
    group_name: Optional[str] = None
    generated_ids: list[str] = field(default_factory=list)
    loop_id: str = field(default_factory=new_avatar_id)
    use_soa: bool = False

    def to_dict(self) -> dict:
        return {
            "var_name": self.var_name,
            "start": self.start,
            "stop": self.stop,
            "step": self.step,
            "model_avatar_id": self.model_avatar_id,
            "expr_x": self.expr_x,
            "expr_y": self.expr_y,
            "expr_z": self.expr_z,
            "expr_radius": self.expr_radius,
            "group_name": self.group_name,
            "generated_ids": list(self.generated_ids),
            "loop_id": self.loop_id,
            "use_soa": self.use_soa,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ForLoop:
        return cls(
            var_name=data.get("var_name", "i"),
            start=float(data.get("start", 0)),
            stop=float(data.get("stop", 10)),
            step=float(data.get("step", 1)),
            model_avatar_id=data.get("model_avatar_id") or "",
            expr_x=data.get("expr_x", "i * 0.1"),
            expr_y=data.get("expr_y", "0.0"),
            expr_z=data.get("expr_z", "0.0"),
            expr_radius=data.get("expr_radius"),
            group_name=data.get("group_name"),
            generated_ids=list(data.get("generated_ids") or []),
            loop_id=data.get("loop_id") or new_avatar_id(),
            use_soa=bool(data.get("use_soa", False)),
        )


@dataclass
class GranuloConfig:
    """Intent of a deposit. Arrays live on ParticlePopulation, not here."""

    nb_particles: int
    radius_min: float
    radius_max: float
    container_type: str
    container_params: dict[str, float]
    material_name: str
    model_name: str
    avatar_type: str = "rigidDisk"
    color: str = "BLUEx"
    group_name: Optional[str] = None
    seed: Optional[int] = None
    population_id: Optional[str] = None
    dimension: int = 2

    def to_dict(self) -> dict:
        return {
            "nb_particles": self.nb_particles,
            "radius_min": self.radius_min,
            "radius_max": self.radius_max,
            "container_type": self.container_type,
            "container_params": dict(self.container_params),
            "material_name": self.material_name,
            "model_name": self.model_name,
            "avatar_type": self.avatar_type,
            "color": self.color,
            "group_name": self.group_name,
            "seed": self.seed,
            "population_id": self.population_id,
            "dimension": self.dimension,
            "use_particle_population": True,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GranuloConfig:
        params = dict(data.get("container_params") or {})
        for key in ("lx", "ly", "lz", "r", "rint", "rext"):
            if key in data and key not in params:
                params[key] = data[key]
        return cls(
            nb_particles=int(data.get("nb_particles", 0)),
            radius_min=float(data.get("radius_min", 0.0)),
            radius_max=float(data.get("radius_max", 0.0)),
            container_type=data.get("container_type") or data.get("deposit", "Box2D"),
            container_params=params,
            material_name=data.get("material_name") or data.get("material") or "",
            model_name=data.get("model_name") or data.get("model") or "",
            avatar_type=data.get("avatar_type", "rigidDisk"),
            color=data.get("color", "BLUEx"),
            group_name=data.get("group_name"),
            seed=data.get("seed"),
            population_id=data.get("population_id"),
            dimension=int(data.get("dimension", 2)),
        )
