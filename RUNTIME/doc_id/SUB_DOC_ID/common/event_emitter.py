# DOC_LINK: DOC-CORE-SSOT-SYS-TOOLS-EVENT-EMITTER-1109
"""Compatibility shim for event_emitter."""

from __future__ import annotations

from importlib import util
from pathlib import Path

_module_dir = Path(__file__).resolve().parent
_impl_path = _module_dir / "DOC-CORE-SSOT-SYS-TOOLS-EVENT-EMITTER-1109__event_emitter.py"

_spec = util.spec_from_file_location("event_emitter_impl", _impl_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load event emitter from {_impl_path}")

_impl = util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

AsyncEventEmitter = _impl.AsyncEventEmitter
EventSeverity = _impl.EventSeverity
generate_ulid = _impl.generate_ulid
set_global_emitter = _impl.set_global_emitter
get_event_emitter = _impl.get_event_emitter

__all__ = [
    "AsyncEventEmitter",
    "EventSeverity",
    "generate_ulid",
    "set_global_emitter",
    "get_event_emitter",
]
