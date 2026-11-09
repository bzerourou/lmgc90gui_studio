"""Export versioned pylmgc90 runtime capabilities as a JSON snapshot."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Sequence

from lmgc90_core import __file__ as _CORE_PACKAGE_FILE

from .introspection import clear_compatibility_catalog_cache, inspect_runtime


SNAPSHOT_SCHEMA_VERSION = 1
_BUNDLED_CAPABILITIES_DIR = (
    Path(_CORE_PACKAGE_FILE).resolve().parent / "capabilities"
)


def build_capability_snapshot() -> dict:
    """Inspect the installed runtime and return a versioned, JSON-safe snapshot."""
    runtime = inspect_runtime()
    if not runtime["available"]:
        raise RuntimeError(
            "cannot generate pylmgc90 capabilities: "
            f"{runtime.get('error', 'runtime unavailable')}"
        )
    version = runtime.get("version")
    if not isinstance(version, str) or not version.strip():
        raise RuntimeError("cannot generate a versioned snapshot: pylmgc90 version is unknown")
    catalogs = runtime.get("catalogs")
    if (
        runtime.get("catalog_source") != "INTROSPECTION"
        or not isinstance(catalogs, dict)
        or not catalogs
    ):
        raise RuntimeError(
            "cannot generate pylmgc90 capabilities: runtime catalogs could not be "
            "introspected; refusing to copy compatibility snapshot data"
        )

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "runtime": {
            "name": "pylmgc90",
            "version": version,
        },
        "apis": runtime["apis"],
        "catalogs": catalogs,
    }


def write_capability_snapshot(
    output_dir: str | Path = _BUNDLED_CAPABILITIES_DIR,
) -> Path:
    """Write the version-specific snapshot and update the bundled index."""
    snapshot = build_capability_snapshot()
    version = snapshot["runtime"]["version"]
    filename_version = re.sub(r"[^A-Za-z0-9._+-]+", "-", version).strip(".-")
    if not filename_version:
        raise ValueError(f"pylmgc90 version cannot be used in a filename: {version!r}")

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"pylmgc90-{filename_version}.json"
    snapshot_path = directory / filename
    index_path = directory / "index.json"
    snapshots = {}
    if index_path.is_file():
        existing_index = json.loads(index_path.read_text(encoding="utf-8"))
        if existing_index.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
            raise ValueError(
                "cannot update capability index with unsupported schema version "
                f"{existing_index.get('schema_version')!r}"
            )
        snapshots = existing_index.get("snapshots", {})
        if not isinstance(snapshots, dict):
            raise ValueError("invalid snapshots mapping in capability index")
    snapshots[version] = filename
    snapshot_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    index = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "latest": filename,
        "snapshots": snapshots,
    }
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    clear_compatibility_catalog_cache()
    return snapshot_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect pylmgc90 and write a versioned JSON capability snapshot."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_BUNDLED_CAPABILITIES_DIR,
        help=(
            "snapshot directory (defaults to the core package's bundled "
            "capabilities directory)"
        ),
    )
    args = parser.parse_args(argv)
    snapshot_path = write_capability_snapshot(args.output_dir)
    print(snapshot_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
