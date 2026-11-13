"""Runtime-backed material fields with the core schema as fallback."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .introspection import compatibility_catalog_source, load_compatibility_catalogs


_MATERIAL_CATALOG_NAMES = (
    "materialTypeOptions",
    "materialOptions",
    "bulkBehavOptions",
    "bulk_behav_options",
    "material_type_options",
)

_MATERIAL_PROPERTY_LABELS = {
    "elas": "elas (loi)",
    "anisotropy": "anisotropy",
    "young": "E — Young (Pa)",
    "nu": "ν — Poisson",
    "young1": "E1 — Young dir. 1 (Pa)",
    "young2": "E2 — Young dir. 2 (Pa)",
    "young3": "E3 — Young dir. 3 (Pa)",
    "nu12": "ν12 — Poisson",
    "nu13": "ν13 — Poisson",
    "nu23": "ν23 — Poisson",
    "G": "G — cisaillement (Pa)",
    "G12": "G12 — cisaillement (Pa)",
    "G13": "G13 — cisaillement (Pa)",
    "G23": "G23 — cisaillement (Pa)",
    "dilatation": "dilatation (α thermal / dilatation)",
    "T_ref_meca": "température mécanique de référence",
    "viscous_model": "modèle visqueux",
    "viscous_young": "Young visqueux (Pa)",
    "viscous_nu": "Poisson visqueux",
    "critere": "critère plastique",
    "isoh": "écrouissage isotrope",
    "iso_hard": "limite élastique initiale (Pa)",
    "isoh_coeff": "module d’écrouissage isotrope (Pa)",
    "cinh": "écrouissage cinématique",
    "visc": "viscoplasticité",
    "conductivity": "conductivité",
    "specific_capacity": "capacité spécifique / stockage",
    "hydro_cpl": "couplage hydraulique (Biot)",
    "masses": "masses (vecteur 2D/3D)",
    "stiffnesses": "raideurs (vecteur 2D/3D)",
    "viscosities": "viscosités (vecteur 2D/3D)",
    "file_mat": "fichier de loi matériau",
}

_ORTHOTROPIC_FIELDS = frozenset({
    "young1", "young2", "young3", "nu12", "nu13", "nu23",
    "G12", "G13", "G23",
})
_ELASTIC_TYPES = frozenset({
    "ELAS", "ELAS_DILA", "VISCO_ELAS", "ELAS_PLAS",
    "THERMO_ELAS", "PORO_ELAS",
})


def _runtime_material_options() -> dict[str, tuple[str, ...]]:
    catalogs = load_compatibility_catalogs()
    raw = next((
        catalogs[name] for name in _MATERIAL_CATALOG_NAMES
        if isinstance(catalogs.get(name), Mapping)
    ), {})
    options: dict[str, tuple[str, ...]] = {}
    for material_type, values in raw.items():
        if isinstance(values, Mapping):
            names = values.keys()
        elif isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
            names = values
        else:
            continue
        options[str(material_type)] = tuple(dict.fromkeys(
            str(name) for name in names
        ))
    return options


def _runtime_material_choices(
    catalogs: Mapping[str, Any],
    options: Mapping[str, Sequence[str]],
) -> dict[str, dict[str, tuple[str, ...]]]:
    rules = catalogs.get("checkBulkBehavOptions", {})
    if not isinstance(rules, Mapping):
        return {}

    choices_by_type: dict[str, dict[str, tuple[str, ...]]] = {}
    for material_type, tree in rules.items():
        fields = set(options.get(str(material_type), ()))
        choices: dict[str, tuple[str, ...]] = {}

        def visit(node: Any) -> None:
            if not isinstance(node, Mapping):
                return
            name = node.get("root")
            children = node.get("children", ())
            if name in fields and isinstance(children, Sequence):
                values = tuple(
                    str(child["root"])
                    for child in children
                    if isinstance(child, Mapping) and child.get("root") is not None
                )
                if values:
                    choices[str(name)] = values
            if isinstance(children, Sequence):
                for child in children:
                    visit(child)

        visit(tree)
        if choices:
            choices_by_type[str(material_type)] = choices
    return choices_by_type


def material_option_catalog(
    fallback: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Return accepted material options, preferring installed runtime values."""
    catalog = {
        str(material_type): tuple(dict.fromkeys(str(name) for name in names))
        for material_type, names in (fallback or {}).items()
    }
    catalog.update(_runtime_material_options())
    return catalog


def material_schema_catalog(
    fallback_schema: Mapping[str, Sequence[tuple[str, Any, str]]] | None = None,
    fallback_choices: Mapping[str, Sequence[str]] | None = None,
    fallback_options: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, Any]:
    """Return type, property, choice, and label data for the material form."""
    from lmgc90_core.types import (
        ISOTROPIC_FIELDS,
        MATERIAL_OPTIONS,
        MATERIAL_PROPERTY_CHOICES,
        MATERIAL_PROPERTY_SCHEMA,
        ORTHOTROPIC_FIELDS_2D,
        ORTHOTROPIC_FIELDS_3D,
    )

    if fallback_schema is None:
        fallback_schema = MATERIAL_PROPERTY_SCHEMA
    if fallback_choices is None:
        fallback_choices = MATERIAL_PROPERTY_CHOICES
    if fallback_options is None:
        fallback_options = MATERIAL_OPTIONS
    catalogs = load_compatibility_catalogs()
    runtime_options = _runtime_material_options()
    runtime_choices = _runtime_material_choices(catalogs, runtime_options)
    options = material_option_catalog(fallback_options)
    schema_by_type: dict[str, tuple[tuple[str, Any, str], ...]] = {}
    known_types = tuple(dict.fromkeys((
        *(str(name) for name in fallback_schema),
        *runtime_options,
    )))

    for material_type in known_types:
        fallback_fields = tuple(fallback_schema.get(material_type, ()))
        defaults = {
            name: (default, kind)
            for name, default, kind in fallback_fields
        }
        runtime_fields = runtime_options.get(material_type)
        if runtime_fields is None:
            schema_by_type[material_type] = fallback_fields
            continue

        field_names = list(name for name in runtime_fields if name != "density")
        if material_type in _ELASTIC_TYPES:
            field_names.extend(
                name for name, _, _ in fallback_fields
                if name in _ORTHOTROPIC_FIELDS and name not in field_names
            )
        schema_by_type[material_type] = tuple(
            (name, *defaults[name]) if name in defaults
            else (name, None, "auto")
            for name in field_names
        )

    runtime_types = tuple(name for name in known_types if name in runtime_options)
    available_types = runtime_types or known_types
    return {
        "source": (
            compatibility_catalog_source()
            if runtime_options else "FALLBACK"
        ),
        "types": available_types,
        "options": options,
        "properties": schema_by_type,
        "choices_by_type": runtime_choices,
        "choices": {
            str(name): tuple(str(choice) for choice in choices)
            for name, choices in fallback_choices.items()
        },
        "labels": _MATERIAL_PROPERTY_LABELS,
        "isotropic_fields": tuple(ISOTROPIC_FIELDS),
        "orthotropic_fields": {
            2: tuple(ORTHOTROPIC_FIELDS_2D),
            3: tuple(ORTHOTROPIC_FIELDS_3D),
        },
    }
