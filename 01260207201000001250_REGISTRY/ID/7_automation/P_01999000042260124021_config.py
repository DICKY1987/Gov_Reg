"""Configuration shim — re-exports from govreg_core canonical location.
FILE_ID: P_01999000042260124021

The canonical implementation lives at:
  ../../../../01260207201000001173_govreg_core/P_01999000042260124021_config.py

This shim exists so that scanner.py (ID/7_automation/P_01999000042260124023_scanner.py)
can resolve the config via a relative path import.
"""
import importlib.util
from pathlib import Path

_canonical = Path(__file__).parent.parent.parent.parent / \
    "01260207201000001173_govreg_core" / "P_01999000042260124021_config.py"

_spec = importlib.util.spec_from_file_location("_config_canonical", _canonical)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

load_json_file = _mod.load_json_file
save_json_file = _mod.save_json_file
load_repo_roots = _mod.load_repo_roots
load_registry = _mod.load_registry
load_schema = _mod.load_schema
resolve_path = _mod.resolve_path
normalize_path = _mod.normalize_path
