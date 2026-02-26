#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0998
"""
Git Log Parser - Human vs AI Commit Analysis
Created: 2026-01-04

Parses git log to extract:
- Human commit count
- AI commit count (commits with AI co-author)
- Last human commit timestamp
- Last AI commit timestamp
- Human to AI ratio

Usage:
    from git_log_parser import GitLogParser

    parser = GitLogParser(repo_root, file_path)
    timeline = parser.get_timeline()

AI Co-Author Detection:
    Looks for "Co-Authored-By:" trailers in commit messages with patterns:
    - "Claude Sonnet"
    - "Copilot"
    - "AI-generated"
    - "Assistant"
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


# ============================================================================
# AI CO-AUTHOR PATTERNS
# ============================================================================

AI_CO_AUTHOR_PATTERNS = [
    r'Co-Authored-By:.*Claude',
    r'Co-Authored-By:.*Copilot',
    r'Co-Authored-By:.*AI',
    r'Co-Authored-By:.*Assistant',
    r'Generated with.*Claude',
    r'Generated with.*AI',
    r'AI-generated'
]


# ============================================================================
# GIT LOG PARSER
# ============================================================================

class GitLogParser:
    """Parses git log to analyze human vs AI commits."""

    def __init__(self, repo_root: Path, file_path: Optional[str] = None):
        """Initialize parser.

        Args:
            repo_root: Path to git repository root
            file_path: Optional specific file path to analyze (relative to repo root)
        """
        self.repo_root = Path(repo_root)
        self.file_path = file_path

        # Compile AI patterns
        self.ai_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in AI_CO_AUTHOR_PATTERNS]

    def _run_git_command(self, args: List[str]) -> str:
        """Run git command and return output.

        Args:
            args: Git command arguments

        Returns:
            Command output as string
        """
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            # Git command failed (e.g., file not in repo, no commits)
            return ""
        except FileNotFoundError:
            # Git not installed
            return ""

    def _is_ai_commit(self, commit_message: str) -> bool:
        """Check if commit message indicates AI co-authorship.

        Args:
            commit_message: Full commit message

        Returns:
            True if AI co-author detected
        """
        for pattern in self.ai_patterns:
            if pattern.search(commit_message):
                return True
        return False

    def get_timeline(self) -> Dict[str, Any]:
        """Get git timeline data for file.

        Returns:
            Dictionary with timeline data matching provenance.git.timeline.* schema
        """
        # Build git log command
        args = [
            'log',
            '--all',
            '--format=%H|%aI|%B',  # hash|author_date_iso|body
            '--'
        ]

        if self.file_path:
            args.append(self.file_path)

        output = self._run_git_command(args)

        if not output:
            # No commits or git unavailable
            return self._empty_timeline()

        # Parse commits
        human_commits = []
        ai_commits = []

        commit_entries = output.split('\n\n')  # Commits separated by blank lines
        for entry in commit_entries:
            if not entry.strip():
                continue

            lines = entry.strip().split('\n')
            if not lines:
                continue

            # First line: hash|date|start_of_message
            first_line = lines[0]
            parts = first_line.split('|', 2)
            if len(parts) < 2:
                continue

            commit_hash = parts[0]
            commit_date = parts[1]

            # Full message is first line + remaining lines
            full_message = '\n'.join(lines)

            # Classify as AI or human
            if self._is_ai_commit(full_message):
                ai_commits.append({
                    'hash': commit_hash,
                    'date': commit_date,
                    'message': full_message
                })
            else:
                human_commits.append({
                    'hash': commit_hash,
                    'date': commit_date,
                    'message': full_message
                })

        # Build timeline result
        result = {
            'human_commit_count': len(human_commits),
            'ai_commit_count': len(ai_commits),
            'last_human_commit': human_commits[0]['date'] if human_commits else None,
            'last_ai_commit': ai_commits[0]['date'] if ai_commits else None,
            'human_to_ai_ratio': self._compute_ratio(len(human_commits), len(ai_commits))
        }

        return result

    def _compute_ratio(self, human_count: int, ai_count: int) -> float:
        """Compute human to AI ratio.

        Args:
            human_count: Number of human commits
            ai_count: Number of AI commits

        Returns:
            Ratio (human_count / (ai_count + 1)) to avoid division by zero
        """
        return human_count / (ai_count + 1)

    def _empty_timeline(self) -> Dict[str, Any]:
        """Return empty timeline (no commits or git unavailable).

        Returns:
            Timeline with zero counts
        """
        return {
            'human_commit_count': 0,
            'ai_commit_count': 0,
            'last_human_commit': None,
            'last_ai_commit': None,
            'human_to_ai_ratio': 0.0
        }


# ============================================================================
# GIT PROVENANCE COLLECTOR
# ============================================================================

class GitProvenanceCollector:
    """Collector for git provenance evidence."""

    def __init__(self, repo_root: Path):
        """Initialize collector.

        Args:
            repo_root: Path to git repository root
        """
        self.repo_root = Path(repo_root)

    def query_evidence(self, file_path: str, evidence_path: str) -> Any:
        """Query git provenance evidence for a file.

        Args:
            file_path: File path (relative to repo root)
            evidence_path: Evidence path (e.g., "provenance.git.timeline.human_commit_count")

        Returns:
            Evidence value
        """
        parser = GitLogParser(self.repo_root, file_path)
        timeline = parser.get_timeline()

        # Map evidence paths to timeline fields
        if evidence_path == "provenance.git.timeline.human_commit_count":
            return timeline['human_commit_count']

        elif evidence_path == "provenance.git.timeline.ai_commit_count":
            return timeline['ai_commit_count']

        elif evidence_path == "provenance.git.timeline.last_human_commit":
            return timeline['last_human_commit']

        elif evidence_path == "provenance.git.timeline.last_ai_commit":
            return timeline['last_ai_commit']

        elif evidence_path == "provenance.git.timeline.human_to_ai_ratio":
            return timeline['human_to_ai_ratio']

        else:
            return None


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python git_log_parser.py <repo_root> [file_path]")
        sys.exit(1)

    repo_root = Path(sys.argv[1])
    file_path = sys.argv[2] if len(sys.argv) > 2 else None

    parser = GitLogParser(repo_root, file_path)
    timeline = parser.get_timeline()

    print(f"\nGit Timeline Analysis")
    print(f"{'='*60}")
    if file_path:
        print(f"File: {file_path}")
    else:
        print(f"Repository: {repo_root}")
    print(f"{'='*60}\n")

    print(f"Human Commits: {timeline['human_commit_count']}")
    print(f"AI Commits: {timeline['ai_commit_count']}")
    print(f"Human/AI Ratio: {timeline['human_to_ai_ratio']:.2f}")

    if timeline['last_human_commit']:
        print(f"Last Human Commit: {timeline['last_human_commit']}")

    if timeline['last_ai_commit']:
        print(f"Last AI Commit: {timeline['last_ai_commit']}")

    print(f"\n{'='*60}\n")
