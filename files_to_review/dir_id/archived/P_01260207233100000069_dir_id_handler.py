""".dir_id file handler for directory identity anchoring.

FILE_ID: 01260207233100000069
PURPOSE: Read/write/validate .dir_id anchor files
PHASE: PH-03A Core Pipeline
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class DirIdAnchor:
    """Data structure for .dir_id anchor file."""
    dir_id: str
    allocator_version: str
    allocated_at_utc: str
    project_root_id: str
    relative_path: str
    depth: int | None = None
    zone: str | None = None
    parent_dir_id: str | None = None
    created_by: str | None = None
    canonicality_law_version: str = "1.0.0"
    metadata: Dict[str, Any] | None = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DirIdAnchor:
        """Create from dictionary."""
        return cls(**data)


class DirIdManager:
    """Manager for .dir_id file operations."""
    
    DIR_ID_FILENAME = ".dir_id"
    
    def __init__(self, schema_path: Path | None = None):
        """Initialize manager.
        
        Args:
            schema_path: Optional path to DIR_ID_ANCHOR schema
        """
        self.schema_path = schema_path
    
    def read_dir_id(self, directory: Path) -> DirIdAnchor | None:
        """Read .dir_id file from directory.
        
        Args:
            directory: Directory containing .dir_id
            
        Returns:
            DirIdAnchor if file exists and valid, None otherwise
            
        Raises:
            ValueError: If .dir_id exists but is invalid (parse error)
        """
        dir_id_path = directory / self.DIR_ID_FILENAME
        
        if not dir_id_path.exists():
            return None
        
        try:
            with open(dir_id_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DirIdAnchor.from_dict(data)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            # Invalid format - raise to signal corruption
            raise ValueError(f"Invalid .dir_id format: {e}")
    
    def write_dir_id(self, directory: Path, anchor: DirIdAnchor) -> Path:
        """Write .dir_id file to directory atomically.
        
        Args:
            directory: Directory to write .dir_id to
            anchor: Anchor data to write
            
        Returns:
            Path: Path to written .dir_id file
            
        Raises:
            OSError: If write fails
        """
        dir_id_path = directory / self.DIR_ID_FILENAME
        
        # Write to temp file first (atomic)
        temp_path = dir_id_path.with_suffix(".dir_id.tmp")
        
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(anchor.to_dict(), f, indent=2)
            
            # Atomic rename
            temp_path.replace(dir_id_path)
            
            return dir_id_path
        except Exception as e:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to write .dir_id: {e}")
    
    def validate_dir_id(self, anchor: DirIdAnchor) -> tuple[bool, list[str]]:
        """Validate .dir_id anchor data.
        
        Args:
            anchor: Anchor to validate
            
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        if not anchor.dir_id:
            errors.append("dir_id is required")
        elif not anchor.dir_id.isdigit():
            errors.append("dir_id must be numeric")
        elif len(anchor.dir_id) != 20:
            errors.append(f"dir_id must be exactly 20 digits, got {len(anchor.dir_id)}")
        
        if not anchor.allocator_version:
            errors.append("allocator_version is required")
        
        if not anchor.allocated_at_utc:
            errors.append("allocated_at_utc is required")
        else:
            # Try to parse timestamp
            try:
                datetime.fromisoformat(anchor.allocated_at_utc.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"allocated_at_utc is not valid ISO 8601: {anchor.allocated_at_utc}")
        
        if not anchor.project_root_id:
            errors.append("project_root_id is required")
        elif not anchor.project_root_id.isdigit():
            errors.append("project_root_id must be numeric")
        
        if not anchor.relative_path:
            errors.append("relative_path is required")
        
        # Check optional fields
        if anchor.zone and anchor.zone not in ["staging", "governed", "excluded"]:
            errors.append(f"zone must be staging/governed/excluded, got {anchor.zone}")
        
        if anchor.depth is not None and anchor.depth < 0:
            errors.append(f"depth must be non-negative, got {anchor.depth}")
        
        if anchor.parent_dir_id and not anchor.parent_dir_id.isdigit():
            errors.append("parent_dir_id must be numeric if provided")
        
        return len(errors) == 0, errors
    
    def exists(self, directory: Path) -> bool:
        """Check if .dir_id exists in directory.
        
        Args:
            directory: Directory to check
            
        Returns:
            bool: True if .dir_id exists
        """
        return (directory / self.DIR_ID_FILENAME).exists()
    
    def delete_dir_id(self, directory: Path) -> bool:
        """Delete .dir_id file (use with caution).
        
        Args:
            directory: Directory containing .dir_id
            
        Returns:
            bool: True if deleted, False if didn't exist
        """
        dir_id_path = directory / self.DIR_ID_FILENAME
        if dir_id_path.exists():
            dir_id_path.unlink()
            return True
        return False
    
    def archive_dir_id(self, directory: Path, archive_dir: Path) -> Path | None:
        """Archive .dir_id file (for deletion/migration).
        
        Args:
            directory: Directory containing .dir_id
            archive_dir: Directory to archive to
            
        Returns:
            Path: Archived file path, or None if no .dir_id existed
        """
        dir_id_path = directory / self.DIR_ID_FILENAME
        if not dir_id_path.exists():
            return None
        
        # Read anchor to get dir_id for archive naming
        anchor = self.read_dir_id(directory)
        if not anchor:
            # Corrupt file, archive anyway with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            archive_name = f".dir_id.corrupt.{timestamp}"
        else:
            archive_name = f".dir_id.{anchor.dir_id}"
        
        archive_path = archive_dir / archive_name
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy then delete (safer than move for cross-filesystem)
        import shutil
        shutil.copy2(dir_id_path, archive_path)
        dir_id_path.unlink()
        
        return archive_path


def create_anchor(
    dir_id: str,
    project_root_id: str,
    relative_path: str,
    depth: int,
    zone: str,
    parent_dir_id: str | None = None,
    created_by: str = "system",
    metadata: Dict[str, Any] | None = None
) -> DirIdAnchor:
    """Create a new DirIdAnchor with standard values.
    
    Args:
        dir_id: Allocated directory ID
        project_root_id: Project root ID
        relative_path: Path relative to project root
        depth: Directory depth
        zone: Governance zone
        parent_dir_id: Optional parent directory ID
        created_by: Who created this anchor
        metadata: Optional metadata
        
    Returns:
        DirIdAnchor: Populated anchor ready to write
    """
    return DirIdAnchor(
        dir_id=dir_id,
        allocator_version="1.0.0",
        allocated_at_utc=datetime.now(timezone.utc).isoformat(),
        project_root_id=project_root_id,
        relative_path=relative_path,
        depth=depth,
        zone=zone,
        parent_dir_id=parent_dir_id,
        created_by=created_by,
        canonicality_law_version="1.0.0",
        metadata=metadata
    )


if __name__ == "__main__":
    # Quick test
    import tempfile
    
    manager = DirIdManager()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test"
        test_dir.mkdir()
        
        # Create anchor
        anchor = create_anchor(
            dir_id="01999000042260124070",
            project_root_id="01999000042260124068",
            relative_path="test",
            depth=1,
            zone="governed",
            created_by="test"
        )
        
        # Validate
        is_valid, errors = manager.validate_dir_id(anchor)
        print(f"Validation: {'PASS' if is_valid else 'FAIL'}")
        if errors:
            for err in errors:
                print(f"  - {err}")
        
        # Write
        path = manager.write_dir_id(test_dir, anchor)
        print(f"Written to: {path}")
        
        # Read back
        read_anchor = manager.read_dir_id(test_dir)
        print(f"Read back: {read_anchor.dir_id if read_anchor else 'FAIL'}")
        
        # Check equality
        if read_anchor:
            assert read_anchor.dir_id == anchor.dir_id
            assert read_anchor.relative_path == anchor.relative_path
            print("✓ Round-trip successful")
