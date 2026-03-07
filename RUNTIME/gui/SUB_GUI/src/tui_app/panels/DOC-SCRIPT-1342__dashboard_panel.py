# DOC_LINK: DOC-SCRIPT-1342
"""Shim for dashboard panel module."""

from __future__ import annotations

from .._docid_local import load_docid

_impl = load_docid(
    "tui_app/panels/DOC-PAT-PANELS-DASHBOARD-PANEL-464__dashboard_panel.py",
    "tui_app.panels.dashboard_panel_impl",
)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
globals().update({name: getattr(_impl, name) for name in __all__})
