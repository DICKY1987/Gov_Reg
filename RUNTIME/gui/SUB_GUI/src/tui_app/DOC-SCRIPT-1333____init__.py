# DOC_LINK: DOC-SCRIPT-1333
"""TUI app package shim."""

from __future__ import annotations

from ._docid_local import load_docid

_impl = load_docid(
    "tui_app/DOC-PAT-TUI-APP-INIT-463____init__.py",
    "tui_app._impl",
)

__all__ = getattr(_impl, "__all__", [])
