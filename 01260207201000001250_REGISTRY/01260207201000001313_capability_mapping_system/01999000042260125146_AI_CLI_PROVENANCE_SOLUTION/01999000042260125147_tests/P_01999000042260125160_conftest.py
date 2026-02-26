# DOC_LINK: DOC-TEST-1242
"""Pytest config for AI_CLI_PROVENANCE_SOLUTION tests."""

from __future__ import annotations

from importlib import util
from pathlib import Path
import sys

SOLUTION_ROOT = Path(__file__).resolve().parents[1]
if str(SOLUTION_ROOT) not in sys.path:
    sys.path.insert(0, str(SOLUTION_ROOT))

_docid_path = SOLUTION_ROOT / "DOC-TEST-PROVENANCE-001__PROV-SOL_conftest.py"
_spec = util.spec_from_file_location("ai_cli_prov_tests_docid_conftest", _docid_path)
if _spec and _spec.loader:
    _module = util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    for _name, _value in _module.__dict__.items():
        if not _name.startswith("_"):
            globals()[_name] = _value
