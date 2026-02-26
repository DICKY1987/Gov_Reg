# DOC_LINK: DOC-SCRIPT-1236
"""Compatibility shim for ai_cli_provenance_collector."""

from __future__ import annotations

from _docid_loader import load_docid

_impl = load_docid("DOC-SCRIPT-1011__PROV-SOL_ai_cli_provenance_collector.py", "ai_cli_provenance_solution.ai_cli_provenance_collector_impl")

if hasattr(_impl, "__all__"):
    for _name in _impl.__all__:
        globals()[_name] = getattr(_impl, _name)
    __all__ = list(_impl.__all__)
else:
    for _name, _value in _impl.__dict__.items():
        if not _name.startswith("_"):
            globals()[_name] = _value
    __all__ = [name for name in globals() if not name.startswith("_")]
