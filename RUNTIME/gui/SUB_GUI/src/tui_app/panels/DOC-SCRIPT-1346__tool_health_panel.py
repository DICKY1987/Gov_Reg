# DOC_LINK: DOC-SCRIPT-1346
"""Shim for tool health panel module."""

from __future__ import annotations

from .._docid_local import load_docid

_impl = load_docid(
    "tui_app/panels/DOC-PAT-PANELS-TOOL-HEALTH-PANEL-468__tool_health_panel.py",
    "tui_app.panels.tool_health_panel_impl",
)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
globals().update({name: getattr(_impl, name) for name in __all__})
