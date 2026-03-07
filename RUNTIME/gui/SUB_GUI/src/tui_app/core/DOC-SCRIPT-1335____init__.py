# DOC_LINK: DOC-SCRIPT-1335
"""Core TUI framework components."""

from __future__ import annotations

from .._docid_local import load_docid

_impl = load_docid(
    "tui_app/core/DOC-CORE-CORE-INIT-125____init__.py",
    "tui_app.core._impl",
)

__all__ = getattr(_impl, "__all__", [])
