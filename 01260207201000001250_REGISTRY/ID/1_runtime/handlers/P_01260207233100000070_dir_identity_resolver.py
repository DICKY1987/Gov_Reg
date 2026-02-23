"""Directory identity resolution pipeline (S10D-S12D).

FILE_ID: 01260207233100000070
PURPOSE: Resolve directory identity - detect, validate, allocate .dir_id
PHASE: PH-03A Core Pipeline
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent))
from P_01260207233100000068_zone_classifier import ZoneClassifier, compute_depth, compute_zone
from P_01260207233100000069_dir_id_handler import DirIdManager, DirIdAnchor, create_anchor
from P_01999000042260125006_id_allocator_facade import allocate_dir_id


@dataclass
class IdentityResolutionResult:
    """Result of directory identity resolution."""
    dir_id: str | None
    status: str  # "exists", "allocated", "error", "skipped"
    anchor: DirIdAnchor | None
    zone: str
    depth: int
    needs_allocation: bool
    error_message: str | None = None


class DirectoryIdentityResolver:
    """Resolves directory identity following S10D-S12D pipeline.
    
    Pipeline:
        S10D: Detect .dir_id anchor file
        S11D: Validate anchor format and content
        S12D: Allocate new dir_id if needed (governed zone only)
    """
    
    def __init__(
        self,
        project_root: Path,
        project_root_id: str,
        zone_classifier: ZoneClassifier | None = None,
        dir_id_manager: DirIdManager | None = None
    ):
        """Initialize resolver.
        
        Args:
            project_root: Path to project root directory
            project_root_id: Allocated ID for project root
            zone_classifier: Optional zone classifier (creates default if None)
            dir_id_manager: Optional dir_id manager (creates default if None)
        """
        self.project_root = project_root
        self.project_root_id = project_root_id
        self.zone_classifier = zone_classifier or ZoneClassifier()
        self.dir_id_manager = dir_id_manager or DirIdManager()
    
    def resolve_identity(
        self,
        directory: Path,
        allocate_if_missing: bool = False
    ) -> IdentityResolutionResult:
        """Resolve directory identity through S10D-S12D pipeline.
        
        Args:
            directory: Directory to resolve
            allocate_if_missing: If True, allocate dir_id for governed directories
            
        Returns:
            IdentityResolutionResult: Resolution outcome
        """
        # Compute relative path
        try:
            relative_path = str(directory.relative_to(self.project_root))
            # Normalize to forward slashes
            relative_path = relative_path.replace("\\", "/")
        except ValueError:
            return IdentityResolutionResult(
                dir_id=None,
                status="error",
                anchor=None,
                zone="unknown",
                depth=-1,
                needs_allocation=False,
                error_message=f"Directory {directory} not under project root {self.project_root}"
            )
        
        # Compute zone and depth
        depth = self.zone_classifier.compute_depth(relative_path)
        zone = self.zone_classifier.compute_zone(relative_path, depth)
        
        # S10D: Detect anchor
        try:
            anchor = self.dir_id_manager.read_dir_id(directory)
        except ValueError as e:
            # Invalid .dir_id format (parse error)
            return IdentityResolutionResult(
                dir_id=None,
                status="error",
                anchor=None,
                zone=zone,
                depth=depth,
                needs_allocation=True,
                error_message=f"DIR-IDENTITY-005: {str(e)}"
            )
        
        if anchor is not None:
            # S11D: Validate anchor
            is_valid, errors = self.dir_id_manager.validate_dir_id(anchor)
            
            if is_valid:
                return IdentityResolutionResult(
                    dir_id=anchor.dir_id,
                    status="exists",
                    anchor=anchor,
                    zone=zone,
                    depth=depth,
                    needs_allocation=False
                )
            else:
                return IdentityResolutionResult(
                    dir_id=None,
                    status="error",
                    anchor=anchor,
                    zone=zone,
                    depth=depth,
                    needs_allocation=True,
                    error_message=f"Invalid .dir_id: {'; '.join(errors)}"
                )
        
        # No anchor exists
        # Check if we should allocate (governed zone + allocate_if_missing)
        if zone == "governed" and allocate_if_missing:
            # S12D: Allocate new dir_id
            try:
                dir_id, metadata = allocate_dir_id(
                    relative_path=relative_path,
                    context=f"resolve:{relative_path}"
                )
                
                # Find parent_dir_id by walking up
                parent_dir_id = self._find_parent_dir_id(directory)
                
                # Create anchor
                new_anchor = create_anchor(
                    dir_id=dir_id,
                    project_root_id=self.project_root_id,
                    relative_path=relative_path,
                    depth=depth,
                    zone=zone,
                    parent_dir_id=parent_dir_id,
                    created_by="resolver"
                )
                
                # Write anchor
                self.dir_id_manager.write_dir_id(directory, new_anchor)
                
                return IdentityResolutionResult(
                    dir_id=dir_id,
                    status="allocated",
                    anchor=new_anchor,
                    zone=zone,
                    depth=depth,
                    needs_allocation=False
                )
            except Exception as e:
                return IdentityResolutionResult(
                    dir_id=None,
                    status="error",
                    anchor=None,
                    zone=zone,
                    depth=depth,
                    needs_allocation=True,
                    error_message=f"Allocation failed: {e}"
                )
        
        # Not governed or not allocating
        return IdentityResolutionResult(
            dir_id=None,
            status="skipped" if zone != "governed" else "missing",
            anchor=None,
            zone=zone,
            depth=depth,
            needs_allocation=(zone == "governed")
        )
    
    def _find_parent_dir_id(self, directory: Path) -> str | None:
        """Find parent directory's dir_id by walking up tree.
        
        Args:
            directory: Directory whose parent to find
            
        Returns:
            Parent's dir_id or None if no parent with .dir_id exists
        """
        parent = directory.parent
        
        # Walk up until we find a .dir_id or reach project root
        while parent != self.project_root and parent != parent.parent:
            anchor = self.dir_id_manager.read_dir_id(parent)
            if anchor:
                return anchor.dir_id
            parent = parent.parent
        
        # Check project root itself
        if parent == self.project_root:
            anchor = self.dir_id_manager.read_dir_id(parent)
            if anchor:
                return anchor.dir_id
        
        return None
    
    def allocate_new_id(self, directory: Path) -> IdentityResolutionResult:
        """Allocate new dir_id for directory (convenience method).
        
        Args:
            directory: Directory to allocate for
            
        Returns:
            IdentityResolutionResult: Allocation outcome
        """
        return self.resolve_identity(directory, allocate_if_missing=True)


if __name__ == "__main__":
    # Quick test
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create test directory structure
        test_dir = project_root / "src" / "module_a"
        test_dir.mkdir(parents=True)
        
        # Resolve identity (with allocation)
        resolver = DirectoryIdentityResolver(
            project_root=project_root,
            project_root_id="01999000042260124068"
        )
        
        result = resolver.resolve_identity(test_dir, allocate_if_missing=True)
        
        print(f"Status: {result.status}")
        print(f"Zone: {result.zone}")
        print(f"Depth: {result.depth}")
        if result.dir_id:
            print(f"Allocated dir_id: {result.dir_id}")
            print("✓ Allocation successful")
        else:
            print(f"Error: {result.error_message}")
