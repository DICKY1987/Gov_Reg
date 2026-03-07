# DOC_LINK: DOC-SCRIPT-1341
"""TUI panels package shim."""

from __future__ import annotations

from .._docid_local import load_docid

_impl = load_docid(
    "tui_app/panels/DOC-PAT-PANELS-INIT-469____init__.py",
    "tui_app.panels._impl",
)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
globals().update({name: getattr(_impl, name) for name in __all__})
