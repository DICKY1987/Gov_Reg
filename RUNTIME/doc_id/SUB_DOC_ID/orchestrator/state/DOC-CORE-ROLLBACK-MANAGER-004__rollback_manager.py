# DOC_LINK: DOC-CORE-ROLLBACK-MANAGER-004
"""Rollback Manager for ID System Orchestrator

Provides atomic operation capabilities with rollback on failure.
Creates snapshots before modifications and restores on errors.

Based on DOC-GUIDE-PROCESS-FLOW-AND-AUTOMATION-LOGIC-638 Section 7.2.

DOC_ID: DOC-CORE-ROLLBACK-MANAGER-004
"""

import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Snapshot:
    """Represents a filesystem snapshot"""
    snapshot_id: str
    snapshot_path: Path
    created_at: str
    context: str
    files_snapshot: List[str] = field(default_factory=list)
    registries_snapshot: List[str] = field(default_factory=list)
    git_status: Optional[str] = None


class RollbackManager:
    """Manages snapshots and rollback operations

    Usage:
        mgr = RollbackManager()
        snapshot_id = mgr.create_snapshot('pre-commit')

        try:
            # ... perform operations ...
            mgr.commit_snapshot()  # Success - remove snapshot
        except Exception:
            mgr.rollback()  # Failure - restore from snapshot
    """

    def __init__(self, repo_root: Optional[Path] = None):
        """Initialize rollback manager

        Args:
            repo_root: Repository root directory (defaults to current working directory)
        """
        self.repo_root = repo_root or Path.cwd()
        self.snapshot_dir = self.repo_root / 'run' / '.snapshots'
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        self.current_snapshot: Optional[Snapshot] = None
        self.operations: List[Dict] = []

    def _now_iso(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    def create_snapshot(self, context: str) -> str:
        """Create a snapshot before modifications

        Args:
            context: Context identifier (e.g., 'pre-commit', 'ci')

        Returns:
            snapshot_id: Unique snapshot identifier
        """
        # Generate snapshot ID
        timestamp = int(time.time())
        snapshot_id = f"snapshot_{context}_{timestamp}"
        snapshot_path = self.snapshot_dir / snapshot_id
        snapshot_path.mkdir(parents=True, exist_ok=True)

        # Capture git status
        try:
            git_status = subprocess.check_output(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_root,
                encoding='utf-8',
                stderr=subprocess.DEVNULL
            )
        except Exception:
            git_status = None

        # Save git status
        if git_status:
            with open(snapshot_path / 'git_status.txt', 'w', encoding='utf-8') as f:
                f.write(git_status)

        # Initialize snapshot
        self.current_snapshot = Snapshot(
            snapshot_id=snapshot_id,
            snapshot_path=snapshot_path,
            created_at=self._now_iso(),
            context=context,
            git_status=git_status
        )

        # Save snapshot metadata
        self._save_snapshot_metadata()

        return snapshot_id

    def snapshot_file(self, filepath: Path):
        """Add a file to the current snapshot

        Args:
            filepath: Path to file to snapshot (relative or absolute)
        """
        if not self.current_snapshot:
            raise RuntimeError("No active snapshot. Call create_snapshot() first.")

        # Convert to absolute path
        if not filepath.is_absolute():
            filepath = self.repo_root / filepath

        # Only snapshot if file exists
        if not filepath.exists():
            return

        # Create relative path for snapshot
        try:
            rel_path = filepath.relative_to(self.repo_root)
        except ValueError:
            # File is outside repo root
            rel_path = filepath

        # Create snapshot file
        snapshot_file = self.current_snapshot.snapshot_path / rel_path
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(filepath, snapshot_file)

        # Record in snapshot
        self.current_snapshot.files_snapshot.append(str(rel_path))

    def snapshot_directory(self, dirpath: Path, patterns: Optional[List[str]] = None):
        """Snapshot all files in a directory

        Args:
            dirpath: Directory to snapshot
            patterns: Optional glob patterns to include (e.g., ['*.yaml', '*.json'])
        """
        if not self.current_snapshot:
            raise RuntimeError("No active snapshot. Call create_snapshot() first.")

        # Convert to absolute path
        if not dirpath.is_absolute():
            dirpath = self.repo_root / dirpath

        if not dirpath.exists():
            return

        # Snapshot files
        if patterns:
            for pattern in patterns:
                for filepath in dirpath.glob(pattern):
                    if filepath.is_file():
                        self.snapshot_file(filepath)
        else:
            for filepath in dirpath.rglob('*'):
                if filepath.is_file():
                    self.snapshot_file(filepath)

    def snapshot_registries(self):
        """Snapshot all Tier A registry files"""
        registry_paths = [
            'RUNTIME/doc_id/SUB_DOC_ID/5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml',
            'data/registries/id_registry_active.json',
            'data/registries/artifact_map.json',
        ]

        for reg_path in registry_paths:
            filepath = self.repo_root / reg_path
            if filepath.exists():
                self.snapshot_file(filepath)
                if self.current_snapshot:
                    self.current_snapshot.registries_snapshot.append(reg_path)

    def record_operation(self, operation: Dict):
        """Record an operation for potential rollback

        Args:
            operation: Operation metadata (action, target, result, etc.)
        """
        self.operations.append({
            **operation,
            'timestamp': self._now_iso()
        })

    def rollback(self) -> bool:
        """Restore from current snapshot

        Returns:
            True if rollback succeeded, False otherwise
        """
        if not self.current_snapshot:
            raise RuntimeError("No active snapshot to rollback to")

        print(f"Rolling back from snapshot: {self.current_snapshot.snapshot_id}")

        try:
            # Restore all snapshotted files
            for rel_path in self.current_snapshot.files_snapshot:
                src = self.current_snapshot.snapshot_path / rel_path
                dest = self.repo_root / rel_path

                if src.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    print(f"  Restored: {rel_path}")

            # Reset git staging area if we have git status
            if self.current_snapshot.git_status:
                try:
                    subprocess.run(
                        ['git', 'reset', 'HEAD'],
                        cwd=self.repo_root,
                        check=True,
                        capture_output=True
                    )
                    print("  Reset git staging area")
                except Exception as e:
                    print(f"  Warning: Could not reset git staging: {e}")

            print("Rollback complete")
            return True

        except Exception as e:
            print(f"ERROR during rollback: {e}")
            return False

    def commit_snapshot(self):
        """Commit snapshot (operation succeeded, remove snapshot)"""
        if not self.current_snapshot:
            return

        # Remove snapshot directory
        if self.current_snapshot.snapshot_path.exists():
            shutil.rmtree(self.current_snapshot.snapshot_path)

        print(f"Snapshot committed: {self.current_snapshot.snapshot_id}")
        self.current_snapshot = None
        self.operations = []

    def _save_snapshot_metadata(self):
        """Save snapshot metadata to JSON"""
        if not self.current_snapshot:
            return

        metadata = {
            'snapshot_id': self.current_snapshot.snapshot_id,
            'created_at': self.current_snapshot.created_at,
            'context': self.current_snapshot.context,
            'files_snapshot': self.current_snapshot.files_snapshot,
            'registries_snapshot': self.current_snapshot.registries_snapshot,
            'operations': self.operations
        }

        metadata_file = self.current_snapshot.snapshot_path / 'metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)


__doc_id__ = 'DOC-CORE-ROLLBACK-MANAGER-004'
