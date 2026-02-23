"""Unified ingest engine - directory and file metadata to registry.

FILE_ID: 01260207233100000073
PURPOSE: Ingest directory identity metadata into governance registry
PHASE: PH-04 Registry Integration
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone
import json
import sys

repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from govreg_core.P_01260207233100000068_zone_classifier import ZoneClassifier
from govreg_core.P_01260207233100000069_dir_id_handler import DirIdManager
from govreg_core.P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver


class UnifiedIngestEngine:
    """Ingests directory and file metadata into governance registry.
    
    Handles:
    - Directory identity resolution
    - File identity association  
    - Parent/owner relationships
    - Zone classification
    - Registry record creation
    """
    
    def __init__(
        self,
        project_root: Path,
        project_root_id: str,
        registry_path: Path,
        zone_classifier: ZoneClassifier | None = None,
        resolver: DirectoryIdentityResolver | None = None
    ):
        """Initialize ingest engine.
        
        Args:
            project_root: Project root directory
            project_root_id: Project root ID
            registry_path: Path to governance registry JSON
            zone_classifier: Optional zone classifier
            resolver: Optional identity resolver
        """
        self.project_root = project_root
        self.project_root_id = project_root_id
        self.registry_path = registry_path
        self.zone_classifier = zone_classifier or ZoneClassifier()
        self.resolver = resolver or DirectoryIdentityResolver(
            project_root=project_root,
            project_root_id=project_root_id,
            zone_classifier=self.zone_classifier
        )
        
        # Load existing registry
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load governance registry from disk."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {"entities": [], "metadata": {"version": "4.0.0"}}
    
    def _save_registry(self) -> None:
        """Save governance registry to disk."""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2)
    
    def ingest_directory(self, directory: Path, allocate_if_missing: bool = True) -> Dict[str, Any]:
        """Ingest directory metadata into registry.
        
        Args:
            directory: Directory to ingest
            allocate_if_missing: Allocate dir_id if missing
            
        Returns:
            Registry record for directory
        """
        # Resolve identity
        result = self.resolver.resolve_identity(directory, allocate_if_missing)
        
        # Compute relative path
        relative_path = str(directory.relative_to(self.project_root)).replace("\\", "/")
        
        # Create registry record
        record = {
            "entity_kind": "directory",
            "relative_path": relative_path,
            "dir_id": result.dir_id,
            "parent_dir_id": None,  # Will be resolved
            "depth": result.depth,
            "zone": result.zone,
            "dir_id_allocated_at": None,
            "dir_id_allocator_version": None,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "status": result.status
        }
        
        # Extract metadata from anchor if available
        if result.anchor:
            record["dir_id_allocated_at"] = result.anchor.allocated_at_utc
            record["dir_id_allocator_version"] = result.anchor.allocator_version
            record["parent_dir_id"] = result.anchor.parent_dir_id
        else:
            # Derive parent_dir_id
            record["parent_dir_id"] = self.resolver._find_parent_dir_id(directory)
        
        return record
    
    def ingest_file(self, file_path: Path, file_id: str) -> Dict[str, Any]:
        """Ingest file metadata into registry.
        
        Args:
            file_path: File to ingest
            file_id: Allocated file_id
            
        Returns:
            Registry record for file
        """
        # Compute relative path
        relative_path = str(file_path.relative_to(self.project_root)).replace("\\", "/")
        
        # Determine owning directory
        owning_dir = file_path.parent
        
        # Resolve owning directory's dir_id
        dir_result = self.resolver.resolve_identity(owning_dir, allocate_if_missing=False)
        
        # Compute zone and depth
        depth = self.zone_classifier.compute_depth(relative_path)
        zone = self.zone_classifier.compute_zone(relative_path, depth)
        
        # Create registry record
        record = {
            "entity_kind": "file",
            "relative_path": relative_path,
            "file_id": file_id,
            "owning_dir_id": dir_result.dir_id if dir_result.dir_id else None,
            "depth": depth,
            "zone": zone,
            "ingested_at": datetime.now(timezone.utc).isoformat()
        }
        
        return record
    
    def bulk_ingest_directories(
        self,
        directories: List[Path],
        allocate_if_missing: bool = True
    ) -> List[Dict[str, Any]]:
        """Bulk ingest multiple directories.
        
        Args:
            directories: List of directories to ingest
            allocate_if_missing: Allocate dir_id if missing
            
        Returns:
            List of registry records
        """
        records = []
        for directory in directories:
            try:
                record = self.ingest_directory(directory, allocate_if_missing)
                records.append(record)
            except Exception as e:
                print(f"Warning: Failed to ingest {directory}: {e}")
        
        return records
    
    def update_registry(self, records: List[Dict[str, Any]]) -> None:
        """Update governance registry with new records.
        
        Args:
            records: List of records to add/update
        """
        if "entities" not in self.registry:
            self.registry["entities"] = []
        
        # Add records (simple append for now, could implement upsert)
        for record in records:
            # Check if record already exists
            existing_idx = self._find_existing_record(record)
            if existing_idx is not None:
                # Update existing
                self.registry["entities"][existing_idx] = record
            else:
                # Add new
                self.registry["entities"].append(record)
        
        # Update metadata
        self.registry["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.registry["metadata"]["total_entities"] = len(self.registry["entities"])
        
        # Save
        self._save_registry()
    
    def _find_existing_record(self, record: Dict[str, Any]) -> int | None:
        """Find existing record by relative_path.
        
        Args:
            record: Record to search for
            
        Returns:
            Index of existing record, or None
        """
        relative_path = record.get("relative_path")
        if not relative_path:
            return None
        
        for idx, entity in enumerate(self.registry.get("entities", [])):
            if entity.get("relative_path") == relative_path:
                return idx
        
        return None
    
    def ingest_tree(
        self,
        root_directory: Path,
        allocate_directories: bool = True,
        include_files: bool = False
    ) -> Dict[str, Any]:
        """Recursively ingest directory tree.
        
        Args:
            root_directory: Root directory to ingest from
            allocate_directories: Allocate dir_id for directories
            include_files: Also ingest files
            
        Returns:
            Summary of ingestion operation
        """
        directories_ingested = []
        files_ingested = []
        errors = []
        
        # Walk directory tree
        for entry in root_directory.rglob("*"):
            if entry.is_dir():
                # Ingest directory
                try:
                    record = self.ingest_directory(entry, allocate_directories)
                    directories_ingested.append(record)
                except Exception as e:
                    errors.append({"path": str(entry), "error": str(e)})
            elif include_files and entry.is_file():
                # Skip ingest for now (requires file_id allocation)
                pass
        
        # Update registry
        if directories_ingested:
            self.update_registry(directories_ingested)
        
        return {
            "directories_ingested": len(directories_ingested),
            "files_ingested": len(files_ingested),
            "errors": len(errors),
            "error_details": errors[:10]  # First 10 errors
        }


if __name__ == "__main__":
    import tempfile
    
    # Quick test
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_dir = project_root / "src" / "module"
        test_dir.mkdir(parents=True)
        
        registry_path = project_root / "registry.json"
        
        engine = UnifiedIngestEngine(
            project_root=project_root,
            project_root_id="01999000042260124068",
            registry_path=registry_path
        )
        
        # Ingest directory
        record = engine.ingest_directory(test_dir)
        print(f"Ingested: {record['relative_path']}")
        print(f"  dir_id: {record['dir_id']}")
        print(f"  zone: {record['zone']}")
        print(f"  depth: {record['depth']}")
        
        # Update registry
        engine.update_registry([record])
        print(f"✅ Registry updated: {registry_path}")
