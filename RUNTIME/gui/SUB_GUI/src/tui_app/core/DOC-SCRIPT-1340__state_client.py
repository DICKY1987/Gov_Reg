# DOC_LINK: DOC-SCRIPT-1340
"""Shim for TUI state client module."""

from __future__ import annotations

from .._docid_local import load_docid

_impl = load_docid(
    "tui_app/core/DOC-CORE-CORE-STATE-CLIENT-STATE-CLIENT-001__state_client.py",
    "tui_app.core.state_client_impl",
)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
globals().update({name: getattr(_impl, name) for name in __all__})
