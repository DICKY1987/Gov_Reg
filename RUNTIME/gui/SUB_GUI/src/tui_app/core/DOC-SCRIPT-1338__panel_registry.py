# DOC_LINK: DOC-SCRIPT-1338
"""Shim for TUI panel registry module."""

from __future__ import annotations

from .._docid_local import load_docid

_impl = load_docid(
    "tui_app/core/DOC-CORE-CORE-PANEL-REGISTRY-121__panel_registry.py",
    "tui_app.core.panel_registry_impl",
)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
globals().update({name: getattr(_impl, name) for name in __all__})

# Trigger panel registration so registry is populated for tests.
try:
    import tui_app.panels  # noqa: F401
except Exception:
    pass
