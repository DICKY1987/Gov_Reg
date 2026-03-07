# DOC_LINK: DOC-SCRIPT-1337
"""Shim for TUI panel plugin module."""

from __future__ import annotations

from .._docid_local import load_docid

_impl = load_docid(
    "tui_app/core/DOC-CORE-CORE-PANEL-PLUGIN-120__panel_plugin.py",
    "tui_app.core.panel_plugin_impl",
)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
globals().update({name: getattr(_impl, name) for name in __all__})
