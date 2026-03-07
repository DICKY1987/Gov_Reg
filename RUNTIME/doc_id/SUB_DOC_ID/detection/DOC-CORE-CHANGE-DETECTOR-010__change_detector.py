# DOC_LINK: DOC-CORE-CHANGE-DETECTOR-010
"""Change Detector for ID System

Detects file changes from git operations.
Implements Section 3.2 Flow 1 from DOC-GUIDE-PROCESS-FLOW-AND-AUTOMATION-LOGIC-638.

DOC_ID: DOC-CORE-CHANGE-DETECTOR-010
"""

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ChangeType(Enum):
    """Types of file changes"""
    FILE_ADDED = "FILE_ADDED"
    FILE_MODIFIED = "FILE_MODIFIED"
    FILE_DELETED = "FILE_DELETED"
    FILE_RENAMED = "FILE_RENAMED"


@dataclass
class Change:
    """Represents a detected change"""
    event_type: ChangeType
    path: str
    old_path: Optional[str] = None
    content_hash: Optional[str] = None
    timestamp: Optional[str] = None
    similarity: Optional[int] = None  # For renames, 0-100

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'event_type': self.event_type.value,
            'path': self.path,
            'old_path': self.old_path,
            'content_hash': self.content_hash,
            'timestamp': self.timestamp,
            'similarity': self.similarity
        }


class ChangeDetector:
    """Detects file changes from git operations

    Supports three modes:
    - staged: Detect changes in git staging area (--cached)
    - branch: Detect changes between current branch and main
    - watcher: Detect filesystem changes (future)

    Deterministic: Same git state → same changes list
    """

    def __init__(self, repo_root: Optional[Path] = None):
        """Initialize change detector

        Args:
            repo_root: Repository root directory
        """
        self.repo_root = repo_root or Path.cwd()

    def detect(self, mode: str = 'staged') -> List[Change]:
        """Detect changes based on mode

        Args:
            mode: Detection mode ('staged', 'branch', 'watcher')

        Returns:
            List of Change objects

        Raises:
            ValueError: If mode is invalid
        """
        if mode == 'staged':
            return self._detect_staged()
        elif mode == 'branch':
            return self._detect_branch()
        elif mode == 'watcher':
            return self._detect_watcher()
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'staged', 'branch', or 'watcher'")

    def _detect_staged(self) -> List[Change]:
        """Detect changes in staging area"""
        changes = []

        try:
            # Get status with rename detection
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-status', '-M90'],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.strip().split('\n')
            if not lines or lines == ['']:
                return []

            for line in lines:
                if not line.strip():
                    continue

                parts = line.split('\t')
                status = parts[0]

                if status.startswith('R'):
                    # Rename: R100  old_path  new_path
                    similarity = int(status[1:]) if len(status) > 1 else 100
                    old_path = parts[1]
                    new_path = parts[2]

                    changes.append(Change(
                        event_type=ChangeType.FILE_RENAMED,
                        path=new_path,
                        old_path=old_path,
                        similarity=similarity,
                        timestamp=self._now_iso()
                    ))

                elif status == 'A':
                    # Added file
                    filepath = parts[1]
                    changes.append(Change(
                        event_type=ChangeType.FILE_ADDED,
                        path=filepath,
                        content_hash=self._compute_file_hash(filepath),
                        timestamp=self._now_iso()
                    ))

                elif status == 'M':
                    # Modified file
                    filepath = parts[1]
                    changes.append(Change(
                        event_type=ChangeType.FILE_MODIFIED,
                        path=filepath,
                        content_hash=self._compute_file_hash(filepath),
                        timestamp=self._now_iso()
                    ))

                elif status == 'D':
                    # Deleted file
                    filepath = parts[1]
                    changes.append(Change(
                        event_type=ChangeType.FILE_DELETED,
                        path=filepath,
                        timestamp=self._now_iso()
                    ))

        except subprocess.CalledProcessError as e:
            print(f"Warning: git diff failed: {e}")
            return []

        return changes

    def _detect_branch(self) -> List[Change]:
        """Detect changes between current branch and origin/main"""
        changes = []

        try:
            # Compare with origin/main
            result = subprocess.run(
                ['git', 'diff', '--name-status', '-M90', 'origin/main...HEAD'],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.strip().split('\n')
            if not lines or lines == ['']:
                return []

            for line in lines:
                if not line.strip():
                    continue

                parts = line.split('\t')
                status = parts[0]

                if status.startswith('R'):
                    similarity = int(status[1:]) if len(status) > 1 else 100
                    old_path = parts[1]
                    new_path = parts[2]

                    changes.append(Change(
                        event_type=ChangeType.FILE_RENAMED,
                        path=new_path,
                        old_path=old_path,
                        similarity=similarity,
                        timestamp=self._now_iso()
                    ))

                elif status == 'A':
                    filepath = parts[1]
                    changes.append(Change(
                        event_type=ChangeType.FILE_ADDED,
                        path=filepath,
                        content_hash=self._compute_file_hash(filepath),
                        timestamp=self._now_iso()
                    ))

                elif status == 'M':
                    filepath = parts[1]
                    changes.append(Change(
                        event_type=ChangeType.FILE_MODIFIED,
                        path=filepath,
                        content_hash=self._compute_file_hash(filepath),
                        timestamp=self._now_iso()
                    ))

                elif status == 'D':
                    filepath = parts[1]
                    changes.append(Change(
                        event_type=ChangeType.FILE_DELETED,
                        path=filepath,
                        timestamp=self._now_iso()
                    ))

        except subprocess.CalledProcessError as e:
            print(f"Warning: git diff failed: {e}")
            return []

        return changes

    def _detect_watcher(self) -> List[Change]:
        """Detect filesystem changes (future implementation)"""
        # Future: Use watchdog library for real-time detection
        raise NotImplementedError("Watcher mode not yet implemented")

    def _compute_file_hash(self, filepath: str) -> Optional[str]:
        """Compute SHA256 hash of file content

        Args:
            filepath: Relative path from repo root

        Returns:
            SHA256 hex digest or None if file doesn't exist
        """
        full_path = self.repo_root / filepath

        if not full_path.exists():
            return None

        try:
            with open(full_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return None

    def _now_iso(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    def save_changes(self, changes: List[Change], output_file: Path):
        """Save changes to JSON file

        Args:
            changes: List of changes
            output_file: Output file path
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'changes': [c.to_dict() for c in changes],
            'total': len(changes),
            'detected_at': self._now_iso()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


__doc_id__ = 'DOC-CORE-CHANGE-DETECTOR-010'
