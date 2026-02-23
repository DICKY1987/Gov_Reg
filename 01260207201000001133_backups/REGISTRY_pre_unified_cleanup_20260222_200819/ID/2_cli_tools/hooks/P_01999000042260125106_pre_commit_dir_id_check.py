"""Pre-commit hook for .dir_id validation (GAP-002).

FILE_ID: 01999000042260125106
PURPOSE: Git pre-commit hook to validate .dir_id files
PHASE: Phase 2 - Continuous Enforcement
BACKLOG: 01999000042260125103 GAP-002
"""
from __future__ import annotations

import json
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# Add parent to path for imports
repo_root = Path(__file__).parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

sys.path.insert(0, str(Path(__file__).parent.parent / "01260207201000001173_govreg_core"))
from P_01260207233100000069_dir_id_handler import DirIdManager
from P_01260207233100000068_zone_classifier import ZoneClassifier


def get_staged_files() -> List[str]:
    """Get list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split('\n') if result.stdout.strip() else []


def check_new_governed_directories_have_dir_id(
    staged_files: List[str],
    project_root: Path
) -> List[Tuple[str, str]]:
    """Check that new governed directories have .dir_id."""
    errors = []
    zone_classifier = ZoneClassifier()
    
    # Find new directories
    new_dirs = set()
    for file_path in staged_files:
        full_path = project_root / file_path
        if full_path.is_file():
            new_dirs.add(full_path.parent)
    
    # Check each directory
    for directory in new_dirs:
        zone = zone_classifier.compute_zone(directory)
        if zone == 'governed':
            dir_id_path = directory / ".dir_id"
            if not dir_id_path.exists():
                errors.append((
                    str(directory.relative_to(project_root)),
                    "New governed directory missing .dir_id"
                ))
    
    return errors


def check_modified_dir_id_files_are_valid(
    staged_files: List[str],
    project_root: Path
) -> List[Tuple[str, str]]:
    """Check that modified .dir_id files are valid."""
    errors = []
    dir_id_manager = DirIdManager()
    
    for file_path in staged_files:
        if not file_path.endswith(".dir_id"):
            continue
        
        full_path = project_root / file_path
        if not full_path.exists():
            continue
        
        try:
            # Validate by reading
            anchor = dir_id_manager.read_dir_id(full_path.parent)
            
            # Basic validation
            if not anchor or not anchor.dir_id:
                errors.append((file_path, "Invalid .dir_id: missing dir_id field"))
            elif len(anchor.dir_id) != 20:
                errors.append((file_path, f"Invalid .dir_id: wrong length ({len(anchor.dir_id)} != 20)"))
        
        except ValueError as e:
            errors.append((file_path, f"Invalid .dir_id: {e}"))
        except Exception as e:
            errors.append((file_path, f"Error reading .dir_id: {e}"))
    
    return errors


def check_no_duplicate_dir_ids(
    staged_files: List[str],
    project_root: Path
) -> List[Tuple[str, str]]:
    """Check for duplicate dir_id allocations."""
    errors = []
    dir_id_manager = DirIdManager()
    seen_dir_ids = {}
    
    for file_path in staged_files:
        if not file_path.endswith(".dir_id"):
            continue
        
        full_path = project_root / file_path
        if not full_path.exists():
            continue
        
        try:
            anchor = dir_id_manager.read_dir_id(full_path.parent)
            if anchor and anchor.dir_id:
                if anchor.dir_id in seen_dir_ids:
                    errors.append((
                        file_path,
                        f"Duplicate dir_id {anchor.dir_id} (also in {seen_dir_ids[anchor.dir_id]})"
                    ))
                else:
                    seen_dir_ids[anchor.dir_id] = file_path
        except Exception:
            pass  # Already caught in validation check
    
    return errors


def main() -> int:
    """Main pre-commit hook."""
    project_root = Path.cwd()
    staged_files = get_staged_files()
    
    if not staged_files:
        return 0
    
    errors = []
    
    # Run checks
    errors.extend(check_new_governed_directories_have_dir_id(staged_files, project_root))
    errors.extend(check_modified_dir_id_files_are_valid(staged_files, project_root))
    errors.extend(check_no_duplicate_dir_ids(staged_files, project_root))
    
    if errors:
        print("❌ Pre-commit hook failed: .dir_id validation errors\n")
        for file_path, error_msg in errors:
            print(f"  • {file_path}: {error_msg}")
        print("\nPlease fix these issues before committing.")
        return 1
    
    print("✅ Pre-commit hook passed: All .dir_id files valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
