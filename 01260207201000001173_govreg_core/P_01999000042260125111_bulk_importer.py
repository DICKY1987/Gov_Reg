"""Bulk directory import with .dir_id allocation (GAP-008).

FILE_ID: 01999000042260125111
PURPOSE: Bulk import of existing directory trees into ID system
PHASE: Phase 8 - Bulk Operations
BACKLOG: 01999000042260125103 GAP-008

Imports existing directory structures en masse:
- Scans directory tree
- Allocates .dir_id for all directories
- Registers all files in registry
- Generates comprehensive import report
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

sys.path.insert(0, str(Path(__file__).parent))
from P_01260207233100000068_zone_classifier import ZoneClassifier
from P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver


@dataclass
class ImportedDirectory:
    """Record of an imported directory."""
    path: str
    dir_id: str
    file_count: int
    subdirectory_count: int
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ImportedFile:
    """Record of an imported file."""
    path: str
    file_id: Optional[str]
    size_bytes: int
    parent_dir_id: str
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class BulkImportResult:
    """Result of bulk directory import."""
    timestamp: str
    root_path: str
    directories_imported: int
    files_imported: int
    errors: List[str] = field(default_factory=list)
    directories: List[ImportedDirectory] = field(default_factory=list)
    files: List[ImportedFile] = field(default_factory=list)
    duration_seconds: float = 0.0
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['directories'] = [d.to_dict() if hasattr(d, 'to_dict') else d for d in self.directories]
        result['files'] = [f.to_dict() if hasattr(f, 'to_dict') else f for f in self.files]
        return result


class BulkDirectoryImporter:
    """Bulk imports directory trees into ID system.
    
    Scans entire directory structures and:
    1. Allocates .dir_id for all directories
    2. Extracts file_id from filenames
    3. Generates import report
    4. Optionally registers in registry
    """
    
    def __init__(
        self,
        project_root: Path,
        project_root_id: str,
        zone_classifier: Optional[ZoneClassifier] = None,
        evidence_dir: Optional[Path] = None
    ):
        """Initialize bulk importer.
        
        Args:
            project_root: Project root directory
            project_root_id: Project root dir_id
            zone_classifier: Zone classifier (creates if None)
            evidence_dir: Directory for evidence artifacts
        """
        self.project_root = project_root
        self.project_root_id = project_root_id
        
        if zone_classifier is None:
            zone_classifier = ZoneClassifier()
        self.zone_classifier = zone_classifier
        
        self.resolver = DirectoryIdentityResolver(project_root, project_root_id, zone_classifier)
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "bulk_import"
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def import_directory_tree(
        self,
        root_path: Path,
        allocate_dir_ids: bool = True,
        register_files: bool = False,
        skip_zones: Optional[List[str]] = None
    ) -> BulkImportResult:
        """Import an entire directory tree.
        
        Args:
            root_path: Root of tree to import
            allocate_dir_ids: If True, allocate .dir_id for directories
            register_files: If True, register files in registry
            skip_zones: Zones to skip (default: ['excluded', 'staging'])
            
        Returns:
            BulkImportResult: Comprehensive import report
        """
        start_time = datetime.now(timezone.utc)
        
        if skip_zones is None:
            skip_zones = ['excluded', 'staging']
        
        directories: List[ImportedDirectory] = []
        files: List[ImportedFile] = []
        errors: List[str] = []
        
        # Walk directory tree
        try:
            for dirpath in root_path.rglob('*'):
                if not dirpath.is_dir():
                    continue
                
                # Check zone
                zone = self.zone_classifier.compute_zone(dirpath)
                if zone in skip_zones:
                    continue
                
                # Import directory
                try:
                    imported_dir = self._import_directory(
                        dirpath,
                        allocate_dir_ids
                    )
                    directories.append(imported_dir)
                    
                    # Import files in directory
                    for file_path in dirpath.glob('*'):
                        if file_path.is_file() and not file_path.name.startswith('.'):
                            try:
                                imported_file = self._import_file(
                                    file_path,
                                    imported_dir.dir_id
                                )
                                files.append(imported_file)
                            except Exception as e:
                                errors.append(f"Error importing file {file_path}: {e}")
                    
                except Exception as e:
                    errors.append(f"Error importing directory {dirpath}: {e}")
        
        except Exception as e:
            errors.append(f"Error walking tree: {e}")
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        result = BulkImportResult(
            timestamp=start_time.isoformat(),
            root_path=str(root_path),
            directories_imported=len(directories),
            files_imported=len(files),
            errors=errors,
            directories=directories,
            files=files,
            duration_seconds=duration
        )
        
        # Save evidence
        self._save_evidence(result, start_time.strftime("%Y%m%d_%H%M%S"))
        
        return result
    
    def _import_directory(
        self,
        dir_path: Path,
        allocate_dir_id: bool
    ) -> ImportedDirectory:
        """Import a single directory."""
        # Count contents
        file_count = sum(1 for f in dir_path.glob('*') if f.is_file() and not f.name.startswith('.'))
        subdirectory_count = sum(1 for d in dir_path.glob('*') if d.is_dir())
        
        # Get or allocate dir_id
        if allocate_dir_id:
            result = self.resolver.resolve_identity(dir_path, allocate_if_missing=True)
            dir_id = result.dir_id or "UNKNOWN"
        else:
            # Try to read existing .dir_id
            dir_id_file = dir_path / '.dir_id'
            if dir_id_file.exists():
                try:
                    with open(dir_id_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    dir_id = data.get('dir_id', 'UNKNOWN')
                except Exception:
                    dir_id = "UNKNOWN"
            else:
                dir_id = "NOT_ALLOCATED"
        
        relative_path = str(dir_path.relative_to(self.project_root))
        
        return ImportedDirectory(
            path=relative_path,
            dir_id=dir_id,
            file_count=file_count,
            subdirectory_count=subdirectory_count
        )
    
    def _import_file(
        self,
        file_path: Path,
        parent_dir_id: str
    ) -> ImportedFile:
        """Import a single file."""
        # Extract file_id from filename if present
        file_id = None
        name = file_path.name
        if '_' in name:
            prefix = name.split('_')[0]
            if prefix.replace('P_', '').isdigit() and len(prefix.replace('P_', '')) == 20:
                file_id = prefix.replace('P_', '')
        
        relative_path = str(file_path.relative_to(self.project_root))
        
        return ImportedFile(
            path=relative_path,
            file_id=file_id,
            size_bytes=file_path.stat().st_size,
            parent_dir_id=parent_dir_id
        )
    
    def _save_evidence(self, result: BulkImportResult, timestamp: str):
        """Save import evidence."""
        evidence_file = self.evidence_dir / f"bulk_import_{timestamp}.json"
        
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2)


def bulk_import_directories(
    project_root: Path,
    target_path: Path,
    project_root_id: str,
    allocate_dir_ids: bool = True,
    register_files: bool = False
) -> BulkImportResult:
    """Bulk import directory tree (public API).
    
    Args:
        project_root: Project root directory
        target_path: Path to import (relative to project root or absolute)
        project_root_id: Project root dir_id
        allocate_dir_ids: If True, allocate .dir_id for directories
        register_files: If True, register files in registry
        
    Returns:
        BulkImportResult: Comprehensive import report
    """
    # Resolve target path
    if not target_path.is_absolute():
        target_path = project_root / target_path
    
    importer = BulkDirectoryImporter(project_root, project_root_id)
    return importer.import_directory_tree(
        target_path,
        allocate_dir_ids,
        register_files
    )


if __name__ == "__main__":
    # CLI entry point
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk import directory tree into ID system")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--target", type=Path, required=True, help="Path to import")
    parser.add_argument("--root-id", required=True, help="Project root dir_id")
    parser.add_argument("--allocate", action="store_true", help="Allocate .dir_id for directories")
    parser.add_argument("--register", action="store_true", help="Register files in registry")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    
    args = parser.parse_args()
    
    result = bulk_import_directories(
        args.project_root,
        args.target,
        args.root_id,
        args.allocate,
        args.register
    )
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Bulk Import Complete:")
        print(f"  Directories imported: {result.directories_imported}")
        print(f"  Files imported: {result.files_imported}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
        if result.errors:
            print("\nErrors:")
            for error in result.errors[:10]:
                print(f"  - {error}")
