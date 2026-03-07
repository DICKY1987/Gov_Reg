# DOC_LINK: DOC-SCRIPT-1347
"""UI core package shim."""

from __future__ import annotations

from ._docid_local import load_docid

_impl = load_docid(
    "ui_core/DOC-CORE-UI-CORE-INIT-300____init__.py",
    "ui_core._impl",
)

__all__ = getattr(_impl, "__all__", [])
