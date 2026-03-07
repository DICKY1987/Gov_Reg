# DOC_LINK: DOC-SCRIPT-1325
"""Compatibility shim for id_core imports."""

from __future__ import annotations

from importlib import util
from pathlib import Path

_module_dir = Path(__file__).resolve().parent
_impl_path = _module_dir / "DOC-CORE-ID-SHARED-LIBRARY-001__id_core.py"

_spec = util.spec_from_file_location("id_core_impl", _impl_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load id_core from {_impl_path}")

_impl = util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

if hasattr(_impl, "__all__"):
    for _name in _impl.__all__:
        globals()[_name] = getattr(_impl, _name)
    __all__ = list(_impl.__all__)
else:
    for _name, _value in _impl.__dict__.items():
        if not _name.startswith("_"):
            globals()[_name] = _value
    __all__ = [name for name in globals() if not name.startswith("_")]
