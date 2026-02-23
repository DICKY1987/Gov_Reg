"""
Update registry with renamed directory paths.

After renaming directories to include dir_id prefix, this script updates
all file paths in the registry to reflect the new directory names.

FILE_ID: 01999000042260125104
Created: 2026-02-14
"""

import sys
import json
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(r"C:\Users\richg\Gov_Reg")
REGISTRY_FILE = PROJECT_ROOT / "01260207201000001250_REGISTRY" / "01999000042260124503_REGISTRY_file.json"


def load_registry(registry_path: Path) -> dict:
    """Load registry JSON file."""
    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_registry(registry_path: Path, data: dict):
    """Save registry JSON file."""
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_directory_mapping(project_root: Path) -> Dict[str, str]:
    """
    Build mapping of old directory names to new names (with dir_id prefix).
    
    Returns:
        Dict mapping old_name -> new_name
    """
    mapping = {}
    
    # Find all .dir_id files
    for dir_id_file in project_root.rglob(".dir_id"):
        directory = dir_id_file.parent
        
        # Skip project root
        if directory == project_root:
            continue
        
        # Read dir_id
        try:
            with open(dir_id_file, 'r') as f:
                anchor = json.load(f)
            
            dir_id = anchor['dir_id']
            current_name = directory.name
            
            # If already has dir_id prefix, extract original name
            if current_name.startswith(dir_id + "_"):
                # Already renamed, use current name
                original_name = current_name.replace(dir_id + "_", "", 1)
                mapping[original_name] = current_name
            else:
                # Not yet renamed, but we know what it should be
                new_name = f"{dir_id}_{current_name}"
                mapping[current_name] = new_name
        
        except Exception as e:
            print(f"Warning: Could not read {dir_id_file}: {e}")
            continue
    
    return mapping


def update_path_component(path: str, mapping: Dict[str, str]) -> str:
    """
    Update a path by replacing directory names with their dir_id versions.
    
    Args:
        path: Original path (e.g., "scripts/utilities/script.py")
        mapping: Dict of old_name -> new_name
    
    Returns:
        Updated path (e.g., "01260207201000001276_scripts/01260207201000001285_utilities/script.py")
    """
    parts = path.split('/')
    new_parts = []
    
    for part in parts:
        # Check if this part needs updating
        if part in mapping:
            new_parts.append(mapping[part])
        else:
            new_parts.append(part)
    
    return '/'.join(new_parts)


def update_registry_paths(registry_path: Path, project_root: Path):
    """Update all paths in registry to reflect renamed directories."""
    print(f"Loading registry: {registry_path}")
    registry = load_registry(registry_path)
    
    print("Building directory name mapping...")
    dir_mapping = build_directory_mapping(project_root)
    
    print(f"Found {len(dir_mapping)} directory mappings")
    if dir_mapping:
        print("Sample mappings:")
        for old, new in list(dir_mapping.items())[:5]:
            print(f"  {old} -> {new}")
    
    stats = {
        "total_files": 0,
        "paths_updated": 0,
        "no_change": 0,
        "errors": []
    }
    
    print("\nUpdating file paths...")
    
    # Update each file record
    if "files" in registry:
        for file_record in registry["files"]:
            stats["total_files"] += 1
            
            try:
                # Update relative_path
                if "relative_path" in file_record:
                    old_path = file_record["relative_path"]
                    new_path = update_path_component(old_path, dir_mapping)
                    
                    if old_path != new_path:
                        file_record["relative_path"] = new_path
                        stats["paths_updated"] += 1
                        
                        # Show progress every 100 updates
                        if stats["paths_updated"] % 100 == 0:
                            print(f"  Updated {stats['paths_updated']} paths...")
                    else:
                        stats["no_change"] += 1
                
                # Update directory_path if present
                if "directory_path" in file_record:
                    old_dir = file_record["directory_path"]
                    new_dir = update_path_component(old_dir, dir_mapping)
                    
                    if old_dir != new_dir:
                        file_record["directory_path"] = new_dir
                
                # Update absolute_path if present
                if "absolute_path" in file_record:
                    old_abs = file_record["absolute_path"]
                    # Convert to forward slashes for consistency
                    old_abs_normalized = old_abs.replace("\\", "/")
                    new_abs = update_path_component(old_abs_normalized, dir_mapping)
                    # Convert back to backslashes for Windows
                    new_abs = new_abs.replace("/", "\\")
                    
                    if old_abs != new_abs:
                        file_record["absolute_path"] = new_abs
            
            except Exception as e:
                error_msg = f"File {file_record.get('file_id', 'unknown')}: {e}"
                stats["errors"].append(error_msg)
                print(f"✗ Error: {error_msg}")
    
    # Create backup
    print("\nCreating backup...")
    backup_path = registry_path.with_suffix(".json.backup.dirnames")
    save_registry(backup_path, load_registry(registry_path))
    print(f"Backup created: {backup_path}")
    
    # Save updated registry
    print("Saving updated registry...")
    save_registry(registry_path, registry)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {stats['total_files']}")
    print(f"Paths updated: {stats['paths_updated']}")
    print(f"No change needed: {stats['no_change']}")
    print(f"Errors: {len(stats['errors'])}")
    
    if stats["errors"]:
        print("\nErrors encountered:")
        for error in stats["errors"][:10]:
            print(f"  - {error}")
        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")
    
    print(f"\nBackup: {backup_path}")
    print(f"Updated: {registry_path}")
    
    return stats


def main():
    """Main entry point."""
    try:
        print("=" * 60)
        print("REGISTRY PATH UPDATE TOOL")
        print("=" * 60)
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Registry file: {REGISTRY_FILE}")
        print()
        
        if not REGISTRY_FILE.exists():
            print(f"Error: Registry file not found: {REGISTRY_FILE}")
            return 1
        
        stats = update_registry_paths(REGISTRY_FILE, PROJECT_ROOT)
        
        if stats["errors"]:
            return 1
        
        print("\n✅ Registry paths updated successfully!")
        return 0
    
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
