# DOC_LINK: DOC-SCRIPT-1336
"""Shim for TUI layout manager module."""

from __future__ import annotations

from .._docid_local import load_docid

_impl = load_docid(
    "tui_app/core/DOC-CORE-CORE-LAYOUT-MANAGER-119__layout_manager.py",
    "tui_app.core.layout_manager_impl",
)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
globals().update({name: getattr(_impl, name) for name in __all__})
