#!/usr/bin/env python3
# DOC_LINK: DOC-CORE-ADAPTERS-GIT-ADAPTER-1177
"""
Git Adapter with deterministic operations and audit logging.

DOC_ID: DOC-CORE-ADAPTERS-GIT-ADAPTER-1177
"""

from pathlib import Path
from typing import List, Dict, Optional
import subprocess
from datetime import datetime


class GitAdapter:
    """
    Git operations with deterministic output and audit trail.
    """

    def __init__(self, path_registry, repo_root: Optional[Path] = None):
        self.registry = path_registry
        self.repo_root = repo_root or Path.cwd()
        self.audit_log: List[Dict] = []

    def _run_git(self, args: List[str]) -> tuple[int, str, str]:
        """Run git command and return (exit_code, stdout, stderr)."""
        result = subprocess.run(
            ['git'] + args,
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr

    def status(self) -> Dict:
        """Get git status (deterministic output)."""
        exit_code, stdout, stderr = self._run_git(['status', '--porcelain', '--untracked-files=all'])

        if exit_code != 0:
            raise RuntimeError(f"Git status failed: {stderr}")

        # Parse porcelain output
        changes = []
        for line in stdout.strip().split('\n'):
            if line:
                status_code = line[:2]
                filepath = line[3:]
                changes.append({'status': status_code.strip(), 'file': filepath})

        result = {
            'is_clean': len(changes) == 0,
            'changes': sorted(changes, key=lambda x: x['file'])  # Deterministic order
        }

        self.audit_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'operation': 'status',
            'change_count': len(changes)
        })

        return result

    def diff(self, path: Optional[str] = None) -> str:
        """Get git diff (sorted for determinism)."""
        args = ['diff', '--no-color']
        if path:
            args.append(path)

        exit_code, stdout, stderr = self._run_git(args)

        if exit_code != 0:
            raise RuntimeError(f"Git diff failed: {stderr}")

        self.audit_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'operation': 'diff',
            'path': path,
            'diff_size': len(stdout)
        })

        return stdout

    def log(self, max_count: int = 10, format: str = 'oneline') -> List[Dict]:
        """Get git log (deterministic)."""
        args = ['log', f'--max-count={max_count}', f'--pretty=format:%H|%an|%ae|%at|%s']

        exit_code, stdout, stderr = self._run_git(args)

        if exit_code != 0:
            raise RuntimeError(f"Git log failed: {stderr}")

        commits = []
        for line in stdout.strip().split('\n'):
            if line:
                parts = line.split('|', 4)
                commits.append({
                    'hash': parts[0],
                    'author_name': parts[1],
                    'author_email': parts[2],
                    'timestamp': int(parts[3]),
                    'subject': parts[4]
                })

        self.audit_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'operation': 'log',
            'commit_count': len(commits)
        })

        return commits

    def list_changed_files(self, ref: str = 'HEAD') -> List[str]:
        """List changed files (sorted for determinism)."""
        args = ['diff', '--name-only', ref]

        exit_code, stdout, stderr = self._run_git(args)

        if exit_code != 0:
            raise RuntimeError(f"Git list changed files failed: {stderr}")

        files = [f for f in stdout.strip().split('\n') if f]

        self.audit_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'operation': 'list_changed_files',
            'ref': ref,
            'file_count': len(files)
        })

        return sorted(files)  # Deterministic order

    def is_clean(self) -> bool:
        """Check if working tree is clean."""
        status = self.status()
        return status['is_clean']

    def export_audit_log(self) -> List[Dict]:
        """Export audit log."""
        return self.audit_log.copy()
