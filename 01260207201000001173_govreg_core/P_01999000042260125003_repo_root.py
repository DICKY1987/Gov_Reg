"""
Repository Root Detection

Provides robust repo root resolution for gates and tools.
Works correctly whether run from:
- Repository subdirectories
- .git/hooks/ (pre-commit hook)
- Any arbitrary working directory

Contract: docs/ID_IDENTITY_CONTRACT.md
"""

import subprocess
from pathlib import Path
from typing import Optional


def get_repo_root() -> Path:
    """
    Determine repository root using git-aware detection.
    
    Strategy:
    1. Try `git rev-parse --show-toplevel` (most reliable)
    2. Fall back to walking upward to find .git/
    3. Raise error if not in a git repository
    
    Returns:
        Path object pointing to repository root
        
    Raises:
        RuntimeError: If not in a git repository
    """
    # Strategy 1: Use git command (most reliable)
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        repo_root = Path(result.stdout.strip())
        if repo_root.exists():
            return repo_root
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Strategy 2: Walk upward to find .git/
    current = Path.cwd().resolve()
    for parent in [current] + list(current.parents):
        git_dir = parent / '.git'
        if git_dir.exists():
            return parent
    
    # Not in a git repository
    raise RuntimeError(
        "Not in a git repository. "
        "This tool must be run from within a git repository."
    )


def get_repo_root_safe(default: Optional[Path] = None) -> Optional[Path]:
    """
    Get repository root without raising exceptions.
    
    Args:
        default: Value to return if not in a git repository
        
    Returns:
        Path to repo root or default value
    """
    try:
        return get_repo_root()
    except RuntimeError:
        return default


def is_in_git_repo() -> bool:
    """
    Check if current directory is within a git repository.
    
    Returns:
        True if in a git repository
    """
    return get_repo_root_safe() is not None
