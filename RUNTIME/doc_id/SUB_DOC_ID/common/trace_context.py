# DOC_LINK: DOC-CORE-SSOT-SYS-TOOLS-TRACE-CONTEXT-1108
"""Compatibility shim for trace_context."""

from __future__ import annotations

from importlib import util
from pathlib import Path

_module_dir = Path(__file__).resolve().parent
_impl_path = _module_dir / "DOC-CORE-SSOT-SYS-TOOLS-TRACE-CONTEXT-1108__trace_context.py"

_spec = util.spec_from_file_location("trace_context_impl", _impl_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load trace_context from {_impl_path}")

_impl = util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

if hasattr(_impl, "__all__"):
    for _name in _impl.__all__:
        globals()[_name] = getattr(_impl, _name)
    __all__ = list(_impl.__all__)
else:
    for _name, _value in _impl.__dict__.items():
        if not _name.startswith("_"):
            globals()[_name] = _value
    __all__ = [name for name in globals() if not name.startswith("_")]
