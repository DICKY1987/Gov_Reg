"""Atomic rename and registry patch transactions (GAP-007).

FILE_ID: 01999000042260125112
PURPOSE: Atomic transactions for rename operations with registry updates
PHASE: Phase 1 - Critical Infrastructure
BACKLOG: 01999000042260125103 GAP-007
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


@dataclass
class RenameOp:
    """A rename operation."""
    old_path: Path
    new_path: Path


@dataclass
class RewriteOp:
    """A reference rewrite operation."""
    file_path: Path
    old_ref: str
    new_ref: str


@dataclass
class TransactionResult:
    """Result of an atomic transaction."""
    transaction_id: str
    timestamp: str
    success: bool
    steps_completed: int
    steps_total: int
    rollback_applied: bool
    error: Optional[str]
    evidence_path: Path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON."""
        result = asdict(self)
        result['evidence_path'] = str(result['evidence_path'])
        return result


class AtomicTransaction:
    """Atomic transaction manager for rename + registry updates.
    
    Protocol:
        1. Prepare: Validate, snapshot
        2. Execute: Rename, patch registry, rewrite references
        3. Rollback: Reverse all operations on failure
        4. Commit: Cleanup, emit evidence
    """
    
    def __init__(
        self,
        rename_ops: List[RenameOp],
        registry_patch: Dict[str, Any],
        reference_rewrites: List[RewriteOp],
        registry_path: Path,
        project_root: Path,
        evidence_dir: Optional[Path] = None
    ):
        """Initialize transaction.
        
        Args:
            rename_ops: List of rename operations
            registry_patch: JSON Patch for registry updates
            reference_rewrites: List of reference rewrite operations
            registry_path: Path to governance registry
            project_root: Project root directory
            evidence_dir: Directory for evidence artifacts
        """
        self.rename_ops = rename_ops
        self.registry_patch = registry_patch
        self.reference_rewrites = reference_rewrites
        self.registry_path = registry_path
        self.project_root = project_root
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "transactions"
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        self.transaction_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.snapshot_dir = self.evidence_dir / f"{self.transaction_id}_snapshot"
        self.transaction_log: List[Dict[str, Any]] = []
        self.steps_completed = 0
        self.steps_total = len(rename_ops) + 1 + len(reference_rewrites)  # renames + registry + rewrites
    
    def execute(self) -> TransactionResult:
        """Execute transaction with rollback on failure."""
        try:
            # Phase 1: Prepare
            self._prepare()
            
            # Phase 2: Execute
            self._execute_renames()
            self._execute_registry_patch()
            self._execute_reference_rewrites()
            
            # Phase 4: Commit
            self._commit()
            
            # Save evidence
            evidence_path = self._save_evidence(success=True, error=None)
            
            return TransactionResult(
                transaction_id=self.transaction_id,
                timestamp=self.timestamp,
                success=True,
                steps_completed=self.steps_completed,
                steps_total=self.steps_total,
                rollback_applied=False,
                error=None,
                evidence_path=evidence_path
            )
            
        except Exception as e:
            # Phase 3: Rollback
            try:
                self._rollback()
                rollback_applied = True
            except Exception as rollback_error:
                rollback_applied = False
                error_msg = f"Transaction failed: {e}. Rollback also failed: {rollback_error}"
            else:
                error_msg = f"Transaction failed: {e}. Rollback successful."
            
            # Save evidence
            evidence_path = self._save_evidence(success=False, error=error_msg)
            
            return TransactionResult(
                transaction_id=self.transaction_id,
                timestamp=self.timestamp,
                success=False,
                steps_completed=self.steps_completed,
                steps_total=self.steps_total,
                rollback_applied=rollback_applied,
                error=error_msg,
                evidence_path=evidence_path
            )
    
    def _prepare(self):
        """Phase 1: Validate and snapshot."""
        # Validate all paths exist
        for op in self.rename_ops:
            if not op.old_path.exists():
                raise FileNotFoundError(f"Path does not exist: {op.old_path}")
        
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry not found: {self.registry_path}")
        
        # Create snapshot directory
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Snapshot registry
        registry_snapshot = self.snapshot_dir / "registry.json"
        shutil.copy2(self.registry_path, registry_snapshot)
        
        # Snapshot files to be renamed
        for i, op in enumerate(self.rename_ops):
            if op.old_path.is_file():
                snapshot_file = self.snapshot_dir / f"file_{i}_{op.old_path.name}"
                shutil.copy2(op.old_path, snapshot_file)
        
        # Snapshot files to be rewritten
        for i, rewrite in enumerate(self.reference_rewrites):
            if rewrite.file_path.exists() and rewrite.file_path.is_file():
                snapshot_file = self.snapshot_dir / f"rewrite_{i}_{rewrite.file_path.name}"
                shutil.copy2(rewrite.file_path, snapshot_file)
        
        self._log_step("prepare", "Validation and snapshot complete")
    
    def _execute_renames(self):
        """Execute rename operations."""
        for op in self.rename_ops:
            # Ensure parent directory exists
            op.new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Rename
            shutil.move(str(op.old_path), str(op.new_path))
            
            self.steps_completed += 1
            self._log_step(
                "rename",
                f"Renamed {op.old_path} -> {op.new_path}",
                {"old_path": str(op.old_path), "new_path": str(op.new_path)}
            )
    
    def _execute_registry_patch(self):
        """Apply JSON Patch to registry."""
        # Load registry
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        # Apply patch (simplified - full implementation would use jsonpatch library)
        for operation in self.registry_patch.get('operations', []):
            op_type = operation.get('op')
            path_parts = operation.get('path', '').strip('/').split('/')
            value = operation.get('value')
            
            if op_type == 'replace':
                # Navigate to the target
                target = registry
                for part in path_parts[:-1]:
                    target = target[part]
                target[path_parts[-1]] = value
        
        # Write back atomically
        temp_path = self.registry_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
        temp_path.replace(self.registry_path)
        
        self.steps_completed += 1
        self._log_step("registry_patch", "Registry patch applied")
    
    def _execute_reference_rewrites(self):
        """Execute reference rewrites."""
        for rewrite in self.reference_rewrites:
            if not rewrite.file_path.exists():
                continue
            
            # Read file
            content = rewrite.file_path.read_text(encoding='utf-8')
            
            # Replace reference
            new_content = content.replace(rewrite.old_ref, rewrite.new_ref)
            
            # Write back
            rewrite.file_path.write_text(new_content, encoding='utf-8')
            
            self.steps_completed += 1
            self._log_step(
                "rewrite",
                f"Rewrote reference in {rewrite.file_path}",
                {
                    "file_path": str(rewrite.file_path),
                    "old_ref": rewrite.old_ref,
                    "new_ref": rewrite.new_ref
                }
            )
    
    def _rollback(self):
        """Phase 3: Rollback all operations."""
        # Restore registry
        registry_snapshot = self.snapshot_dir / "registry.json"
        if registry_snapshot.exists():
            shutil.copy2(registry_snapshot, self.registry_path)
            self._log_step("rollback", "Registry restored from snapshot")
        
        # Reverse renames
        for i, op in enumerate(reversed(self.rename_ops)):
            if op.new_path.exists():
                # Move back
                shutil.move(str(op.new_path), str(op.old_path))
            else:
                # Restore from snapshot
                snapshot_file = self.snapshot_dir / f"file_{len(self.rename_ops) - 1 - i}_{op.old_path.name}"
                if snapshot_file.exists():
                    shutil.copy2(snapshot_file, op.old_path)
            self._log_step("rollback", f"Reversed rename: {op.new_path} -> {op.old_path}")
        
        # Restore rewritten files
        for i, rewrite in enumerate(self.reference_rewrites):
            snapshot_file = self.snapshot_dir / f"rewrite_{i}_{rewrite.file_path.name}"
            if snapshot_file.exists() and rewrite.file_path.exists():
                shutil.copy2(snapshot_file, rewrite.file_path)
                self._log_step("rollback", f"Restored {rewrite.file_path}")
    
    def _commit(self):
        """Phase 4: Cleanup and finalize."""
        # Delete snapshot
        if self.snapshot_dir.exists():
            shutil.rmtree(self.snapshot_dir)
        
        self._log_step("commit", "Transaction committed, snapshot deleted")
    
    def _log_step(self, phase: str, description: str, details: Optional[Dict[str, Any]] = None):
        """Log a transaction step."""
        self.transaction_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": phase,
            "description": description,
            "details": details or {}
        })
    
    def _save_evidence(self, success: bool, error: Optional[str]) -> Path:
        """Save transaction evidence."""
        evidence_file = self.evidence_dir / f"{self.transaction_id}_txn.json"
        
        evidence = {
            "transaction_id": self.transaction_id,
            "timestamp": self.timestamp,
            "success": success,
            "steps_completed": self.steps_completed,
            "steps_total": self.steps_total,
            "error": error,
            "rename_ops": [{"old_path": str(op.old_path), "new_path": str(op.new_path)} for op in self.rename_ops],
            "registry_patch": self.registry_patch,
            "reference_rewrites": [
                {
                    "file_path": str(rw.file_path),
                    "old_ref": rw.old_ref,
                    "new_ref": rw.new_ref
                }
                for rw in self.reference_rewrites
            ],
            "transaction_log": self.transaction_log,
            "defect_code": "TXN-SUCCESS" if success else "TXN-ROLLBACK"
        }
        
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, indent=2)
        
        return evidence_file


@contextmanager
def atomic_rename_and_registry_patch(
    rename_ops: List[Tuple[Path, Path]],
    registry_patch: Dict[str, Any],
    reference_rewrites: List[Tuple[Path, str, str]],
    registry_path: Path,
    project_root: Path
):
    """Context manager for atomic rename and registry patch operations.
    
    Args:
        rename_ops: List of (old_path, new_path) tuples
        registry_patch: JSON Patch for registry updates
        reference_rewrites: List of (file_path, old_ref, new_ref) tuples
        registry_path: Path to governance registry
        project_root: Project root directory
        
    Yields:
        TransactionResult: Result of transaction
        
    Example:
        with atomic_rename_and_registry_patch(
            [(old_file, new_file)],
            {"operations": [...]},
            [(config, "old_id", "new_id")],
            registry_path,
            project_root
        ) as result:
            if not result.success:
                raise RuntimeError(f"Transaction failed: {result.error}")
    """
    # Convert tuples to dataclasses
    rename_ops_dc = [RenameOp(old, new) for old, new in rename_ops]
    rewrite_ops_dc = [RewriteOp(path, old_ref, new_ref) for path, old_ref, new_ref in reference_rewrites]
    
    # Create and execute transaction
    txn = AtomicTransaction(
        rename_ops_dc,
        registry_patch,
        rewrite_ops_dc,
        registry_path,
        project_root
    )
    
    result = txn.execute()
    yield result
