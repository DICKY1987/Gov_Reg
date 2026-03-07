# DOC_LINK: DOC-SCRIPT-1354
"""Compatibility shim for legacy git_adapter imports."""

from __future__ import annotations

from importlib import util
from pathlib import Path

_sub_root = Path(__file__).resolve().parent
_impl_path = (
    _sub_root
    / "sync-pipeline"
    / "FILE_WATTCH_GIT_PIPE"
    / "DOC-CORE-FILE-WATTCH-GIT-PIPE-GIT-ADAPTER-1182__git_adapter.py"
)

_spec = util.spec_from_file_location("git_adapter_impl", _impl_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load git adapter from {_impl_path}")

_impl = util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

GitError = _impl.GitError
_emit_event = _impl._emit_event
_run_git = _impl._run_git
is_repo = _impl.is_repo
init_repo = _impl.init_repo
set_remote = _impl.set_remote
get_branch = _impl.get_branch
checkout_branch = _impl.checkout_branch
add = _impl.add
staged_summary = _impl.staged_summary
commit = _impl.commit
push = _impl.push
pull = _impl.pull
list_conflicts = _impl.list_conflicts

__all__ = [
    "GitError",
    "_emit_event",
    "_run_git",
    "is_repo",
    "init_repo",
    "set_remote",
    "get_branch",
    "checkout_branch",
    "add",
    "staged_summary",
    "commit",
    "push",
    "pull",
    "list_conflicts",
]
