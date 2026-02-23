"""File Creator Module - Create files with pre-assigned IDs.

FILE_ID: 01999000042260124028
DOC_ID: P_01999000042260124028

This module provides the 'create' command that allocates an ID,
creates the file with the ID in its name/content, and updates
the governance registry atomically.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "PATH_FILES"))

try:
    from path_registry import import_module
    id_allocator = import_module("ID_ALLOCATOR")
    shared_utils = import_module("SHARED_UTILS")
    allocate_single_id = id_allocator.allocate_single_id
    allocate_batch_ids = id_allocator.allocate_batch_ids
    utc_timestamp = shared_utils.utc_timestamp
    atomic_json_read = shared_utils.atomic_json_read
    atomic_json_write = shared_utils.atomic_json_write
except ImportError:
    # Fallback to direct import
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from P_01999000042260124027_id_allocator import allocate_single_id, allocate_batch_ids
    from P_01999000042260124030_shared_utils import utc_timestamp, atomic_json_read, atomic_json_write


def determine_file_type(filename: str) -> tuple[str, str, bool]:
    """Determine file type, layer, and whether it needs P_ prefix.
    
    Returns:
        (artifact_kind, layer, needs_p_prefix)
    """
    ext = Path(filename).suffix.lower()
    name = Path(filename).stem.lower()
    
    # Python files get P_ prefix
    if ext == ".py":
        needs_prefix = True
        
        if name.startswith("test_"):
            return ("TEST", "TESTING", needs_prefix)
        elif "test" in name:
            return ("TEST", "TESTING", needs_prefix)
        else:
            return ("PYTHON_MODULE", "CORE", needs_prefix)
    
    # Other file types
    needs_prefix = False
    
    if ext in [".json", ".yaml", ".yml"]:
        if "schema" in name:
            return ("SCHEMA", "VALIDATION", needs_prefix)
        elif "config" in name or "settings" in name:
            return ("JSON", "CONFIGURATION", needs_prefix)
        else:
            return ("JSON", "SSOT", needs_prefix)
    
    elif ext == ".md":
        if "readme" in name:
            return ("MARKDOWN", "DOCUMENTATION", needs_prefix)
        elif "guide" in name or "tutorial" in name:
            return ("MARKDOWN", "DOCUMENTATION", needs_prefix)
        elif "report" in name:
            return ("MARKDOWN", "EVIDENCE", needs_prefix)
        else:
            return ("MARKDOWN", "DOCUMENTATION", needs_prefix)
    
    elif ext in [".txt", ".ini"]:
        return ("TEXT", "CONFIGURATION", needs_prefix)
    
    elif ext in [".sh", ".bash"]:
        return ("SHELL_SCRIPT", "AUTOMATION", needs_prefix)
    
    else:
        return ("UNKNOWN", "OTHER", needs_prefix)


def format_filename_with_id(original_name: str, file_id: str, needs_p_prefix: bool) -> str:
    """Format filename with ID according to convention.
    
    Args:
        original_name: Original filename (e.g., "my_module.py")
        file_id: Allocated file ID
        needs_p_prefix: Whether to use P_ prefix
        
    Returns:
        Formatted filename
    """
    if needs_p_prefix:
        # Python files: P_{FILE_ID}_{original_name}
        return f"P_{file_id}_{original_name}"
    else:
        # Other files: DOC-{TYPE}-{NAME}-{FILE_ID}__{original_name}
        # For now, use simple format
        return f"DOC-FILE-{file_id}__{original_name}"


def create_file_header(file_id: str, filename: str, description: str = "") -> str:
    """Generate file header with ID information.
    
    Args:
        file_id: The allocated file ID
        filename: The filename
        description: Optional file description
        
    Returns:
        Header string appropriate for the file type
    """
    ext = Path(filename).suffix.lower()
    
    if ext == ".py":
        return f'''"""
{description or 'Python module'}

FILE_ID: {file_id}
DOC_ID: P_{file_id}
"""
'''
    
    elif ext == ".md":
        return f'''# {description or 'Documentation'}

**FILE_ID**: {file_id}  
**Created**: {utc_timestamp()}

---

'''
    
    elif ext in [".json", ".yaml", ".yml"]:
        # JSON/YAML files typically don't have headers, but we can add a comment field
        return ""
    
    else:
        return f"# FILE_ID: {file_id}\n# Created: {utc_timestamp()}\n\n"


def create_file_with_id(
    filename: str,
    content: str = "",
    description: str = "",
    directory: Optional[Path] = None,
    update_registry: bool = True
) -> tuple[str, Path]:
    """Create a file with a pre-allocated ID.
    
    Args:
        filename: Desired filename (will be prefixed with ID)
        content: Initial file content (header will be prepended)
        description: File description for header
        directory: Target directory (default: current)
        update_registry: Whether to update governance_registry.json
        
    Returns:
        (file_id, full_path) tuple
    """
    # Allocate ID
    purpose = description or f"Create {filename}"
    file_id = allocate_single_id(purpose)
    
    # Determine file properties
    artifact_kind, layer, needs_p_prefix = determine_file_type(filename)
    
    # Format filename with ID
    new_filename = format_filename_with_id(filename, file_id, needs_p_prefix)
    
    # Resolve target path
    if directory is None:
        directory = Path.cwd()
    else:
        directory = Path(directory)
    
    full_path = directory / new_filename
    
    # Ensure directory exists
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate header
    header = create_file_header(file_id, filename, description)
    
    # Combine header and content
    full_content = header + content
    
    # Write file
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(full_content)
    
    print(f"✅ Created: {full_path}")
    print(f"   File ID: {file_id}")
    
    # Update registry
    if update_registry:
        try:
            _update_registry(file_id, full_path, layer, artifact_kind)
            print(f"   Registry: Updated")
        except Exception as e:
            print(f"   Registry: Failed to update - {e}")
    
    return file_id, full_path


def create_batch_files(
    filenames: List[str],
    descriptions: Optional[List[str]] = None,
    directory: Optional[Path] = None,
    update_registry: bool = True
) -> List[tuple[str, Path]]:
    """Create multiple files with pre-allocated IDs.
    
    Args:
        filenames: List of desired filenames
        descriptions: Optional list of descriptions
        directory: Target directory (default: current)
        update_registry: Whether to update governance_registry.json
        
    Returns:
        List of (file_id, full_path) tuples
    """
    if descriptions is None:
        descriptions = [""] * len(filenames)
    
    if len(descriptions) != len(filenames):
        raise ValueError("Descriptions list must match filenames list length")
    
    # Allocate all IDs upfront (atomic)
    file_ids = allocate_batch_ids(len(filenames), f"Batch create {len(filenames)} files")
    
    results = []
    for file_id, filename, description in zip(file_ids, filenames, descriptions):
        try:
            artifact_kind, layer, needs_p_prefix = determine_file_type(filename)
            new_filename = format_filename_with_id(filename, file_id, needs_p_prefix)
            
            if directory is None:
                directory = Path.cwd()
            else:
                directory = Path(directory)
            
            full_path = directory / new_filename
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            header = create_file_header(file_id, filename, description)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(header)
            
            print(f"✅ Created: {full_path}")
            print(f"   File ID: {file_id}")
            
            if update_registry:
                try:
                    _update_registry(file_id, full_path, layer, artifact_kind)
                    print(f"   Registry: Updated")
                except Exception as e:
                    print(f"   Registry: Failed - {e}")
            
            results.append((file_id, full_path))
        
        except Exception as e:
            print(f"❌ Failed to create {filename}: {e}")
            results.append((file_id, None))
    
    return results


def _update_registry(file_id: str, full_path: Path, layer: str, artifact_kind: str) -> None:
    """Update governance_registry.json with new file entry (with file locking)."""
    registry_path = Path("governance_registry.json")
    
    if not registry_path.exists():
        print(f"Warning: Registry not found at {registry_path}")
        return
    
    # Read with lock
    registry = atomic_json_read(registry_path)
    
    # Get relative path from registry location
    try:
        relative_path = full_path.relative_to(Path.cwd())
    except ValueError:
        relative_path = full_path
    
    # Add new entry
    new_entry = {
        "file_id": file_id,
        "relative_path": str(relative_path).replace("\\", "/"),
        "layer": layer,
        "artifact_kind": artifact_kind
    }
    
    # Check if already exists
    if "files" not in registry:
        registry["files"] = []
    
    existing = [f for f in registry["files"] if f.get("file_id") == file_id]
    if existing:
        print(f"Warning: File ID {file_id} already in registry")
        return
    
    registry["files"].append(new_entry)
    registry["generated"] = utc_timestamp()
    
    # Write back with lock
    atomic_json_write(registry_path, registry)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python P_01999000042260124028_file_creator.py create <filename> [description]")
        print("  python P_01999000042260124028_file_creator.py batch <file1> <file2> ...")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "create":
        if len(sys.argv) < 3:
            print("Error: create command requires filename")
            sys.exit(1)
        
        filename = sys.argv[2]
        description = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        
        file_id, path = create_file_with_id(filename, description=description)
        print(f"\n✅ Success! File created with ID: {file_id}")
    
    elif cmd == "batch":
        if len(sys.argv) < 3:
            print("Error: batch command requires at least one filename")
            sys.exit(1)
        
        filenames = sys.argv[2:]
        results = create_batch_files(filenames)
        
        success = sum(1 for _, path in results if path is not None)
        print(f"\n✅ Created {success}/{len(filenames)} files")
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
