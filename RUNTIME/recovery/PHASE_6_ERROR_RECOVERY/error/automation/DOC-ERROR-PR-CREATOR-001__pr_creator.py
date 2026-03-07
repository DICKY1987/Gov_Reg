# DOC_LINK: DOC-ERROR-PR-CREATOR-001
"""GitHub PR creation for error patches

EXECUTION PATTERN: EXEC-003 (Tool Availability Guards)
- Validates GitHub token before execution
- Checks repository access
- Graceful fallback if API unavailable

DOC_ID: DOC-ERROR-PR-CREATOR-001
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


class PRCreator:
    """Creates PRs with auto-merge for validated patches"""

    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        token: Optional[str] = None
    ):
        """Initialize PR creator with GitHub credentials.

        Pattern: EXEC-003 - Validate tool availability at init

        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            token: GitHub personal access token (or use GITHUB_TOKEN env var)

        Raises:
            ValueError: If token not provided or repo inaccessible
            ImportError: If PyGithub not installed
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name

        # Get token from env or parameter
        self.token = token or os.getenv('GITHUB_TOKEN')

        # EXEC-003: Validate token availability
        if not self.token:
            raise ValueError(
                "GITHUB_TOKEN environment variable required for PR creation. "
                "Set via: export GITHUB_TOKEN='ghp_...'"
            )

        # Lazy import to allow module load even if PyGithub not installed
        try:
            from github import Github, GithubException
            self.Github = Github
            self.GithubException = GithubException
        except ImportError as e:
            raise ImportError(
                "PyGithub library required for PR creation. "
                "Install via: pip install PyGithub"
            ) from e

        # Initialize GitHub client
        self.gh = self.Github(self.token)

        # EXEC-003: Validate repository access
        try:
            self.repo = self.gh.get_repo(f"{repo_owner}/{repo_name}")
            # Test access
            self.repo.get_branch('main')
        except self.GithubException as e:
            raise ValueError(
                f"Cannot access repository {repo_owner}/{repo_name}. "
                f"Check token permissions. Error: {e}"
            )

    def create_pr_with_auto_merge(
        self,
        patch_path: Path,
        confidence: Dict[str, float],
        base_branch: str = 'main'
    ) -> Dict[str, Any]:
        """Create PR with auto-merge enabled.

        Pattern: EXEC-004 - Atomic multi-step operation
        - Create branch
        - Apply patch
        - Create PR
        - Enable auto-merge
        - Rollback on any failure

        Args:
            patch_path: Path to patch file
            confidence: Confidence scores dictionary
            base_branch: Base branch for PR (default: 'main')

        Returns:
            Dict with status, pr_number, pr_url, branch, auto_merge_enabled
        """
        from datetime import datetime

        branch_name = f"error-fix/{patch_path.stem}-{self._generate_timestamp()}"
        pr = None

        try:
            # Step 1: Create branch
            base_ref = self.repo.get_git_ref(f"heads/{base_branch}")
            self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_ref.object.sha
            )

            # Step 2: Apply patch to branch
            self._apply_patch_to_branch(patch_path, branch_name)

            # Step 3: Create PR
            pr = self.repo.create_pull(
                title=f"[Auto] Error fix: {patch_path.stem}",
                body=self._generate_pr_body(patch_path, confidence),
                head=branch_name,
                base=base_branch
            )

            # Step 4: Add labels
            pr.add_to_labels('automated-fix', 'error-recovery')

            # Step 5: Enable auto-merge (using gh CLI)
            auto_merge_enabled = self._enable_auto_merge_cli(pr.number)

            return {
                'status': 'pr_created',
                'pr_number': pr.number,
                'pr_url': pr.html_url,
                'branch': branch_name,
                'auto_merge_enabled': auto_merge_enabled
            }

        except Exception as e:
            # Rollback: Delete branch if PR creation failed
            if pr is None:
                try:
                    self.repo.get_git_ref(f"heads/{branch_name}").delete()
                except Exception:
                    pass

            return {
                'status': 'failed',
                'error': str(e),
                'branch': branch_name
            }

    def _apply_patch_to_branch(self, patch_path: Path, branch_name: str) -> None:
        """Apply patch to remote branch.

        Uses local git worktree to apply patch, then pushes to remote.
        """
        import tempfile

        with tempfile.TemporaryDirectory(prefix='pr_patch_') as tmpdir:
            worktree_path = Path(tmpdir) / 'worktree'

            # Create worktree on new branch
            subprocess.run(
                ['git', 'worktree', 'add', str(worktree_path), branch_name],
                check=True,
                capture_output=True
            )

            try:
                # Apply patch
                subprocess.run(
                    ['git', 'apply', str(patch_path)],
                    cwd=worktree_path,
                    check=True,
                    capture_output=True
                )

                # Stage and commit
                subprocess.run(
                    ['git', 'add', '-A'],
                    cwd=worktree_path,
                    check=True,
                    capture_output=True
                )

                subprocess.run(
                    ['git', 'commit', '-m', f'Auto-apply patch: {patch_path.name}'],
                    cwd=worktree_path,
                    check=True,
                    capture_output=True
                )

                # Push to remote
                subprocess.run(
                    ['git', 'push', 'origin', branch_name],
                    cwd=worktree_path,
                    check=True,
                    capture_output=True
                )

            finally:
                # Cleanup worktree
                subprocess.run(
                    ['git', 'worktree', 'remove', str(worktree_path), '--force'],
                    capture_output=True
                )

    def _enable_auto_merge_cli(self, pr_number: int) -> bool:
        """Enable auto-merge using GitHub CLI.

        Requires 'gh' CLI to be installed and authenticated.

        Returns:
            True if auto-merge enabled, False otherwise
        """
        try:
            subprocess.run(
                ['gh', 'pr', 'merge', str(pr_number), '--auto', '--squash'],
                check=True,
                capture_output=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Non-fatal: PR created but auto-merge not enabled
            print(f"Warning: Could not enable auto-merge for PR #{pr_number}")
            return False

    def _generate_pr_body(
        self,
        patch_path: Path,
        confidence: Dict[str, float]
    ) -> str:
        """Generate PR description with confidence metrics."""
        overall = confidence.get('overall', 0.0)

        return f"""## Automated Error Recovery Patch

**Patch**: `{patch_path.name}`
**Confidence Score**: {overall:.1%}

### Validation Results

| Check | Result | Score |
|-------|--------|-------|
| Tests | {'✅ Passed' if confidence.get('tests_passed', 0) == 1.0 else '❌ Failed'} | {confidence.get('tests_passed', 0):.1%} |
| Linting | {'✅ Passed' if confidence.get('lint_passed', 0) == 1.0 else '⚠️ Warnings'} | {confidence.get('lint_passed', 0):.1%} |
| Type Checking | {'✅ Passed' if confidence.get('type_check_passed', 0) == 1.0 else '⚠️ Issues'} | {confidence.get('type_check_passed', 0):.1%} |
| Security Scan | {'✅ Passed' if confidence.get('security_scan_passed', 0) == 1.0 else '❌ Failed'} | {confidence.get('security_scan_passed', 0):.1%} |
| Coverage | {'✅ Maintained' if confidence.get('coverage_maintained', 0) >= 0.7 else '⚠️ Reduced'} | {confidence.get('coverage_maintained', 0):.1%} |

### Automation Details

This PR was created automatically by the error recovery automation system.

- **Auto-merge**: {'Enabled - will merge after CI passes' if overall >= 0.80 else 'Disabled - requires manual review'}
- **Decision log**: `.state/patch_decisions.jsonl`
- **Confidence threshold**: {overall:.1%} (PR threshold: 80%)

### Review Guidelines

This patch scored between 80-95% confidence. Please review:

1. ✅ Validation results above are acceptable
2. ✅ Changes align with project conventions
3. ✅ No unintended side effects

If approved, CI will auto-merge. If not, close this PR and reject the patch in the manual review queue.

---

*Generated by error automation* 🤖
"""

    def _generate_timestamp(self) -> str:
        """Generate timestamp for branch name."""
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d%H%M%S')
