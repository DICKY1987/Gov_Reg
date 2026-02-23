"""Directory governance gates for pre-commit enforcement.

FILE_ID: 01260207233100000075
PURPOSE: Pre-commit gates for directory ID governance
PHASE: PH-06 Enforcement
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Tuple
import sys
import json

repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from govreg_core.P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver
from govreg_core.P_01260207233100000069_dir_id_handler import DirIdManager


class DirectoryGateViolation:
    """Represents a directory governance gate violation."""
    
    def __init__(
        self,
        gate_id: str,
        severity: str,
        path: str,
        message: str,
        remediation: str
    ):
        self.gate_id = gate_id
        self.severity = severity
        self.path = path
        self.message = message
        self.remediation = remediation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
            "remediation": self.remediation
        }


class DirectoryGovernanceGates:
    """Enforcement gates for directory ID governance.
    
    Gates:
    - GATE-DIR-001: All governed directories must have .dir_id
    - GATE-DIR-002: .dir_id format must be valid
    - GATE-DIR-003: dir_id must be unique across project
    - GATE-DIR-004: Parent dir_id must exist for non-root directories
    """
    
    def __init__(
        self,
        project_root: Path,
        project_root_id: str,
        resolver: DirectoryIdentityResolver | None = None,
        dir_id_manager: DirIdManager | None = None
    ):
        """Initialize directory gates.
        
        Args:
            project_root: Project root directory
            project_root_id: Project root ID
            resolver: Optional identity resolver
            dir_id_manager: Optional dir_id manager
        """
        self.project_root = project_root
        self.project_root_id = project_root_id
        self.resolver = resolver or DirectoryIdentityResolver(
            project_root=project_root,
            project_root_id=project_root_id
        )
        self.dir_id_manager = dir_id_manager or DirIdManager()
        
        # Track allocated dir_ids for uniqueness check
        self.dir_id_index: Dict[str, Path] = {}
    
    def check_gate_dir_001(self, directory: Path) -> List[DirectoryGateViolation]:
        """GATE-DIR-001: All governed directories must have .dir_id.
        
        Args:
            directory: Directory to check
            
        Returns:
            List of violations (empty if passing)
        """
        violations = []
        
        # Resolve identity
        result = self.resolver.resolve_identity(directory, allocate_if_missing=False)
        
        # Check if governed zone and missing .dir_id
        if result.zone == "governed" and result.status == "missing":
            violations.append(DirectoryGateViolation(
                gate_id="GATE-DIR-001",
                severity="ERROR",
                path=str(directory),
                message=f"Governed directory missing .dir_id file",
                remediation="Run scanner with --fix to allocate dir_id"
            ))
        
        return violations
    
    def check_gate_dir_002(self, directory: Path) -> List[DirectoryGateViolation]:
        """GATE-DIR-002: .dir_id format must be valid.
        
        Args:
            directory: Directory to check
            
        Returns:
            List of violations (empty if passing)
        """
        violations = []
        
        # Read .dir_id
        try:
            anchor = self.dir_id_manager.read_dir_id(directory)
            
            if anchor:
                # Validate format
                is_valid, errors = self.dir_id_manager.validate_dir_id(anchor)
                
                if not is_valid:
                    violations.append(DirectoryGateViolation(
                        gate_id="GATE-DIR-002",
                        severity="ERROR",
                        path=str(directory),
                        message=f"Invalid .dir_id format: {'; '.join(errors)}",
                        remediation="Delete .dir_id and run scanner with --fix"
                    ))
        except ValueError as e:
            # Parse error
            violations.append(DirectoryGateViolation(
                gate_id="GATE-DIR-002",
                severity="ERROR",
                path=str(directory),
                message=f"Invalid .dir_id file: {e}",
                remediation="Delete .dir_id and run scanner with --fix"
            ))
        
        return violations
    
    def check_gate_dir_003(self, directory: Path) -> List[DirectoryGateViolation]:
        """GATE-DIR-003: dir_id must be unique across project.
        
        Args:
            directory: Directory to check
            
        Returns:
            List of violations (empty if passing)
        """
        violations = []
        
        # Read .dir_id
        anchor = self.dir_id_manager.read_dir_id(directory)
        
        if anchor:
            dir_id = anchor.dir_id
            
            # Check if already seen
            if dir_id in self.dir_id_index:
                existing_path = self.dir_id_index[dir_id]
                violations.append(DirectoryGateViolation(
                    gate_id="GATE-DIR-003",
                    severity="CRITICAL",
                    path=str(directory),
                    message=f"Duplicate dir_id {dir_id} found at {existing_path}",
                    remediation="Resolve conflict manually or delete one .dir_id and re-allocate"
                ))
            else:
                # Register dir_id
                self.dir_id_index[dir_id] = directory
        
        return violations
    
    def check_gate_dir_004(self, directory: Path) -> List[DirectoryGateViolation]:
        """GATE-DIR-004: Parent dir_id must exist for non-root directories.
        
        Args:
            directory: Directory to check
            
        Returns:
            List of violations (empty if passing)
        """
        violations = []
        
        # Skip root directory
        if directory == self.project_root:
            return violations
        
        # Read .dir_id
        anchor = self.dir_id_manager.read_dir_id(directory)
        
        if anchor and anchor.parent_dir_id:
            # Find parent directory
            parent_dir = directory.parent
            parent_anchor = self.dir_id_manager.read_dir_id(parent_dir)
            
            if not parent_anchor:
                violations.append(DirectoryGateViolation(
                    gate_id="GATE-DIR-004",
                    severity="WARNING",
                    path=str(directory),
                    message=f"Parent directory {parent_dir} missing .dir_id (expected {anchor.parent_dir_id})",
                    remediation="Run scanner with --fix on parent directory"
                ))
            elif parent_anchor.dir_id != anchor.parent_dir_id:
                violations.append(DirectoryGateViolation(
                    gate_id="GATE-DIR-004",
                    severity="ERROR",
                    path=str(directory),
                    message=f"Parent dir_id mismatch: expected {anchor.parent_dir_id}, found {parent_anchor.dir_id}",
                    remediation="Delete .dir_id and re-allocate to fix parent relationship"
                ))
        
        return violations
    
    def check_all_gates(self, directory: Path) -> List[DirectoryGateViolation]:
        """Run all gates on directory.
        
        Args:
            directory: Directory to check
            
        Returns:
            List of all violations
        """
        violations = []
        
        violations.extend(self.check_gate_dir_001(directory))
        violations.extend(self.check_gate_dir_002(directory))
        violations.extend(self.check_gate_dir_003(directory))
        violations.extend(self.check_gate_dir_004(directory))
        
        return violations
    
    def check_tree(self, root_directory: Path) -> Tuple[List[DirectoryGateViolation], int]:
        """Check all directories in tree.
        
        Args:
            root_directory: Root directory to check from
            
        Returns:
            Tuple of (violations, directories_checked)
        """
        all_violations = []
        directories_checked = 0
        
        # Walk tree
        for entry in root_directory.rglob("*"):
            if entry.is_dir():
                violations = self.check_all_gates(entry)
                all_violations.extend(violations)
                directories_checked += 1
        
        return all_violations, directories_checked
    
    def run_as_pre_commit_hook(self) -> int:
        """Run gates as pre-commit hook.
        
        Returns:
            Exit code (0 = pass, 1 = violations found)
        """
        print("🔒 Running directory governance gates...")
        
        violations, checked = self.check_tree(self.project_root)
        
        print(f"  Checked: {checked} directories")
        print(f"  Violations: {len(violations)}")
        
        if violations:
            print("\n⛔ GATE VIOLATIONS DETECTED:")
            for v in violations:
                print(f"\n  [{v.severity}] {v.gate_id}")
                print(f"    Path: {v.path}")
                print(f"    {v.message}")
                print(f"    Remediation: {v.remediation}")
            
            print("\n❌ Pre-commit check FAILED")
            return 1
        else:
            print("✅ All gates passed")
            return 0


if __name__ == "__main__":
    import tempfile
    
    # Quick test
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_dir = project_root / "src" / "module"
        test_dir.mkdir(parents=True)
        
        gates = DirectoryGovernanceGates(
            project_root=project_root,
            project_root_id="01999000042260124068"
        )
        
        # Check gates (should find missing .dir_id)
        violations = gates.check_all_gates(test_dir)
        
        print(f"Violations found: {len(violations)}")
        for v in violations:
            print(f"  {v.gate_id}: {v.message}")
