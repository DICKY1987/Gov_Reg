# DOC_LINK: DOC-CORE-ENGINE-INTEGRATION-WORKER-150
"""Integration worker for merge conflict detection and resolution.

Phase I WS-I4: Handles merging of parallel workstream results.
"""

# DOC_ID: DOC-CORE-ENGINE-INTEGRATION-WORKER-150

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class MergeConflict:
    """Represents a merge conflict."""

    workstream_id: str
    file_path: str
    conflict_type: str  # 'content', 'delete', 'rename'
    base_branch: str
    feature_branch: str
    detected_at: datetime


@dataclass
class MergeResult:
    """Result of merge operation."""

    success: bool
    conflicts: List[MergeConflict]
    merged_files: List[str]
    error_message: Optional[str] = None


class IntegrationWorker:
    """Handles integration of parallel workstream results."""

    def __init__(self, repo_root: Path):
        """Initialize integration worker.

        Args:
            repo_root: Repository root directory
        """
        self.repo_root = repo_root

    def merge_workstream_results(
        self, base_branch: str, feature_branches: List[str], run_id: str
    ) -> MergeResult:
        """Merge results from multiple parallel workstreams.

        Args:
            base_branch: Base branch (usually 'main')
            feature_branches: List of feature branches to merge
            run_id: Execution run ID

        Returns:
            MergeResult with conflicts detected
        """
        conflicts = []
        merged_files = []

        # Create integration branch
        integration_branch = f"uet-integration-{run_id}"

        try:
            # Create integration branch from base
            subprocess.run(
                ["git", "checkout", "-b", integration_branch, base_branch],
                cwd=str(self.repo_root),
                check=True,
                capture_output=True,
                text=True,
            )

            # Merge each feature branch
            for branch in feature_branches:
                try:
                    result = subprocess.run(
                        ["git", "merge", "--no-ff", "--no-commit", branch],
                        cwd=str(self.repo_root),
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode != 0:
                        # Detect conflicts
                        branch_conflicts = self._detect_conflicts(branch, base_branch)
                        conflicts.extend(branch_conflicts)

                        # Abort merge
                        subprocess.run(
                            ["git", "merge", "--abort"],
                            cwd=str(self.repo_root),
                            check=False,
                        )
                    else:
                        # Get merged files
                        files = self._get_changed_files(branch)
                        merged_files.extend(files)

                        # Commit merge
                        subprocess.run(
                            ["git", "commit", "-m", f"Merge {branch}"],
                            cwd=str(self.repo_root),
                            check=True,
                        )

                except subprocess.CalledProcessError as e:
                    return MergeResult(
                        success=False,
                        conflicts=[],
                        merged_files=[],
                        error_message=f"Merge failed for {branch}: {e}",
                    )

            # Success if no conflicts
            if not conflicts:
                return MergeResult(
                    success=True, conflicts=[], merged_files=merged_files
                )
            else:
                return MergeResult(
                    success=False, conflicts=conflicts, merged_files=merged_files
                )

        except Exception as e:
            return MergeResult(
                success=False,
                conflicts=conflicts,
                merged_files=merged_files,
                error_message=str(e),
            )

        finally:
            # Cleanup: return to base branch
            try:
                subprocess.run(
                    ["git", "checkout", base_branch],
                    cwd=str(self.repo_root),
                    check=False,
                )
            except:
                pass

    def _detect_conflicts(self, branch: str, base_branch: str) -> List[MergeConflict]:
        """Detect merge conflicts between branches.

        Args:
            branch: Feature branch
            base_branch: Base branch

        Returns:
            List of MergeConflict objects
        """
        conflicts = []

        try:
            # Get conflicted files
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                check=True,
            )

            conflicted_files = result.stdout.strip().split("\n")

            for file_path in conflicted_files:
                if file_path:
                    conflicts.append(
                        MergeConflict(
                            workstream_id=branch,
                            file_path=file_path,
                            conflict_type="content",
                            base_branch=base_branch,
                            feature_branch=branch,
                            detected_at=datetime.now(timezone.utc),
                        )
                    )

        except:
            pass

        return conflicts

    def _get_changed_files(self, branch: str) -> List[str]:
        """Get files changed in branch.

        Args:
            branch: Branch name

        Returns:
            List of changed file paths
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD", branch],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                check=True,
            )

            files = result.stdout.strip().split("\n")
            return [f for f in files if f]

        except:
            return []

    def persist_conflicts(self, conflicts: List[MergeConflict], run_id: str) -> None:
        """Persist merge conflicts to database.

        Args:
            conflicts: List of conflicts
            run_id: Execution run ID
        """
        from core.state import db

        db.init_db()

        for conflict in conflicts:
            # Record as merge_conflict in DB
            db.record_event(
                event_type="merge_conflict_detected",
                run_id=run_id,
                ws_id=conflict.workstream_id,
                payload={
                    "file_path": conflict.file_path,
                    "conflict_type": conflict.conflict_type,
                    "base_branch": conflict.base_branch,
                    "feature_branch": conflict.feature_branch,
                },
            )


def detect_and_merge(
    workstream_ids: List[str], run_id: str, repo_root: Optional[Path] = None
) -> MergeResult:
    """Detect and merge workstream results.

    Args:
        workstream_ids: List of workstream IDs
        run_id: Execution run ID
        repo_root: Repository root (default: current directory)

    Returns:
        MergeResult
    """
    if repo_root is None:
        repo_root = Path.cwd()

    worker = IntegrationWorker(repo_root)

    # Assume each workstream creates a branch named ws-{id}
    feature_branches = [f"ws-{ws_id}" for ws_id in workstream_ids]

    result = worker.merge_workstream_results(
        base_branch="main", feature_branches=feature_branches, run_id=run_id
    )

    # Persist conflicts
    if result.conflicts:
        worker.persist_conflicts(result.conflicts, run_id)

    return result
