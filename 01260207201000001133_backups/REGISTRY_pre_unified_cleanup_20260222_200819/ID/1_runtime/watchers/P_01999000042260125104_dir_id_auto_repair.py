"""Auto-repair invalid .dir_id anchors (GAP-001).

FILE_ID: 01999000042260125104
PURPOSE: Automatically repair invalid, malformed, or corrupted .dir_id files
PHASE: Phase 1 - Critical Infrastructure
BACKLOG: 01999000042260125103 GAP-001
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Literal
from dataclasses import dataclass, asdict
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

sys.path.insert(0, str(Path(__file__).parent))
from P_01260207233100000069_dir_id_handler import DirIdManager, DirIdAnchor, create_anchor
from P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver
from P_01999000042260125006_id_allocator_facade import allocate_dir_id


@dataclass
class RepairResult:
    """Result of a .dir_id repair operation."""
    success: bool
    action_taken: Literal['repaired', 'quarantined', 'regenerated', 'failed']
    old_content: Optional[str]
    new_content: Optional[str]
    evidence_path: Path
    error_message: Optional[str] = None
    defect_code: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['evidence_path'] = str(result['evidence_path'])
        return result


class DirIdAutoRepair:
    """Auto-repair invalid .dir_id anchors.
    
    Handles:
    - Malformed JSON (parse errors)
    - Wrong relative_path
    - Wrong project_root_id
    - Wrong digit count in dir_id
    - Unrecoverable corruption
    """
    
    def __init__(
        self,
        project_root: Path,
        project_root_id: str,
        evidence_dir: Optional[Path] = None
    ):
        """Initialize auto-repair service.
        
        Args:
            project_root: Project root directory
            project_root_id: Project root dir_id
            evidence_dir: Directory for evidence artifacts (default: .state/evidence/dir_id_repairs)
        """
        self.project_root = project_root
        self.project_root_id = project_root_id
        self.dir_id_manager = DirIdManager()
        self.resolver = DirectoryIdentityResolver(project_root, project_root_id)
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "dir_id_repairs"
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def fix_invalid_dir_id_anchors(
        self,
        directory: Path,
        validation_errors: List[str],
        quarantine: bool = True
    ) -> RepairResult:
        """Auto-repair invalid .dir_id anchor.
        
        Args:
            directory: Directory containing invalid .dir_id
            validation_errors: List of validation error messages
            quarantine: If True, quarantine unrecoverable .dir_id before regenerating
            
        Returns:
            RepairResult: Outcome of repair operation
        """
        dir_id_path = directory / ".dir_id"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # Read old content if possible
        old_content = None
        if dir_id_path.exists():
            try:
                old_content = dir_id_path.read_text(encoding='utf-8')
            except Exception:
                old_content = "<binary or unreadable>"
        
        # Determine error type from validation errors
        error_type = self._classify_error(validation_errors)
        
        try:
            if error_type == "malformed_json":
                return self._repair_malformed_json(directory, old_content, quarantine, timestamp)
            elif error_type == "wrong_relative_path":
                return self._repair_wrong_relative_path(directory, old_content, timestamp)
            elif error_type == "wrong_project_root_id":
                return self._repair_wrong_project_root_id(directory, old_content, timestamp)
            elif error_type == "wrong_digit_count":
                return self._repair_wrong_digit_count(directory, old_content, quarantine, timestamp)
            else:
                # Unrecoverable - quarantine and regenerate
                return self._quarantine_and_regenerate(directory, old_content, quarantine, timestamp)
                
        except Exception as e:
            # Repair failed
            evidence_path = self._save_evidence(
                directory,
                timestamp,
                "failed",
                old_content,
                None,
                str(e)
            )
            return RepairResult(
                success=False,
                action_taken='failed',
                old_content=old_content,
                new_content=None,
                evidence_path=evidence_path,
                error_message=str(e),
                defect_code="DIR-IDENTITY-009"
            )
    
    def _classify_error(self, validation_errors: List[str]) -> str:
        """Classify error type from validation messages."""
        errors_text = " ".join(validation_errors).lower()
        
        if "invalid .dir_id format" in errors_text or "json" in errors_text:
            return "malformed_json"
        elif "relative_path" in errors_text:
            return "wrong_relative_path"
        elif "project_root_id" in errors_text:
            return "wrong_project_root_id"
        elif "digit" in errors_text or "length" in errors_text:
            return "wrong_digit_count"
        else:
            return "unrecoverable"
    
    def _repair_malformed_json(
        self,
        directory: Path,
        old_content: Optional[str],
        quarantine: bool,
        timestamp: str
    ) -> RepairResult:
        """Repair malformed JSON in .dir_id."""
        dir_id_path = directory / ".dir_id"
        
        # Quarantine corrupt file
        if quarantine and dir_id_path.exists():
            quarantine_path = directory / f".dir_id.corrupt.{timestamp}"
            shutil.copy2(dir_id_path, quarantine_path)
        
        # Generate new valid .dir_id
        result = self.resolver.resolve_identity(directory, allocate_if_missing=True)
        
        if result.status != "allocated":
            raise ValueError(f"Failed to allocate new dir_id: {result.error_message}")
        
        # Read new content
        new_content = dir_id_path.read_text(encoding='utf-8')
        
        # Save evidence
        evidence_path = self._save_evidence(
            directory,
            timestamp,
            "regenerated",
            old_content,
            new_content,
            "Malformed JSON - quarantined and regenerated"
        )
        
        return RepairResult(
            success=True,
            action_taken='regenerated',
            old_content=old_content,
            new_content=new_content,
            evidence_path=evidence_path,
            defect_code="DIR-IDENTITY-007"
        )
    
    def _repair_wrong_relative_path(
        self,
        directory: Path,
        old_content: Optional[str],
        timestamp: str
    ) -> RepairResult:
        """Repair wrong relative_path in .dir_id."""
        dir_id_path = directory / ".dir_id"
        
        # Read current anchor
        try:
            with open(dir_id_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Cannot parse .dir_id: {e}")
        
        # Compute correct relative_path
        correct_relative_path = str(directory.relative_to(self.project_root))
        if correct_relative_path == ".":
            correct_relative_path = ""
        
        # Update relative_path
        data['relative_path'] = correct_relative_path
        
        # Write back
        with open(dir_id_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        new_content = dir_id_path.read_text(encoding='utf-8')
        
        # Save evidence
        evidence_path = self._save_evidence(
            directory,
            timestamp,
            "repaired",
            old_content,
            new_content,
            f"Fixed relative_path to: {correct_relative_path}"
        )
        
        return RepairResult(
            success=True,
            action_taken='repaired',
            old_content=old_content,
            new_content=new_content,
            evidence_path=evidence_path,
            defect_code="DIR-IDENTITY-007"
        )
    
    def _repair_wrong_project_root_id(
        self,
        directory: Path,
        old_content: Optional[str],
        timestamp: str
    ) -> RepairResult:
        """Repair wrong project_root_id in .dir_id."""
        dir_id_path = directory / ".dir_id"
        
        # Read current anchor
        try:
            with open(dir_id_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Cannot parse .dir_id: {e}")
        
        # Update project_root_id
        data['project_root_id'] = self.project_root_id
        
        # Write back
        with open(dir_id_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        new_content = dir_id_path.read_text(encoding='utf-8')
        
        # Save evidence
        evidence_path = self._save_evidence(
            directory,
            timestamp,
            "repaired",
            old_content,
            new_content,
            f"Fixed project_root_id to: {self.project_root_id}"
        )
        
        return RepairResult(
            success=True,
            action_taken='repaired',
            old_content=old_content,
            new_content=new_content,
            evidence_path=evidence_path,
            defect_code="DIR-IDENTITY-007"
        )
    
    def _repair_wrong_digit_count(
        self,
        directory: Path,
        old_content: Optional[str],
        quarantine: bool,
        timestamp: str
    ) -> RepairResult:
        """Repair wrong digit count in dir_id (reallocate)."""
        dir_id_path = directory / ".dir_id"
        
        # Quarantine old file
        if quarantine and dir_id_path.exists():
            quarantine_path = directory / f".dir_id.corrupt.{timestamp}"
            shutil.copy2(dir_id_path, quarantine_path)
        
        # Reallocate new ID
        result = self.resolver.resolve_identity(directory, allocate_if_missing=True)
        
        if result.status != "allocated":
            raise ValueError(f"Failed to reallocate dir_id: {result.error_message}")
        
        # Read new content
        new_content = dir_id_path.read_text(encoding='utf-8')
        
        # Save evidence
        evidence_path = self._save_evidence(
            directory,
            timestamp,
            "regenerated",
            old_content,
            new_content,
            "Wrong digit count - reallocated new dir_id"
        )
        
        return RepairResult(
            success=True,
            action_taken='regenerated',
            old_content=old_content,
            new_content=new_content,
            evidence_path=evidence_path,
            defect_code="DIR-IDENTITY-007"
        )
    
    def _quarantine_and_regenerate(
        self,
        directory: Path,
        old_content: Optional[str],
        quarantine: bool,
        timestamp: str
    ) -> RepairResult:
        """Quarantine unrecoverable .dir_id and regenerate."""
        dir_id_path = directory / ".dir_id"
        
        # Quarantine
        if quarantine and dir_id_path.exists():
            quarantine_path = directory / f".dir_id.corrupt.{timestamp}"
            shutil.copy2(dir_id_path, quarantine_path)
        
        # Delete corrupt file
        if dir_id_path.exists():
            dir_id_path.unlink()
        
        # Allocate fresh dir_id
        result = self.resolver.resolve_identity(directory, allocate_if_missing=True)
        
        if result.status != "allocated":
            raise ValueError(f"Failed to allocate new dir_id: {result.error_message}")
        
        # Read new content
        new_content = dir_id_path.read_text(encoding='utf-8')
        
        # Save evidence
        evidence_path = self._save_evidence(
            directory,
            timestamp,
            "quarantined",
            old_content,
            new_content,
            "Unrecoverable corruption - quarantined and regenerated"
        )
        
        return RepairResult(
            success=True,
            action_taken='quarantined',
            old_content=old_content,
            new_content=new_content,
            evidence_path=evidence_path,
            defect_code="DIR-IDENTITY-008"
        )
    
    def _save_evidence(
        self,
        directory: Path,
        timestamp: str,
        action: str,
        old_content: Optional[str],
        new_content: Optional[str],
        description: str
    ) -> Path:
        """Save repair evidence to evidence directory."""
        relative_path = directory.relative_to(self.project_root)
        safe_path = str(relative_path).replace("/", "_").replace("\\", "_")
        
        evidence_file = self.evidence_dir / f"{timestamp}_repair_{safe_path}.json"
        
        evidence = {
            "timestamp": timestamp,
            "directory": str(directory),
            "relative_path": str(relative_path),
            "action": action,
            "description": description,
            "old_content": old_content,
            "new_content": new_content
        }
        
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, indent=2)
        
        return evidence_file


def fix_invalid_dir_id_anchors(
    directory: Path,
    validation_errors: List[str],
    quarantine: bool = True,
    project_root: Optional[Path] = None,
    project_root_id: Optional[str] = None
) -> RepairResult:
    """Auto-repair invalid .dir_id anchor (public API).
    
    Args:
        directory: Directory containing invalid .dir_id
        validation_errors: List of validation error messages
        quarantine: If True, quarantine unrecoverable .dir_id before regenerating
        project_root: Optional project root (auto-detected if None)
        project_root_id: Optional project root ID (read from config if None)
        
    Returns:
        RepairResult: Outcome of repair operation
    """
    if project_root is None:
        # Auto-detect project root
        project_root = directory
        while project_root.parent != project_root:
            if (project_root / ".git").exists():
                break
            project_root = project_root.parent
    
    if project_root_id is None:
        # Try to read from root .dir_id
        try:
            root_dir_id_path = project_root / ".dir_id"
            if root_dir_id_path.exists():
                with open(root_dir_id_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                project_root_id = data.get('dir_id', '01260207201000000000')
            else:
                project_root_id = '01260207201000000000'
        except Exception:
            project_root_id = '01260207201000000000'
    
    repairer = DirIdAutoRepair(project_root, project_root_id)
    return repairer.fix_invalid_dir_id_anchors(directory, validation_errors, quarantine)
