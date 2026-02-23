"""
Validate .dir_id files for governed directories using IDPKG config.

FILE_ID: 01999000042260125101
Created: 2026-02-14
"""
from __future__ import annotations

from pathlib import Path
import sys

CORE_PATH = Path(__file__).parent.parent / "01260207201000001173_govreg_core"
if str(CORE_PATH) not in sys.path:
    sys.path.insert(0, str(CORE_PATH))

from P_01999000042260126000__idpkg_runtime import IdpkgEngine


def validate_all_dir_ids(config_path: Path) -> int:
    engine = IdpkgEngine(config_path)
    stats = {
        "total_checked": 0,
        "valid": 0,
        "invalid": 0,
        "errors": [],
    }

    print(f"Validating .dir_id files in: {engine.config.project_root_path}")
    print("-" * 60)

    for directory in engine._walk_directories():
        rel_path = str(directory.relative_to(engine.config.project_root_path)).replace("\\", "/")
        zone = engine.zone_classifier.compute_zone(rel_path)
        if zone != "governed":
            continue

        stats["total_checked"] += 1
        anchor = engine.dir_manager.read_dir_id(directory)
        errors = engine._validate_dir_anchor(anchor)
        if errors:
            stats["invalid"] += 1
            stats["errors"].append(f"{rel_path}: {'; '.join(errors)}")
            print(f"Invalid: {rel_path}: {'; '.join(errors)}")
        else:
            stats["valid"] += 1
            print(f"Valid: {rel_path}")

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total .dir_id files checked: {stats['total_checked']}")
    print(f"Valid: {stats['valid']}")
    print(f"Invalid: {stats['invalid']}")

    if stats["errors"]:
        print("\nErrors:")
        for error in stats["errors"][:10]:
            print(f"  - {error}")
        return 1

    print("\nAll .dir_id files are valid")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate .dir_id files for governed directories")
    parser.add_argument("--config", type=Path, default=Path(".idpkg") / "config.json", help="Path to IDPKG config")

    args = parser.parse_args()
    if not args.config.exists():
        print(f"Config not found: {args.config}")
        return 1

    return validate_all_dir_ids(args.config)


if __name__ == "__main__":
    raise SystemExit(main())
