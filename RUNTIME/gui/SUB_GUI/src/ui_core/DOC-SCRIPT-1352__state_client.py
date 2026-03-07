# DOC_LINK: DOC-SCRIPT-1352
"""Shim for ui_core state client module."""

from __future__ import annotations

from ._docid_local import load_docid

_impl = load_docid(
    "ui_core/DOC-CORE-CORE-STATE-CLIENT-124__state_client.py",
    "ui_core.state_client_impl",
)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
globals().update({name: getattr(_impl, name) for name in __all__})
