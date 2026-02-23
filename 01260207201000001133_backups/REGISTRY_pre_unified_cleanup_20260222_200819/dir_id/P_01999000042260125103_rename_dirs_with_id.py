"""
Rename directories to include dir_id prefix.

This script renames all directories to include their dir_id as a prefix,
similar to how files have file_id prefixes.

Format: {dir_id}_{original_name}
Example: scripts -> 01260207201000001276_scripts

FILE_ID: 01999000042260125103
Created: 2026-02-14
"""

import sys
import json
from pathlib import Path
from typing import List, Tuple
import shutil

# Add govreg_core to path
govreg_core_path = Path(__file__).parent.parent / "govreg_core"
sys.path.insert(0, str(govreg_core_path))

from P_01999000042260125068_dir_id_handler import DirIdManager

PROJECT_ROOT = Path(r"C:\Users\richg\Gov_Reg")


def get_dir_rename_plan(project_root: Path, manager: DirIdManager) -> List[Tuple[Path, Path, str]]:
    """
    Create rename plan for all directories.
    
    Returns:
        List of (old_path, new_path, dir_id) tuples
    """
    rename_plan = []
    
    # Find all directories with .dir_id files
    for dir_id_file in sorted(project_root.rglob(".dir_id")):
        directory = dir_id_file.parent
        
        # Skip if directory is project root
        if directory == project_root:
            continue
        
        # Read dir_id
        try:
            anchor = manager.read_dir_id(directory)
            if not anchor:
                continue
            
            dir_id = anchor.dir_id
            original_name = directory.name
            
            # Check if already renamed
            if original_name.startswith(dir_id):
                continue
            
            # Build new name
            new_name = f"{dir_id}_{original_name}"
            new_path = directory.parent / new_name
            
            rename_plan.append((directory, new_path, dir_id))
        
        except Exception as e:
            print(f"Error reading .dir_id for {directory}: {e}")
            continue
    
    return rename_plan


def validate_rename_plan(rename_plan: List[Tuple[Path, Path, str]]) -> Tuple[bool, List[str]]:
    """
    Validate rename plan for conflicts.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    new_paths = set()
    
    for old_path, new_path, dir_id in rename_plan:
        # Check if target already exists
        if new_path.exists():
            errors.append(f"Target already exists: {new_path}")
        
        # Check for duplicates in plan
        if new_path in new_paths:
            errors.append(f"Duplicate target in plan: {new_path}")
        
        new_paths.add(new_path)
    
    return (len(errors) == 0, errors)


def execute_rename(rename_plan: List[Tuple[Path, Path, str]], dry_run: bool = True):
    """
    Execute directory renames.
    
    Renames are done in depth-first order (deepest first) to avoid
    conflicts with parent directories.
    """
    # Sort by depth (deepest first)
    sorted_plan = sorted(rename_plan, key=lambda x: len(x[0].parts), reverse=True)
    
    stats = {
        "total": len(sorted_plan),
        "renamed": 0,
        "errors": []
    }
    
    print(f"Rename plan: {stats['total']} directories")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("-" * 60)
    
    for old_path, new_path, dir_id in sorted_plan:
        try:
            rel_old = old_path.relative_to(PROJECT_ROOT)
            rel_new = new_path.relative_to(PROJECT_ROOT)
            
            if dry_run:
                print(f"→ Would rename: {rel_old}")
                print(f"             to: {rel_new}")
            else:
                old_path.rename(new_path)
                stats["renamed"] += 1
                print(f"✓ Renamed: {rel_old}")
                print(f"        to: {rel_new}")
        
        except Exception as e:
            error_msg = f"{old_path}: {e}"
            stats["errors"].append(error_msg)
            print(f"✗ Error: {error_msg}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total directories: {stats['total']}")
    if not dry_run:
        print(f"Successfully renamed: {stats['renamed']}")
    print(f"Errors: {len(stats['errors'])}")
    
    if stats["errors"]:
        print("\nErrors encountered:")
        for error in stats["errors"][:10]:
            print(f"  - {error}")
        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")
    
    return stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rename directories to include dir_id prefix")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without actually renaming")
    parser.add_argument("--force", action="store_true", help="Proceed even with validation warnings")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("DIRECTORY RENAME TOOL")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print("")
    
    # Initialize manager
    manager = DirIdManager(PROJECT_ROOT)
    
    # Create rename plan
    print("Creating rename plan...")
    rename_plan = get_dir_rename_plan(PROJECT_ROOT, manager)
    
    if not rename_plan:
        print("No directories need renaming.")
        return 0
    
    # Validate plan
    print("Validating rename plan...")
    is_valid, errors = validate_rename_plan(rename_plan)
    
    if not is_valid:
        print("\n✗ VALIDATION ERRORS:")
        for error in errors:
            print(f"  - {error}")
        
        if not args.force:
            print("\nRename aborted. Use --force to proceed anyway.")
            return 1
        else:
            print("\n⚠ Proceeding despite validation errors (--force)")
    else:
        print("✓ Validation passed")
    
    print("")
    
    # Execute rename
    stats = execute_rename(rename_plan, dry_run=args.dry_run)
    
    if args.dry_run:
        print("\n⚠ This was a dry run. Use without --dry-run to actually rename.")
        return 0
    
    if stats["errors"]:
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
