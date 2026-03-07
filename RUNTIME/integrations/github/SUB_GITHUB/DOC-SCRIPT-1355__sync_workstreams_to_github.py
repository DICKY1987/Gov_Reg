# DOC_LINK: DOC-SCRIPT-1355
"""Compatibility shim for legacy sync_workstreams_to_github imports."""

from __future__ import annotations

from importlib import util
from pathlib import Path

_sub_root = Path(__file__).resolve().parent
_impl_path = (
    _sub_root
    / "DOC-CORE-SUB-GITHUB-SYNC-WORKSTREAMS-TO-GITHUB-769__sync_workstreams_to_github.py"
)

_spec = util.spec_from_file_location("sync_workstreams_to_github_impl", _impl_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load sync module from {_impl_path}")

_impl = util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

WorkstreamSyncEngine = _impl.WorkstreamSyncEngine
main = _impl.main
_emit_event = _impl._emit_event

__all__ = ["WorkstreamSyncEngine", "main", "_emit_event"]
