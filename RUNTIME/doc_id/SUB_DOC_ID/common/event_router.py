# DOC_LINK: DOC-SCRIPT-1006
"""Compatibility shim for event_router."""

from __future__ import annotations

from importlib import util
from pathlib import Path

_module_dir = Path(__file__).resolve().parent
_impl_path = _module_dir / "DOC-SCRIPT-1006__event_router.py"

_spec = util.spec_from_file_location("event_router_impl", _impl_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load event router from {_impl_path}")

_impl = util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

EventRouter = _impl.EventRouter

__all__ = ["EventRouter"]
