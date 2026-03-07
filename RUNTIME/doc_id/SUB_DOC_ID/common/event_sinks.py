# DOC_LINK: DOC-SCRIPT-1007
"""Compatibility shim for event_sinks."""

from __future__ import annotations

from importlib import util
from pathlib import Path

_module_dir = Path(__file__).resolve().parent
_impl_path = _module_dir / "DOC-SCRIPT-1007__event_sinks.py"

_spec = util.spec_from_file_location("event_sinks_impl", _impl_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load event sinks from {_impl_path}")

_impl = util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

JSONLSink = _impl.JSONLSink
ConsoleSink = _impl.ConsoleSink
MemorySink = _impl.MemorySink

__all__ = ["JSONLSink", "ConsoleSink", "MemorySink"]
