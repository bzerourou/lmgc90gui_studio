"""Build a serializable capability snapshot from the installed pylmgc90 API."""
from __future__ import annotations

import importlib
import importlib.metadata
import inspect
import re
from collections.abc import Mapping
from enum import Enum
from functools import lru_cache
from typing import Any

from lmgc90_core.lmgc_dicts import load_capability_snapshot


def _safe_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return _safe_value(value.value)
    if isinstance(value, Mapping):
        return {str(key): _safe_value(item) for key, item in value.items()}
    if hasattr(value, "root") and hasattr(value, "childs"):
        return {
            "root": _safe_value(value.root),
            "children": [_safe_value(child) for child in value.childs],
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_safe_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _describe_callable(name: str, member: Any) -> dict[str, Any]:
    parameters: list[dict[str, Any]] = []
    signature_text = None
    arity = None
    arity_source = "unknown"
    try:
        signature = inspect.signature(member)
    except (TypeError, ValueError):
        signature = None
    if signature is not None:
        signature_text = str(signature)
        signature_parameters = tuple(signature.parameters.values())
        has_variadic = any(
            parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            )
            for parameter in signature_parameters
        )
        if not has_variadic:
            arity = sum(
                parameter.kind in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
                for parameter in signature_parameters
            )
            arity_source = "signature"
        for parameter in signature_parameters:
            required = parameter.default is inspect.Parameter.empty
            default = None if required else _safe_value(parameter.default)
            parameters.append({
                "name": parameter.name,
                "kind": parameter.kind.name,
                "required": required,
                "default": default,
            })

    doc = inspect.getdoc(member)
    if arity is None and doc:
        first_line = doc.strip().splitlines()[0]
        match = re.match(r"^[\w.]*\((.*?)\)", first_line)
        if match is not None:
            arguments = match.group(1).strip()
            arity = 0 if not arguments else len(arguments.split(","))
            arity_source = "docstring"

    return {
        "name": name,
        "signature": signature_text,
        "parameters": parameters,
        "arity": arity,
        "arity_source": arity_source,
        "doc": doc,
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


def _runtime_catalogs() -> dict[str, Any]:
    try:
        module = importlib.import_module("pylmgc90.pre.config.lmgc90dicts")
    except Exception:
        return {}
    return {
        name: _safe_value(value)
        for name, value in sorted(vars(module).items())
        if not name.startswith("_")
        and isinstance(value, (Mapping, list, tuple, set, frozenset))
    }


def _snapshot_catalogs(version: str | None = None) -> dict[str, Any]:
    try:
        return load_capability_snapshot(version)["catalogs"]
    except (FileNotFoundError, LookupError):
        return {}


def _installed_runtime_version() -> str | None:
    try:
        return importlib.metadata.version("pylmgc90")
    except importlib.metadata.PackageNotFoundError:
        try:
            runtime = importlib.import_module("pylmgc90")
        except ImportError:
            return None
        version = getattr(runtime, "__version__", None)
        return version if isinstance(version, str) and version else None


@lru_cache(maxsize=1)
def _catalog_data() -> tuple[str, dict[str, Any]]:
    snapshot_catalogs = _snapshot_catalogs(_installed_runtime_version())
    if snapshot_catalogs:
        return "SNAPSHOT", snapshot_catalogs
    runtime_catalogs = _runtime_catalogs()
    if runtime_catalogs:
        return "INTROSPECTION", runtime_catalogs
    return "FALLBACK", {}


@lru_cache(maxsize=1)
def load_compatibility_catalogs() -> dict[str, Any]:
    """Load bundled snapshot catalogs, or introspect runtime when no snapshot exists."""
    return _catalog_data()[1]


def compatibility_catalog_source() -> str:
    """Return whether snapshot, runtime introspection, or core fallback is active."""
    return _catalog_data()[0]


def clear_compatibility_catalog_cache() -> None:
    """Refresh compatibility data after the bundled snapshot index changes."""
    load_compatibility_catalogs.cache_clear()
    _catalog_data.cache_clear()


def inspect_runtime() -> dict[str, Any]:
    """Return pylmgc90 callables and runtime catalogs, or an unavailable marker.

    Imports of pylmgc90 stay in this module and are only executed when runtime
    data is requested. Core package initialization never probes the runtime.
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

    runtime_catalogs = _runtime_catalogs()
    return {
        "available": True,
        "version": version,
        "apis": {
            "pre": _public_callables(pre),
            "chipy": _public_callables(chipy),
        },
        "catalogs": runtime_catalogs,
        "catalog_source": "INTROSPECTION" if runtime_catalogs else "UNAVAILABLE",
    }
