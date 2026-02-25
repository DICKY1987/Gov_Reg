"""
Populate dir_id field in registry files list using IDPKG config.

FILE_ID: 01999000042260125102
Created: 2026-02-14
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

CORE_PATH = Path(__file__).parent.parent / "01260207201000001173_govreg_core"
if str(CORE_PATH) not in sys.path:
    sys.path.insert(0, str(CORE_PATH))

from P_01999000042260126000__idpkg_runtime import IdpkgConfig
from P_01260207233100000069_dir_id_handler import DirIdManager
from P_01999000042260124030_shared_utils import atomic_json_read, atomic_json_write


def apply_patch(registry: Dict[str, Any], patch_ops: List[Dict[str, Any]]) -> Dict[str, Any]:
    updated = json.loads(json.dumps(registry))
    for op in patch_ops:
        path = op["path"].strip("/")
        parts = path.split("/") if path else []
        target = updated
        for part in parts[:-1]:
            if part.isdigit():
                target = target[int(part)]
            else:
                target = target[part]
        key = parts[-1]
        if key.isdigit():
            key = int(key)

        if op["op"] == "add" or op["op"] == "replace":
            target[key] = op["value"]
        elif op["op"] == "remove":
            if isinstance(target, list):
                target.pop(key)
            else:
                target.pop(key, None)
    return updated


def get_dir_id_for_file(file_path: Path, manager: DirIdManager) -> Optional[str]:
    try:
        anchor = manager.read_dir_id(file_path.parent)
        return anchor.dir_id if anchor else None
    except Exception:
        return None


def populate_dir_ids(config_path: Path) -> int:
    config = IdpkgConfig.load(config_path)
    registry_path = config.registry_path

    registry = atomic_json_read(registry_path)
    manager = DirIdManager()

    patch_ops: List[Dict[str, Any]] = []
    stats = {
        "total_files": 0,
        "dir_id_added": 0,
        "dir_id_missing": 0,
        "errors": [],
    }

    print(f"Loading registry from: {registry_path}")
    print("Processing file records...")

    for idx, record in enumerate(registry.get("files", [])):
        stats["total_files"] += 1
        rel_path = record.get("relative_path")
        if not rel_path:
            stats["errors"].append(f"Missing relative_path for file at index {idx}")
            continue

        file_path = config.project_root_path / rel_path
        dir_id = get_dir_id_for_file(file_path, manager)
        current = record.get("dir_id")
        if dir_id:
            if current != dir_id:
                patch_ops.append({
                    "op": "replace" if "dir_id" in record else "add",
                    "path": f"/files/{idx}/dir_id",
                    "value": dir_id,
                })
                stats["dir_id_added"] += 1
        else:
            if current is not None:
                patch_ops.append({
                    "op": "replace",
                    "path": f"/files/{idx}/dir_id",
                    "value": None,
                })
            stats["dir_id_missing"] += 1

    if not patch_ops:
        print("No updates required.")
        return 0

    config.patch_output_dir.mkdir(parents=True, exist_ok=True)
    patch_path = config.patch_output_dir / "idpkg_patch_populate_dir_ids.json"
    with open(patch_path, "w", encoding="utf-8") as f:
        json.dump(patch_ops, f, indent=2)

    updated_registry = apply_patch(registry, patch_ops)
    atomic_json_write(registry_path, updated_registry)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {stats['total_files']}")
    print(f"dir_id values added: {stats['dir_id_added']}")
    print(f"dir_id missing: {stats['dir_id_missing']}")
    print(f"Errors: {len(stats['errors'])}")
    print(f"Patch written: {patch_path}")

    if stats["errors"]:
        print("\nErrors:")
        for error in stats["errors"][:10]:
            print(f"  - {error}")

    return 1 if stats["errors"] else 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Populate dir_id field in registry")
    parser.add_argument("--config", type=Path, default=Path(".idpkg") / "config.json", help="Path to IDPKG config")

    args = parser.parse_args()
    if not args.config.exists():
        print(f"Config not found: {args.config}")
        return 1

    return populate_dir_ids(args.config)


if __name__ == "__main__":
    raise SystemExit(main())
