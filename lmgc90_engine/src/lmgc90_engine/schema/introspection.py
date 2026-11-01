"""Build a serializable capability snapshot from the installed pylmgc90 API."""
from __future__ import annotations

import importlib
import importlib.metadata
import inspect
from collections.abc import Mapping
from enum import Enum
from typing import Any


_CATALOG_NAMES = (
    "bodyType2contactor",
    "contactorPair2TactBehav",
    "contactorOptions",
    "contactorOptionalOptions",
    "dimension2contactor",
    "dimension2element",
    "geo2element",
    "modelOptions",
    "materialOptions",
    "materialTypeOptions",
    "bulkBehavOptions",
    "bulk_behav_options",
    "material_type_options",
    "tactBehavOptions",
    "listeBodyType",
    "listeCandidat",
    "listeAntagoniste",
    "listeContactor",
    "listeTactBehav",
    "rigidContactor",
    "pointContactor",
)


def _safe_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return _safe_value(value.value)
    if isinstance(value, Mapping):
        return {str(key): _safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _describe_callable(name: str, member: Any) -> dict[str, Any]:
    parameters: list[dict[str, Any]] = []
    signature_text = None
    try:
        signature = inspect.signature(member)
    except (TypeError, ValueError):
        signature = None
    if signature is not None:
        signature_text = str(signature)
        for parameter in signature.parameters.values():
            required = parameter.default is inspect.Parameter.empty
            default = None if required else _safe_value(parameter.default)
            parameters.append({
                "name": parameter.name,
                "kind": parameter.kind.name,
                "required": required,
                "default": default,
            })

    return {
        "name": name,
        "signature": signature_text,
        "parameters": parameters,
        "doc": inspect.getdoc(member),
    }


def _public_callables(module: Any) -> dict[str, dict[str, Any]]:
    result = {}
    for name in dir(module):
        if name.startswith("_"):
            continue
        try:
            member = getattr(module, name)
        except Exception:
            continue
        if callable(member):
            result[name] = _describe_callable(name, member)
    return result


def _load_compatibility_catalogs() -> dict[str, Any]:
    module = None
    for module_name in (
        "pylmgc90.pre.config.lmgc90dicts",
        "pylmgc90.pre_lmgc.config.lmgc90dicts",
    ):
        try:
            module = importlib.import_module(module_name)
            break
        except Exception:
            continue
    if module is None:
        return {}
    return {
        name: _safe_value(getattr(module, name))
        for name in _CATALOG_NAMES
        if hasattr(module, name)
    }


def inspect_runtime() -> dict[str, Any]:
    """Return pylmgc90 callables and compatibility data, or an unavailable marker.

    Imports of pylmgc90 are kept inside this function. Other engine/core package
    initialization may independently probe the optional compatibility catalogs.
    """
    try:
        pylmgc = importlib.import_module("pylmgc90")
        pre = importlib.import_module("pylmgc90.pre")
        chipy = importlib.import_module("pylmgc90.chipy")
    except Exception as exc:
        return {
            "available": False,
            "version": None,
            "apis": {},
            "catalogs": {},
            "error": f"{type(exc).__name__}: {exc}",
        }

    try:
        version = importlib.metadata.version("pylmgc90")
    except importlib.metadata.PackageNotFoundError:
        version = getattr(pylmgc, "__version__", None)

    return {
        "available": True,
        "version": version,
        "apis": {
            "pre": _public_callables(pre),
            "chipy": _public_callables(chipy),
        },
        "catalogs": _load_compatibility_catalogs(),
    }