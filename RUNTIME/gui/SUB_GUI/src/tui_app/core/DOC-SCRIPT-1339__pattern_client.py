# DOC_LINK: DOC-SCRIPT-1339
"""Shim for TUI pattern client module."""

from __future__ import annotations

from .._docid_local import load_docid

_impl = load_docid(
    "tui_app/core/DOC-CORE-CORE-PATTERN-CLIENT-PATTERN-CLIENT-001__pattern_client.py",
    "tui_app.core.pattern_client_impl",
)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
globals().update({name: getattr(_impl, name) for name in __all__})
