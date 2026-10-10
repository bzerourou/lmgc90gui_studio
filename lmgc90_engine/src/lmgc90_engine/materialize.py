"""Turn a pure Project into live pylmgc90.pre containers.

Returns a MaterializedScene holding the containers and id maps.
Does not write DATBOX (see datbox.py / EngineSession.write_datbox).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from lmgc90_core.entities import Avatar, ContactLaw, Material, Model, VisibilityRule
from lmgc90_core.population import ParticlePopulation
from lmgc90_core.project import Project

from .avatar_factory import build_avatar, build_population_bodies
from .errors import MaterializationError, PylmgcNotAvailable


def _pre():
    try:
        from lmgc90_core.numpy_compat import patch_numpy_cross
        patch_numpy_cross()
        from pylmgc90 import pre
        return pre
    except ImportError as exc:
        raise PylmgcNotAvailable(
            "pylmgc90 is required for materialization."
        ) from exc


@dataclass
class MaterializedScene:
    """Live pylmgc containers + identity maps."""

    materials_container: Any
    models_container: Any
    bodies_container: Any
    tacts_container: Any
    sees_container: Any
    posts_container: Any

    material_by_name: dict[str, Any] = field(default_factory=dict)
    model_by_name: dict[str, Any] = field(default_factory=dict)
    body_by_avatar_id: dict[str, Any] = field(default_factory=dict)
    bodies_by_population_id: dict[str, list[Any]] = field(default_factory=dict)
    law_by_name: dict[str, Any] = field(default_factory=dict)

    dimension: int = 2
    project_name: str = "untitled"


def materialize_project(project: Project) -> MaterializedScene:
    """Full materialization of a Project. Raises if pylmgc90 is missing."""
    pre = _pre()

    mats = pre.materials()
    mods = pre.models()
    bodies = pre.avatars()
    tacts = pre.tact_behavs()
    sees = pre.see_tables()
    posts = pre.postpro_commands()

    scene = MaterializedScene(
        materials_container=mats,
        models_container=mods,
        bodies_container=bodies,
        tacts_container=tacts,
        sees_container=sees,
        posts_container=posts,
        dimension=project.dimension,
        project_name=project.name,
    )

    # --- materials ---
    for m in project.materials:
        obj = _make_material(pre, m)
        mats.addMaterial(obj)
        scene.material_by_name[m.name] = obj

    # --- models ---
    for m in project.models:
        obj = _make_model(pre, m)
        mods.addModel(obj)
        scene.model_by_name[m.name] = obj

    # --- avatars (AoS) ---
    from .avatar_factory import expand_rigids_from_mesh2d

    for av in project.avatars:
        mp = getattr(av, "mesh_params", None) or {}
        geom = str(mp.get("geom", "") or "")
        if geom.lower() in ("rigidsfrommesh2d", "rigids_from_mesh2d") or mp.get(
            "source"
        ) == "rigidsFromMesh2D":
            many = expand_rigids_from_mesh2d(
                av,
                materials=scene.material_by_name,
                models=scene.model_by_name,
            )
            for i, body in enumerate(many):
                bodies.addAvatar(body)
                scene.body_by_avatar_id[f"{av.avatar_id}_{i}"] = body
            # keep primary id → first body for DOF targeting if needed
            if many:
                scene.body_by_avatar_id[av.avatar_id] = many[0]
            continue
        body = build_avatar(
            av,
            materials=scene.material_by_name,
            models=scene.model_by_name,
        )
        bodies.addAvatar(body)
        scene.body_by_avatar_id[av.avatar_id] = body

    # --- populations (SoA → many bodies) ---
    for pop in project.populations:
        pop_bodies = build_population_bodies(
            pop,
            materials=scene.material_by_name,
            models=scene.model_by_name,
        )
        for b in pop_bodies:
            bodies.addAvatar(b)
        scene.bodies_by_population_id[pop.population_id] = pop_bodies

    # --- contact laws ---
    for law in project.laws:
        obj = _make_law(pre, law)
        tacts.addBehav(obj)
        # index under both original and 5-char LMGC name
        scene.law_by_name[law.name] = obj
        scene.law_by_name[_lmgc5(law.name)] = obj

    # --- see tables ---
    for rule in project.visibility:
        obj = _make_see(pre, rule)
        sees.addSeeTable(obj)

    # --- DOF / operations (applied on bodies) ---
    for op in project.operations:
        _apply_dof(project, scene, op)

    # --- postpro ---
    for cmd in project.postpro:
        kwargs: dict[str, Any] = {"name": cmd.name, "step": cmd.step}
        if cmd.target_type != "global" and cmd.target_value is not None:
            kwargs[cmd.target_type] = cmd.target_value
        posts.addCommand(pre.postpro_command(**kwargs))

    return scene


def _lmgc5(name: str, default: str = "XXXXX") -> str:
    """LMGC90 Fortran identifiers are fixed-width 5 characters."""
    s = (name or default).strip()
    if len(s) > 5:
        s = s[:5]
    if len(s) < 5:
        s = s + ("x" * (5 - len(s)))
    return s


# pylmgc90.pre.material option aliases (GUI / schema → Fortran name)
_MATERIAL_PROP_ALIASES: dict[str, dict[str, str]] = {
    "ELAS_DILA": {"alpha": "dilatation"},
    "ELAS_PLAS": {"sigc": "iso_hard", "hard": "isoh_coeff"},
    "THERMO_ELAS": {"alpha": "dilatation", "capacity": "specific_capacity"},
    "PORO_ELAS": {
        "biot": "hydro_cpl",
        "permeability": "conductivity",
        "capacity": "specific_capacity",
    },
}

_ORTHOTROPIC_FIELDS = (
    "young1", "young2", "young3",
    "nu12", "nu13", "nu23",
    "G12", "G13", "G23",
)

_MATERIAL_OPTIONS = {
    "RIGID": {"density"},
    "ELAS": {"density", "elas", "anisotropy", "young", "nu", "G"},
    "ELAS_DILA": {
        "density", "elas", "anisotropy", "young", "nu", "dilatation", "T_ref_meca",
    },
    "VISCO_ELAS": {
        "density", "elas", "anisotropy", "young", "nu", "viscous_model",
        "viscous_young", "viscous_nu",
    },
    "ELAS_PLAS": {
        "density", "elas", "anisotropy", "young", "nu", "critere", "isoh",
        "iso_hard", "isoh_coeff", "cinh", "visc",
    },
    "THERMO_ELAS": {
        "density", "elas", "anisotropy", "young", "nu", "dilatation", "T_ref_meca",
        "conductivity", "specific_capacity", "therm_cpl",
    },
    "PORO_ELAS": {
        "density", "elas", "anisotropy", "young", "nu", "hydro_cpl", "conductivity",
        "specific_capacity",
    },
    "DISCRETE": {"masses", "stiffnesses", "viscosities"},
    "USER_MAT": {"density", "file_mat"},
    "EXTERNAL": set(),
}

_STALE_VISCOUS_OPTIONS = (
    "eta", "viscosity",
)


def _make_material(pre, m: Material) -> Any:
    mtype = m.material_type.value
    allowed = _MATERIAL_OPTIONS.get(mtype, set())
    kwargs: dict[str, Any] = dict(
        name=_lmgc5(m.name),
        materialType=mtype,
    )
    if "density" in allowed:
        kwargs["density"] = float(m.density)
    props = dict(m.properties or {})
    aliases = _MATERIAL_PROP_ALIASES.get(mtype, {})

    def _rename(src: dict) -> dict:
        out = {}
        for k, v in src.items():
            key = aliases.get(k, k)
            if k in aliases and key in src:
                continue
            if key in allowed:
                out[key] = v
        return out

    aniso = str(props.get("anisotropy", "isotropic")).lower()
    if mtype == "ELAS" and aniso in ("orthotropic", "ortho", "orthotrop"):
        y1 = props.pop("young1", props.get("young", 2.1e11))
        y2 = props.pop("young2", y1)
        y3 = props.pop("young3", None)
        n12 = props.pop("nu12", props.get("nu", 0.3))
        n13 = props.pop("nu13", n12)
        n23 = props.pop("nu23", n12)
        g12 = props.pop("G12", props.pop("G", None))
        g13 = props.pop("G13", g12)
        g23 = props.pop("G23", g12)
        props.pop("young", None)
        props.pop("nu", None)
        props.pop("G", None)
        if y3 is not None:
            kwargs["young"] = [float(y1), float(y2), float(y3)]
            kwargs["nu"] = [float(n12), float(n13), float(n23)]
            if g12 is not None:
                kwargs["G"] = [float(g12), float(g13), float(g23)]
        else:
            kwargs["young"] = [float(y1), float(y2)]
            kwargs["nu"] = [float(n12)]
            if g12 is not None:
                kwargs["G"] = [float(g12)]
        kwargs["anisotropy"] = "orthotropic"
        rest = {k: v for k, v in props.items() if k not in _ORTHOTROPIC_FIELDS and k != "anisotropy"}
        kwargs.update(_rename(rest))
    else:
        for k in _ORTHOTROPIC_FIELDS:
            props.pop(k, None)
        if mtype != "ELAS":
            for k in _STALE_VISCOUS_OPTIONS:
                props.pop(k, None)
            if "anisotropy" in allowed:
                props["anisotropy"] = "isotropic"
        elif "anisotropy" in props:
            value = str(props["anisotropy"]).lower()
            props["anisotropy"] = value if value in ("isotropic", "orthotropic") else "isotropic"
        if props.get("elas") not in (None, "", "standard"):
            if props.get("elas") not in ("Hookean", "HartSmith"):
                props["elas"] = "standard"
        kwargs.update(_rename(props))

    if mtype == "DISCRETE":
        for key in ("masses", "stiffnesses", "viscosities"):
            value = kwargs.get(key)
            if isinstance(value, str):
                kwargs[key] = [float(part.strip()) for part in value.replace(";", ",").split(",") if part.strip()]

    if mtype == "ELAS_DILA" and "dilatation" not in kwargs:
        kwargs["dilatation"] = 1e-5

    return pre.material(**kwargs)


def _make_model(pre, m: Model) -> Any:
    dim = int(m.dimension)
    if dim not in (2, 3):
        raise MaterializationError(
            f"model {m.name!r}: spatial dimension must be 2 or 3, got {dim!r}"
        )
    kwargs: dict[str, Any] = dict(
        name=_lmgc5(m.name),
        physics=m.physics,
        element=m.element,
        dimension=dim,
    )
    opts = dict(m.options or {})
    # never let options overwrite dimension with a bad value
    opts.pop("dimension", None)
    kwargs.update(opts)
    kwargs["dimension"] = dim
    return pre.model(**kwargs)


def _make_law(pre, law: ContactLaw) -> Any:
    # pylmgc90.pre.tact_behav requires name to be exactly 5 characters
    kwargs: dict[str, Any] = dict(name=_lmgc5(law.name), law=law.law_type.value)
    if law.friction is not None:
        kwargs["fric"] = float(law.friction)
    kwargs.update(law.properties or {})
    return pre.tact_behav(**kwargs)


def _make_see(pre, rule: VisibilityRule) -> Any:
    return pre.see_table(
        CorpsCandidat=rule.candidate_body,
        candidat=rule.candidate_contactor,
        colorCandidat=rule.candidate_color,
        CorpsAntagoniste=rule.antagonist_body,
        antagoniste=rule.antagonist_contactor,
        colorAntagoniste=rule.antagonist_color,
        behav=_lmgc5(rule.behavior_name),
        alert=float(rule.alert),
    )


def _apply_dof(project: Project, scene: MaterializedScene, op) -> None:
    """Apply one DOFOperation onto the corresponding live body(ies).

    Supports ``imposeDrivenDof`` with ``description='predefined'`` (cell spreading).
    Studio-only keys (``phase``, …) are stripped before calling pylmgc.
    """
    targets: list[Any] = []
    if op.target_type == "avatar":
        body = scene.body_by_avatar_id.get(str(op.target_value))
        if body is None:
            raise MaterializationError(
                f"DOF target avatar_id={op.target_value!r} not in scene"
            )
        targets = [body]
    elif op.target_type == "group":
        ids = project.avatar_groups.get(str(op.target_value), [])
        for aid in ids:
            body = scene.body_by_avatar_id.get(aid)
            if body is not None:
                targets.append(body)
    else:
        return

    method = op.operation_type
    raw = dict(op.parameters or {})
    # drop studio metadata
    raw.pop("phase", None)
    raw.pop("protein_target", None)

    # allowed kwargs for common body methods
    allowed = {
        "component", "dofty", "ct", "description", "amp", "omega", "phi",
        "rampi", "ramp", "dx", "dy", "dz", "axis", "alpha", "center",
        "evolutionFile", "evolution_file",
    }
    params = {k: v for k, v in raw.items() if k in allowed}
    # normalize evolution_file → evolutionFile (pylmgc spelling)
    if "evolution_file" in params and "evolutionFile" not in params:
        params["evolutionFile"] = params.pop("evolution_file")
    # evolution BC requires a non-empty filename
    if str(params.get("description", "")).lower() == "evolution":
        evo = params.get("evolutionFile")
        if not evo or not str(evo).strip():
            params["evolutionFile"] = "vx.dat"
        else:
            params["evolutionFile"] = str(evo).strip()

    for body in targets:
        fn = getattr(body, method, None)
        if fn is None:
            raise MaterializationError(
                f"body has no method {method!r} for DOF on {op.target_value!r}"
            )
        try:
            fn(**params)
        except TypeError:
            # older API: component as list, or fewer kwargs
            p2 = dict(params)
            if "component" in p2 and not isinstance(p2["component"], (list, tuple)):
                p2["component"] = [p2["component"]]
            try:
                fn(**p2)
            except TypeError as exc:
                # last resort: only component + dofty + ct
                minimal = {
                    k: p2[k] for k in ("component", "dofty", "ct") if k in p2
                }
                try:
                    fn(**minimal)
                except Exception as exc2:
                    raise MaterializationError(
                        f"DOF {method} failed on {op.target_value!r}: {exc2}"
                    ) from exc2
