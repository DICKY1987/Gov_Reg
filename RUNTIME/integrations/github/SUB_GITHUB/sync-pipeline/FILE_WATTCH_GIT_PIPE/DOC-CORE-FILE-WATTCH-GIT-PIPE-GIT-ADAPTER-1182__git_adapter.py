# DOC_LINK: DOC-CORE-FILE-WATTCH-GIT-PIPE-GIT-ADAPTER-1182
from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

# Event emission (Phase 4: Observability)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
try:
    from event_emitter import get_event_emitter
    EVENT_SYSTEM_AVAILABLE = True
except ImportError:
    EVENT_SYSTEM_AVAILABLE = False
    def get_event_emitter():
        return None

def _emit_event(subsystem: str, step_id: str, subject: str, summary: str,
                severity: str = "INFO", details: dict = None):
    """Helper to emit events with graceful degradation if event system unavailable."""
    if EVENT_SYSTEM_AVAILABLE:
        try:
            emitter = get_event_emitter()
            if emitter:
                emitter.emit(
                    subsystem=subsystem,
                    step_id=step_id,
                    subject=subject,
                    summary=summary,
                    severity=severity,
                    details=details or {}
                )
        except Exception:
            pass  # Gracefully degrade if event system fails


class GitError(RuntimeError):
    pass


def _run_git(repo_path: str, args: List[str], timeout: float = 15.0) -> Tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def is_repo(repo_path: str) -> bool:
    return Path(repo_path, ".git").exists()


def init_repo(repo_path: str) -> None:
    code, out, err = _run_git(repo_path, ["init"])
    if code != 0:
        raise GitError(err or out)


def set_remote(repo_path: str, name: str, url: str) -> None:
    # Try set-url first, then add
    code, out, err = _run_git(repo_path, ["remote", "set-url", name, url])
    if code != 0:
        code, out, err = _run_git(repo_path, ["remote", "add", name, url])
        if code != 0 and "already exists" not in err:
            raise GitError(err or out)


def get_branch(repo_path: str) -> str:
    code, out, err = _run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
    if code != 0:
        raise GitError(err or out)
    return out


def checkout_branch(repo_path: str, branch: str, create: bool = False) -> None:
    args = ["checkout"] + (["-b", branch] if create else [branch])
    code, out, err = _run_git(repo_path, args)
    if code != 0:
        raise GitError(err or out)


def add(repo_path: str, paths: List[str]) -> None:
    if not paths:
        return
    code, out, err = _run_git(repo_path, ["add", "--", *paths])
    if code != 0:
        raise GitError(err or out)


def staged_summary(repo_path: str) -> List[str]:
    code, out, err = _run_git(repo_path, ["diff", "--cached", "--name-only"])
    if code != 0:
        raise GitError(err or out)
    return [line for line in out.splitlines() if line.strip()]


def commit(repo_path: str, message: str, sign: bool = False) -> Optional[str]:
    _emit_event(
        subsystem="SUB_GITHUB",
        step_id="GIT_COMMIT_STARTED",
        subject=repo_path,
        summary=f"Starting git commit: {message[:50]}...",
        severity="INFO",
        details={"repo_path": repo_path, "message": message, "sign": sign}
    )

    args = ["commit", "-m", message]
    if sign:
        args.append("-S")
    code, out, err = _run_git(repo_path, args)
    if code != 0:
        # No changes to commit is not fatal
        if "nothing to commit" in (out + err).lower():
            _emit_event(
                subsystem="SUB_GITHUB",
                step_id="GIT_COMMIT_SKIPPED",
                subject=repo_path,
                summary="No changes to commit",
                severity="INFO",
                details={"repo_path": repo_path}
            )
            return None
        _emit_event(
            subsystem="SUB_GITHUB",
            step_id="GIT_COMMIT_FAILED",
            subject=repo_path,
            summary=f"Commit failed: {err or out}",
            severity="ERROR",
            details={"repo_path": repo_path, "error": err or out}
        )
        raise GitError(err or out)
    # Return new commit sha
    code, out, err = _run_git(repo_path, ["rev-parse", "HEAD"])
    if code != 0:
        return None

    _emit_event(
        subsystem="SUB_GITHUB",
        step_id="GIT_COMMIT_COMPLETED",
        subject=repo_path,
        summary=f"Commit completed: {out[:8]}",
        severity="INFO",
        details={"repo_path": repo_path, "commit_sha": out, "message": message}
    )
    return out


def push(repo_path: str, remote: str, branch: str, force: bool = False) -> None:
    _emit_event(
        subsystem="SUB_GITHUB",
        step_id="GIT_PUSH_STARTED",
        subject=f"{repo_path}:{branch}",
        summary=f"Pushing to {remote}/{branch}",
        severity="INFO",
        details={"repo_path": repo_path, "remote": remote, "branch": branch, "force": force}
    )

    args = ["push", remote, branch]
    if force:
        args.insert(1, "--force-with-lease")
    code, out, err = _run_git(repo_path, args, timeout=60.0)
    if code != 0:
        _emit_event(
            subsystem="SUB_GITHUB",
            step_id="GIT_PUSH_FAILED",
            subject=f"{repo_path}:{branch}",
            summary=f"Push failed: {err or out}",
            severity="ERROR",
            details={"repo_path": repo_path, "remote": remote, "branch": branch, "error": err or out}
        )
        raise GitError(err or out)

    _emit_event(
        subsystem="SUB_GITHUB",
        step_id="GIT_PUSH_COMPLETED",
        subject=f"{repo_path}:{branch}",
        summary=f"Push completed to {remote}/{branch}",
        severity="INFO",
        details={"repo_path": repo_path, "remote": remote, "branch": branch}
    )


def pull(repo_path: str, remote: str, branch: str) -> None:
    _emit_event(
        subsystem="SUB_GITHUB",
        step_id="GIT_PULL_STARTED",
        subject=f"{repo_path}:{branch}",
        summary=f"Pulling from {remote}/{branch}",
        severity="INFO",
        details={"repo_path": repo_path, "remote": remote, "branch": branch}
    )

    code, out, err = _run_git(repo_path, ["pull", remote, branch], timeout=120.0)
    if code != 0:
        # Not fatal for MVP; pull may fail if no tracking or conflicts
        _emit_event(
            subsystem="SUB_GITHUB",
            step_id="GIT_PULL_FAILED",
            subject=f"{repo_path}:{branch}",
            summary=f"Pull failed: {err or out}",
            severity="ERROR",
            details={"repo_path": repo_path, "remote": remote, "branch": branch, "error": err or out}
        )
        raise GitError(err or out)

    _emit_event(
        subsystem="SUB_GITHUB",
        step_id="GIT_PULL_COMPLETED",
        subject=f"{repo_path}:{branch}",
        summary=f"Pull completed from {remote}/{branch}",
        severity="INFO",
        details={"repo_path": repo_path, "remote": remote, "branch": branch}
    )


def list_conflicts(repo_path: str) -> List[str]:
    # Use diff-filter=U to list unmerged files
    code, out, err = _run_git(repo_path, ["diff", "--name-only", "--diff-filter=U"])
    if code != 0:
        return []
    return [line for line in out.splitlines() if line.strip()]
