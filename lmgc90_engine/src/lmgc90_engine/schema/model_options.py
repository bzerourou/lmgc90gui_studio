"""Runtime model-option choices with the core vocabulary as fallback."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import lru_cache
from typing import Any

from .introspection import load_compatibility_catalogs


@lru_cache(maxsize=1)
def _runtime_model_options() -> dict[str, dict[str, tuple[str, ...]]]:
    raw = load_compatibility_catalogs().get("modelOptions", {})
    return {
        str(physics): {
            str(option): tuple(str(choice) for choice in choices)
            for option, choices in options.items()
            if isinstance(choices, Sequence) and not isinstance(choices, str)
        }
        for physics, options in raw.items()
        if isinstance(options, dict)
    }


def model_option_catalog(
    fallback: Mapping[str, Mapping[str, Sequence[str]]] | None = None,
) -> dict[str, dict[str, tuple[str, ...]]]:
    """Return all model-option choices, preferring installed runtime values."""
    catalog = {
        str(physics): {
            str(option): tuple(str(choice) for choice in choices)
            for option, choices in options.items()
        }
        for physics, options in (fallback or {}).items()
    }
    for physics, options in _runtime_model_options().items():
        catalog.setdefault(physics, {}).update(options)
    return catalog


def model_schema_catalog(
    fallback_elements: Mapping[str, Mapping[Any, Sequence[str]]] | None = None,
    fallback_options: Mapping[str, Mapping[str, Sequence[str]]] | None = None,
    *,
    fallback_rigid_elements: Sequence[str] = (),
    fallback_discrete_elements: Sequence[str] = (),
    fallback_joint_elements: Sequence[str] = (),
) -> dict[str, dict[str, Any]]:
    """Return runtime model compatibility, option rules and per-element fields."""
    catalogs = load_compatibility_catalogs()
    options_by_physics = model_option_catalog(fallback_options)

    elements_by_physics: dict[str, dict[str, tuple[str, ...]]] = {
        str(physics): {
            str(dimension): tuple(str(element) for element in elements)
            for dimension, elements in dimensions.items()
        }
        for physics, dimensions in (fallback_elements or {}).items()
    }

    runtime_elements = catalogs.get("element2ddl")
    runtime_dimensions = catalogs.get("dimension2element")
    if isinstance(runtime_elements, Mapping) and isinstance(runtime_dimensions, Mapping):
        dimensions = {
            str(dimension): {str(element) for element in elements}
            for dimension, elements in runtime_dimensions.items()
        }
        derived: dict[str, dict[str, list[str]]] = {}
        for element, compatible_physics in runtime_elements.items():
            if not isinstance(compatible_physics, Mapping):
                continue
            for physics in compatible_physics:
                physics_name = str(physics)
                for dimension, dimension_elements in dimensions.items():
                    if str(element) in dimension_elements:
                        derived.setdefault(physics_name, {}).setdefault(
                            dimension, []
                        ).append(str(element))
        for physics, dimensions_by_physics in derived.items():
            elements_by_physics[physics] = {
                dimension: tuple(dict.fromkeys(elements))
                for dimension, elements in dimensions_by_physics.items()
            }

    rigid_elements = {
        str(element)
        for element in catalogs.get("rigidElements", fallback_rigid_elements)
    }
    discrete_elements = {
        str(element)
        for element in catalogs.get("discreteElements", fallback_discrete_elements)
    }
    joint_elements = {
        str(element)
        for element in catalogs.get("jointElements", fallback_joint_elements)
    }
    runtime_rules = catalogs.get("checkModelOptions", {})

    schema: dict[str, dict[str, Any]] = {}
    physics_names = dict.fromkeys((
        *elements_by_physics,
        *options_by_physics,
        *(str(physics) for physics in runtime_rules),
    ))
    for physics in physics_names:
        physics_options = options_by_physics.get(physics, {})
        rules = runtime_rules.get(physics, {})
        option_rules = (
            rules.get("children", ())
            if isinstance(rules, Mapping) else ()
        )
        element_options: dict[str, tuple[str, ...]] = {}
        element_choices: dict[str, dict[str, tuple[str, ...]]] = {}
        element_required_options: dict[str, tuple[str, ...]] = {}
        element_option_rules: dict[str, tuple[Mapping[str, Any], ...]] = {}
        required_by_rules = tuple(dict.fromkeys(
            str(rule["root"])
            for rule in option_rules
            if isinstance(rule, Mapping) and rule.get("root") is not None
        ))
        for dimension_elements in elements_by_physics.get(physics, {}).values():
            for element in dimension_elements:
                if element in rigid_elements:
                    element_options[element] = ()
                    element_choices[element] = {}
                    element_required_options[element] = ()
                    element_option_rules[element] = ()
                    continue

                choices = dict(physics_options)
                if "discrete" in choices:
                    if element in discrete_elements:
                        choices["discrete"] = ("yes__",)
                    else:
                        choices.pop("discrete")
                elif element in discrete_elements:
                    choices["discrete"] = ("yes__",)
                if element in discrete_elements | joint_elements:
                    if "external_model" in choices:
                        choices["external_model"] = ("no___",)

                element_options[element] = tuple(choices)
                element_choices[element] = choices
                if element in discrete_elements:
                    element_required_options[element] = (
                        "discrete", "external_model",
                    )
                    element_option_rules[element] = ()
                elif element in joint_elements:
                    element_required_options[element] = ("external_model",)
                    element_option_rules[element] = ()
                else:
                    element_required_options[element] = required_by_rules
                    element_option_rules[element] = tuple(option_rules)

        schema[physics] = {
            "elements_by_dimension": elements_by_physics.get(physics, {}),
            "options": physics_options,
            "option_rules": tuple(option_rules),
            "rigid_elements": tuple(sorted(rigid_elements)),
            "discrete_elements": tuple(sorted(discrete_elements)),
            "joint_elements": tuple(sorted(joint_elements)),
            "element_options": element_options,
            "element_choices": element_choices,
            "element_required_options": element_required_options,
            "element_option_rules": element_option_rules,
        }
    return schema


def model_option_choices_for_values(
    physics_schema: Mapping[str, Any],
    element: str,
    option: str,
    values: Mapping[str, str],
) -> tuple[str, ...]:
    """Filter choices using the runtime's conditional model-option rules."""
    base = tuple(
        physics_schema.get("element_choices", {})
        .get(element, {})
        .get(option, ())
    )
    if not base:
        return ()

    conditional: set[str] = set()

    def visit(option_node: Mapping[str, Any], conditions: tuple[tuple[str, str], ...]) -> None:
        name = str(option_node.get("root", ""))
        for value_node in option_node.get("children", ()):
            value = str(value_node.get("root", ""))
            if any(
                selected in values and values[selected] != expected
                for selected, expected in conditions
            ):
                continue
            if name == option:
                conditional.add(value)
            for child in value_node.get("children", ()):
                visit(child, conditions + ((name, value),))

    for rule in physics_schema.get("option_rules", ()):
        if isinstance(rule, Mapping):
            visit(rule, ())
    if not conditional:
        return base
    return tuple(value for value in base if value in conditional)


def model_option_choices(
    physics: str,
    option: str,
    fallback: tuple[str, ...] | list[str] = (),
) -> tuple[str, ...]:
    """Return installed choices for a model option, or the supplied fallback."""
    choices = _runtime_model_options().get(str(physics), {}).get(str(option))
    return tuple(fallback) if choices is None else choices