"""
Directory ID Handler - Directory ID Package v1.0

Provides .dir_id file format handling (read/write/validate).

**.dir_id Format** (JSON):
{
  "dir_id": "01999000042260124550",
  "allocator_version": "1.0.0",
  "allocated_at_utc": "2026-02-13T10:00:00Z",
  "project_root_id": "01999000042260124068",
  "relative_path": "src/module_a"
}

Author: Gov_Reg System
Created: 2026-02-13
File ID: 01999000042260125068
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import re

# Valid 20-digit ID pattern
ID_PATTERN = re.compile(r'^\d{20}$')


@dataclass
class DirIdAnchor:
    """
    Structure of a .dir_id anchor file.
    
    Fields:
        dir_id: 20-digit allocator-issued directory ID
        allocator_version: Version of allocator used (for provenance)
        allocated_at_utc: ISO-8601 timestamp of allocation
        project_root_id: 20-digit ID of project root
        relative_path: Path from project root to this directory
    """
    dir_id: str
    allocator_version: str
    allocated_at_utc: str
    project_root_id: str
    relative_path: str
    
    def __post_init__(self):
        """Validate fields after initialization."""
        if not ID_PATTERN.match(self.dir_id):
            raise ValueError(f"Invalid dir_id format: {self.dir_id} (must be 20 digits)")
        
        if not ID_PATTERN.match(self.project_root_id):
            raise ValueError(f"Invalid project_root_id format: {self.project_root_id}")
        
        # Validate ISO-8601 timestamp
        try:
            datetime.fromisoformat(self.allocated_at_utc.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValueError(f"Invalid allocated_at_utc format: {e}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "DirIdAnchor":
        """Create from dictionary."""
        required_fields = ['dir_id', 'allocator_version', 'allocated_at_utc', 'project_root_id', 'relative_path']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return cls(
            dir_id=data['dir_id'],
            allocator_version=data['allocator_version'],
            allocated_at_utc=data['allocated_at_utc'],
            project_root_id=data['project_root_id'],
            relative_path=data['relative_path']
        )


class DirIdManager:
    """
    Manager for .dir_id file operations.
    
    Responsibilities:
        - Read .dir_id files and parse to DirIdAnchor
        - Write DirIdAnchor to .dir_id files (atomic)
        - Validate .dir_id file format and content
    """
    
    DIR_ID_FILENAME = ".dir_id"
    
    def __init__(self, project_root: Path):
        """
        Initialize manager.
        
        Args:
            project_root: Absolute path to project root
        """
        self.project_root = project_root.resolve()
    
    def get_dir_id_path(self, directory: Path) -> Path:
        """
        Get path to .dir_id file for a directory.
        
        Args:
            directory: Absolute path to directory
        
        Returns:
            Absolute path to .dir_id file
        """
        return directory / self.DIR_ID_FILENAME
    
    def exists(self, directory: Path) -> bool:
        """
        Check if .dir_id file exists for directory.
        
        Args:
            directory: Absolute path to directory
        
        Returns:
            True if .dir_id exists
        """
        dir_id_path = self.get_dir_id_path(directory)
        return dir_id_path.exists() and dir_id_path.is_file()
    
    def read_dir_id(self, directory: Path) -> Optional[DirIdAnchor]:
        """
        Read and parse .dir_id file.
        
        Args:
            directory: Absolute path to directory
        
        Returns:
            DirIdAnchor if file exists and is valid, None otherwise
        
        Raises:
            ValueError: If .dir_id exists but is invalid
            OSError: If file cannot be read
        """
        dir_id_path = self.get_dir_id_path(directory)
        
        if not dir_id_path.exists():
            return None
        
        try:
            with open(dir_id_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            anchor = DirIdAnchor.from_dict(data)
            
            # Additional validation: relative_path should match actual path
            directory_resolved = directory.resolve()
            try:
                actual_relative = directory_resolved.relative_to(self.project_root)
                actual_relative_str = str(actual_relative).replace("\\", "/")
                
                if anchor.relative_path != actual_relative_str:
                    raise ValueError(
                        f"relative_path mismatch: .dir_id says '{anchor.relative_path}' "
                        f"but actual is '{actual_relative_str}'"
                    )
            except ValueError:
                # Directory not under project_root - that's a bigger problem
                raise ValueError(f"Directory {directory} is not under project root {self.project_root}")
            
            return anchor
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in .dir_id: {e}")
        except Exception as e:
            raise ValueError(f"Failed to read .dir_id: {e}")
    
    def write_dir_id(self, directory: Path, anchor: DirIdAnchor, overwrite: bool = False) -> None:
        """
        Write .dir_id file atomically.
        
        Args:
            directory: Absolute path to directory
            anchor: DirIdAnchor to write
            overwrite: If True, allow overwriting existing .dir_id
        
        Raises:
            FileExistsError: If .dir_id exists and overwrite=False
            OSError: If file cannot be written
        """
        dir_id_path = self.get_dir_id_path(directory)
        
        if dir_id_path.exists() and not overwrite:
            raise FileExistsError(f".dir_id already exists at {dir_id_path}")
        
        # Write to temp file first (atomic)
        temp_path = dir_id_path.with_suffix(".dir_id.tmp")
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(anchor.to_dict(), f, indent=2)
                f.write('\n')  # Trailing newline
            
            # Atomic rename
            temp_path.replace(dir_id_path)
        
        except Exception as e:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to write .dir_id: {e}")
    
    def validate_dir_id(self, directory: Path) -> tuple[bool, Optional[str]]:
        """
        Validate .dir_id file for directory.
        
        Args:
            directory: Absolute path to directory
        
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid
        """
        try:
            anchor = self.read_dir_id(directory)
            
            if anchor is None:
                return False, "Missing .dir_id file"
            
            # Additional checks can go here (e.g., uniqueness)
            
            return True, None
        
        except ValueError as e:
            return False, str(e)
        except OSError as e:
            return False, f"IO error: {e}"
    
    def create_anchor(
        self,
        dir_id: str,
        relative_path: str,
        project_root_id: str,
        allocator_version: str = "1.0.0"
    ) -> DirIdAnchor:
        """
        Create a new DirIdAnchor with current timestamp.
        
        Args:
            dir_id: 20-digit directory ID
            relative_path: Path from project root
            project_root_id: 20-digit project root ID
            allocator_version: Allocator version string
        
        Returns:
            DirIdAnchor instance
        """
        now_utc = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        return DirIdAnchor(
            dir_id=dir_id,
            allocator_version=allocator_version,
            allocated_at_utc=now_utc,
            project_root_id=project_root_id,
            relative_path=relative_path
        )


if __name__ == "__main__":
    # Example usage
    print("Directory ID Handler - Examples")
    print("=" * 40)
    
    # Create test anchor
    anchor = DirIdAnchor(
        dir_id="01999000042260124550",
        allocator_version="1.0.0",
        allocated_at_utc="2026-02-13T10:00:00Z",
        project_root_id="01999000042260124068",
        relative_path="src/module_a"
    )
    
    print("Anchor created:")
    print(json.dumps(anchor.to_dict(), indent=2))
    
    print("\nValidation:")
    print(f"  dir_id valid: {ID_PATTERN.match(anchor.dir_id) is not None}")
    print(f"  project_root_id valid: {ID_PATTERN.match(anchor.project_root_id) is not None}")
