"""
Generate .dir_id files for governed directories using IDPKG config.

FILE_ID: 01999000042260125100
Created: 2026-02-14
"""
from __future__ import annotations

from pathlib import Path
import sys

CORE_PATH = Path(__file__).parent.parent / "01260207201000001173_govreg_core"
if str(CORE_PATH) not in sys.path:
    sys.path.insert(0, str(CORE_PATH))

from P_01999000042260126000__idpkg_runtime import IdpkgConfig
from P_01260207233100000068_zone_classifier import ZoneClassifier
from P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver


def generate_dir_ids(config_path: Path, dry_run: bool = False) -> dict:
    config = IdpkgConfig.load(config_path)
    zone_classifier = ZoneClassifier(exclusions=config.exclusions)
    resolver = DirectoryIdentityResolver(
        project_root=config.project_root_path,
        project_root_id=config.project_root_id,
        zone_classifier=zone_classifier,
    )

    stats = {
        "total_dirs": 0,
        "governed_dirs": 0,
        "existing_dir_ids": 0,
        "created_dir_ids": 0,
        "errors": [],
    }

    print(f"Scanning directories in: {config.project_root_path}")
    print(f"Dry run: {dry_run}")
    print("-" * 60)

    for directory in sorted(config.project_root_path.rglob("*")):
        if not directory.is_dir():
            continue

        stats["total_dirs"] += 1
        rel_path = str(directory.relative_to(config.project_root_path)).replace("\\", "/")
        if zone_classifier.should_skip(rel_path):
            continue

        zone = zone_classifier.compute_zone(rel_path)
        if zone != "governed":
            continue

        stats["governed_dirs"] += 1

        try:
            result = resolver.resolve_identity(directory, allocate_if_missing=not dry_run)
            if result.status == "exists":
                stats["existing_dir_ids"] += 1
                print(f"Exists: {rel_path}")
            elif result.status == "allocated":
                stats["created_dir_ids"] += 1
                print(f"Created: {rel_path} -> {result.dir_id}")
            elif result.status == "missing" and dry_run:
                print(f"Would create: {rel_path}")
            elif result.status == "error":
                stats["errors"].append(f"{rel_path}: {result.error_message}")
                print(f"Error: {rel_path}: {result.error_message}")
        except Exception as exc:
            stats["errors"].append(f"{rel_path}: {exc}")
            print(f"Error: {rel_path}: {exc}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total directories scanned: {stats['total_dirs']}")
    print(f"Governed directories: {stats['governed_dirs']}")
    print(f"Existing .dir_id files: {stats['existing_dir_ids']}")
    print(f"Created .dir_id files: {stats['created_dir_ids']}")
    print(f"Errors: {len(stats['errors'])}")

    if stats["errors"]:
        print("\nErrors encountered:")
        for error in stats["errors"][:10]:
            print(f"  - {error}")

    return stats


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate .dir_id files for governed directories")
    parser.add_argument("--config", type=Path, default=Path(".idpkg") / "config.json", help="Path to IDPKG config")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing files")

    args = parser.parse_args()

    if not args.config.exists():
        print(f"Config not found: {args.config}")
        return 1

    stats = generate_dir_ids(args.config, dry_run=args.dry_run)
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
