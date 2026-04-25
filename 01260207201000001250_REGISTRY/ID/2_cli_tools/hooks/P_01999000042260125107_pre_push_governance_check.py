"""Pre-push hook for governance validation (GAP-002).

FILE_ID: 01999000042260125107
PURPOSE: Git pre-push hook to validate full governance compliance
PHASE: Phase 2 - Continuous Enforcement
BACKLOG: 01999000042260125103 GAP-002
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Tuple

SCRIPT_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = SCRIPT_ROOT / "ID" / "1_runtime"

if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver
from P_01260207233100000068_zone_classifier import ZoneClassifier
from P_01260207233100000069_dir_id_handler import DirIdManager


def _detect_project_root() -> Path:
    cwd = Path.cwd().resolve()
    for candidate in (cwd, SCRIPT_ROOT):
        if (candidate / ".idpkg" / "config.json").exists():
            return candidate
    return SCRIPT_ROOT


def _load_registry_path(project_root: Path) -> Path:
    config_path = project_root / ".idpkg" / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
        registry_value = config.get("registry", {}).get("registry_path")
        if registry_value:
            registry_path = Path(registry_value)
            if not registry_path.is_absolute():
                registry_path = (project_root / registry_path).resolve()
            return registry_path

    for candidate_name in (
        "01999000042260124503_REGISTRY_file.json",
        "01999000042260124503_governance_registry_unified.json",
    ):
        candidate = project_root / candidate_name
        if candidate.exists():
            return candidate

    return project_root / "01999000042260124503_REGISTRY_file.json"


def check_all_governed_directories_have_dir_id(project_root: Path) -> List[Tuple[str, str]]:
    """Check that all governed directories have .dir_id."""
    errors = []
    zone_classifier = ZoneClassifier(project_root=project_root)
    dir_id_manager = DirIdManager(project_root=project_root)
    
    # Scan all directories
    for directory in project_root.rglob("*"):
        if not directory.is_dir():
            continue
        
        # Skip excluded paths
        excluded_patterns = ['.git', '__pycache__', 'node_modules', '.state', '.quarantine']
        if any(pattern in directory.parts for pattern in excluded_patterns):
            continue
        
        # Check zone
        zone = zone_classifier.compute_zone(directory)
        if zone == 'governed':
            if not dir_id_manager.exists(directory):
                errors.append((
                    str(directory.relative_to(project_root)),
                    "Governed directory missing .dir_id"
                ))
    
    return errors


def check_registry_in_sync_with_filesystem(project_root: Path) -> List[Tuple[str, str]]:
    """Check that registry is in sync with filesystem."""
    errors = []

    registry_path = _load_registry_path(project_root)
    if not registry_path.exists():
        return [("registry", "Governance registry not found")]
    
    # Load registry
    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    except Exception as e:
        return [("registry", f"Failed to load registry: {e}")]
    
    # Check paths exist
    registry_files = registry.get('files', [])
    for entry in registry_files[:100]:  # Limit check to first 100 for performance
        relative_path = entry.get('relative_path', '')
        if relative_path:
            file_path = project_root / relative_path
            if not file_path.exists():
                errors.append((
                    relative_path,
                    "Registry entry without disk file"
                ))
    
    return errors


def check_no_orphaned_dir_ids(project_root: Path) -> List[Tuple[str, str]]:
    """Check for orphaned .dir_id files."""
    errors = []
    zone_classifier = ZoneClassifier(project_root=project_root)
    
    for dir_id_path in project_root.rglob(".dir_id"):
        parent_dir = dir_id_path.parent
        zone = zone_classifier.compute_zone(parent_dir)
        
        if zone == 'excluded':
            errors.append((
                str(parent_dir.relative_to(project_root)),
                "Orphaned .dir_id in excluded zone"
            ))
    
    return errors


def main() -> int:
    """Main pre-push hook."""
    project_root = _detect_project_root()
    
    errors = []
    
    # Run checks
    print("Running pre-push governance checks...")
    
    print("  • Checking governed directories have .dir_id...")
    errors.extend(check_all_governed_directories_have_dir_id(project_root))
    
    print("  • Checking registry sync with filesystem...")
    errors.extend(check_registry_in_sync_with_filesystem(project_root))
    
    print("  • Checking for orphaned .dir_id files...")
    errors.extend(check_no_orphaned_dir_ids(project_root))
    
    if errors:
        print("\n❌ Pre-push hook failed: Governance violations detected\n")
        for file_path, error_msg in errors[:20]:  # Show first 20 errors
            print(f"  • {file_path}: {error_msg}")
        if len(errors) > 20:
            print(f"\n  ... and {len(errors) - 20} more errors")
        print("\nPlease fix these issues before pushing.")
        return 1
    
    print("✅ Pre-push hook passed: All governance checks successful")
    return 0


if __name__ == "__main__":
    sys.exit(main())
