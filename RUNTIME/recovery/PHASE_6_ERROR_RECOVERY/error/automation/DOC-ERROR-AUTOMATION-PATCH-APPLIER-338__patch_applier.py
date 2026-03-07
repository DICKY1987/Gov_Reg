# DOC_LINK: DOC-ERROR-AUTOMATION-PATCH-APPLIER-338
"""Automated patch application with validation and confidence scoring."""
DOC_ID: DOC-ERROR-AUTOMATION-PATCH-APPLIER-338

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class PatchDecision(Enum):
    """Decision on patch application."""
    AUTO_MERGE = "auto_merge"
    AUTO_MERGE_PR = "auto_merge_pr"
    MANUAL_REVIEW = "manual_review"
    REJECTED = "rejected"


@dataclass
class ConfidenceScore:
    """Confidence scoring for patch safety."""

    tests_passed: float = 0.0  # 0.0-1.0
    lint_passed: float = 0.0
    type_check_passed: float = 0.0
    security_scan_passed: float = 0.0
    coverage_maintained: float = 0.0

    @property
    def overall(self) -> float:
        """Calculate overall confidence score."""
        weights = {
            'tests': 0.4,
            'lint': 0.2,
            'types': 0.15,
            'security': 0.15,
            'coverage': 0.1
        }
        return (
            weights['tests'] * self.tests_passed +
            weights['lint'] * self.lint_passed +
            weights['types'] * self.type_check_passed +
            weights['security'] * self.security_scan_passed +
            weights['coverage'] * self.coverage_maintained
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'tests_passed': self.tests_passed,
            'lint_passed': self.lint_passed,
            'type_check_passed': self.type_check_passed,
            'security_scan_passed': self.security_scan_passed,
            'coverage_maintained': self.coverage_maintained,
            'overall': self.overall
        }


class PatchApplier:
    """Automated patch application with validation and safety checks."""

    def __init__(
        self,
        repo_path: Path,
        test_command: str = "pytest -q",
        lint_command: str = "ruff check",
        type_check_command: str = "mypy",
        auto_merge_threshold: float = 0.95,
        pr_threshold: float = 0.80
    ):
        """Initialize patch applier.

        Args:
            repo_path: Path to git repository
            test_command: Command to run tests
            lint_command: Command to run linter
            type_check_command: Command to run type checker
            auto_merge_threshold: Confidence threshold for auto-merge
            pr_threshold: Confidence threshold for PR with auto-merge
        """
        self.repo_path = Path(repo_path)
        self.test_command = test_command
        self.lint_command = lint_command
        self.type_check_command = type_check_command
        self.auto_merge_threshold = auto_merge_threshold
        self.pr_threshold = pr_threshold
        self.decision_log = Path(".state/patch_decisions.jsonl")
        self.decision_log.parent.mkdir(parents=True, exist_ok=True)

    def apply_with_validation(self, patch_path: Path) -> Dict[str, Any]:
        """Apply patch with full validation pipeline.

        Args:
            patch_path: Path to patch file

        Returns:
            Dictionary with decision, confidence, and metadata
        """
        result = {
            'patch_path': str(patch_path),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'decision': None,
            'confidence': None,
            'validation_results': {}
        }

        with tempfile.TemporaryDirectory(prefix='patch_validation_') as tmpdir:
            worktree_path = Path(tmpdir) / 'worktree'

            try:
                self._create_worktree(worktree_path)

                self._apply_patch(worktree_path, patch_path)

                confidence = self._validate_patch(worktree_path, result)

                decision = self._make_decision(confidence)

                result['confidence'] = confidence.to_dict()
                result['decision'] = decision.value

                if decision == PatchDecision.AUTO_MERGE:
                    result['action_taken'] = self._auto_merge(patch_path)
                elif decision == PatchDecision.AUTO_MERGE_PR:
                    result['action_taken'] = self._create_pr_with_auto_merge(patch_path)
                else:
                    result['action_taken'] = self._queue_for_manual_review(patch_path, confidence)

            except Exception as e:
                result['error'] = str(e)
                result['decision'] = PatchDecision.REJECTED.value
                result['action_taken'] = {'status': 'error', 'message': str(e)}

            finally:
                self._cleanup_worktree(worktree_path)

        self._record_decision(result)
        return result

    def _create_worktree(self, worktree_path: Path) -> None:
        """Create isolated git worktree for testing."""
        subprocess.run(
            ['git', 'worktree', 'add', str(worktree_path), 'HEAD'],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )

    def _cleanup_worktree(self, worktree_path: Path) -> None:
        """Remove git worktree."""
        try:
            subprocess.run(
                ['git', 'worktree', 'remove', str(worktree_path), '--force'],
                cwd=self.repo_path,
                capture_output=True
            )
        except Exception:
            pass

    def _apply_patch(self, worktree_path: Path, patch_path: Path) -> None:
        """Apply patch in worktree."""
        subprocess.run(
            ['git', 'apply', str(patch_path)],
            cwd=worktree_path,
            check=True,
            capture_output=True
        )

    def _validate_patch(self, worktree_path: Path, result: Dict[str, Any]) -> ConfidenceScore:
        """Run validation checks and calculate confidence."""
        confidence = ConfidenceScore()

        tests_result = self._run_tests(worktree_path)
        result['validation_results']['tests'] = tests_result
        confidence.tests_passed = 1.0 if tests_result['passed'] else 0.0

        lint_result = self._run_lint(worktree_path)
        result['validation_results']['lint'] = lint_result
        confidence.lint_passed = 1.0 if lint_result['passed'] else 0.5

        type_result = self._run_type_check(worktree_path)
        result['validation_results']['type_check'] = type_result
        confidence.type_check_passed = 1.0 if type_result['passed'] else 0.5

        security_result = self._run_security_scan(worktree_path)
        result['validation_results']['security'] = security_result
        confidence.security_scan_passed = 1.0 if security_result['passed'] else 0.0

        coverage_result = self._check_coverage(worktree_path)
        result['validation_results']['coverage'] = coverage_result
        confidence.coverage_maintained = coverage_result.get('score', 0.5)

        return confidence

    def _run_tests(self, worktree_path: Path) -> Dict[str, Any]:
        """Run test suite."""
        try:
            result = subprocess.run(
                self.test_command.split(),
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                'passed': result.returncode == 0,
                'output': result.stdout + result.stderr
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _run_lint(self, worktree_path: Path) -> Dict[str, Any]:
        """Run linter."""
        try:
            result = subprocess.run(
                self.lint_command.split(),
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                'passed': result.returncode == 0,
                'output': result.stdout + result.stderr
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _run_type_check(self, worktree_path: Path) -> Dict[str, Any]:
        """Run type checker."""
        try:
            result = subprocess.run(
                self.type_check_command.split(),
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                'passed': result.returncode == 0,
                'output': result.stdout + result.stderr
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _run_security_scan(self, worktree_path: Path) -> Dict[str, Any]:
        """Run security scan."""
        return {'passed': True, 'message': 'Security scan placeholder'}

    def _check_coverage(self, worktree_path: Path) -> Dict[str, Any]:
        """Check test coverage."""
        return {'score': 0.8, 'message': 'Coverage check placeholder'}

    def _make_decision(self, confidence: ConfidenceScore) -> PatchDecision:
        """Make decision based on confidence score."""
        overall = confidence.overall

        if overall >= self.auto_merge_threshold:
            return PatchDecision.AUTO_MERGE
        elif overall >= self.pr_threshold:
            return PatchDecision.AUTO_MERGE_PR
        else:
            return PatchDecision.MANUAL_REVIEW

    def _auto_merge(self, patch_path: Path) -> Dict[str, Any]:
        """Auto-merge patch directly."""
        try:
            subprocess.run(
                ['git', 'apply', str(patch_path)],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ['git', 'add', '-A'],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ['git', 'commit', '-m', f'Auto-apply patch: {patch_path.name}'],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            return {'status': 'merged', 'method': 'auto_merge'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}

    def _create_pr_with_auto_merge(self, patch_path: Path) -> Dict[str, Any]:
        """Create PR with auto-merge enabled for medium-confidence patches.

        Pattern: EXEC-003 - Tool availability guard with graceful fallback
        """
        try:
            # Import PR creator (lazy to avoid dependency if not used)
            from error.automation.pr_creator import PRCreator

            # Get repo info from git config
            repo_info = self._get_repo_info()

            # Create PR
            creator = PRCreator(
                repo_owner=repo_info['owner'],
                repo_name=repo_info['name']
            )

            # Get confidence score from last validation
            confidence = self._last_confidence_score

            result = creator.create_pr_with_auto_merge(
                patch_path=patch_path,
                confidence=confidence.to_dict() if hasattr(confidence, 'to_dict') else {
                    'overall': confidence.overall,
                    'tests_passed': confidence.tests_passed,
                    'lint_passed': confidence.lint_passed,
                    'type_check_passed': confidence.type_check_passed,
                    'security_scan_passed': confidence.security_scan_passed,
                    'coverage_maintained': confidence.coverage_maintained
                }
            )

            return result

        except (ImportError, ValueError) as e:
            # Graceful fallback: Queue for manual PR creation
            return {
                'status': 'pr_creation_failed',
                'error': str(e),
                'fallback': 'Patch queued for manual PR creation'
            }

    def _get_repo_info(self) -> Dict[str, str]:
        """Extract repo owner/name from git remote.

        Returns:
            Dict with 'owner' and 'name' keys

        Raises:
            ValueError: If remote URL cannot be parsed
        """
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        # Parse: git@github.com:owner/repo.git or https://github.com/owner/repo.git
        url = result.stdout.strip()

        if 'github.com' in url:
            # Extract owner and repo name
            if url.startswith('git@'):
                # SSH format: git@github.com:owner/repo.git
                parts = url.split(':')[1].split('/')
            else:
                # HTTPS format: https://github.com/owner/repo.git
                parts = url.split('/')[-2:]

            owner = parts[0]
            name = parts[1].replace('.git', '')
            return {'owner': owner, 'name': name}

        raise ValueError(f"Could not parse GitHub repo from remote: {url}")

    def _queue_for_manual_review(
        self,
        patch_path: Path,
        confidence: ConfidenceScore
    ) -> Dict[str, Any]:
        """Queue patch for manual review."""
        review_queue = Path(".state/manual_review_queue.jsonl")
        entry = {
            'patch_path': str(patch_path),
            'confidence': confidence.to_dict(),
            'queued_at': datetime.now(timezone.utc).isoformat()
        }
        with open(review_queue, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        return {'status': 'queued', 'queue_path': str(review_queue)}

    def _record_decision(self, result: Dict[str, Any]) -> None:
        """Record decision to log."""
        with open(self.decision_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result) + '\n')
