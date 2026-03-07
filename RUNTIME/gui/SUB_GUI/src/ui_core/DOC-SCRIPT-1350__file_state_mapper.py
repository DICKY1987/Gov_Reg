# DOC_LINK: DOC-SCRIPT-1350
"""Shim for ui_core file state mapper module."""

from __future__ import annotations

from ._docid_local import load_docid

_impl = load_docid(
    "ui_core/DOC-CORE-UI-CORE-FILE-STATE-MAPPER-780__file_state_mapper.py",
    "ui_core.file_state_mapper_impl",
)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
globals().update({name: getattr(_impl, name) for name in __all__})
