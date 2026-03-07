# DOC_LINK: DOC-PAT-AIM-ENVIRONMENT-INIT-480
"""Module: aim-environment

ULID Prefix: 01001B
Layer: api
Files: 7

This module dynamically imports ULID-prefixed files and re-exports their symbols.
Import from this module:

    from modules.aim_environment import function_name  # ?
"""
# DOC_ID: DOC-PAT-AIM-ENVIRONMENT-INIT-480

import importlib
import sys
from pathlib import Path

# Module metadata
__module_id__ = "aim-environment"
__ulid_prefix__ = "01001B"
__layer__ = "api"
module_import_name = "aim_environment"

# Dynamically import all ULID-prefixed files and re-export
_module_dir = Path(__file__).parent
_ulid_files = [
"m01001B_audit",
"m01001B_exceptions",
"m01001B_health",
"m01001B_installer",
"m01001B_scanner",
"m01001B_secrets",
"m01001B_version_control",
]

_pending = list(_ulid_files)
_errors = {stem: None for stem in _pending}

while _pending:
    _progress = False
    for _file_stem in list(_pending):
        _module_path = f"modules.aim_environment.{_file_stem}"
        try:
            _mod = importlib.import_module(_module_path)

            # Re-export all public symbols
            if hasattr(_mod, '__all__'):
                for _name in _mod.__all__:
                    globals()[_name] = getattr(_mod, _name)
            else:
                # Export everything that doesn't start with underscore
                for _name in dir(_mod):
                    if not _name.startswith('_'):
                        globals()[_name] = getattr(_mod, _name)
            # Alias without ULID prefix to support relative imports (e.g., db_sqlite)
            if "_" in _file_stem:
                _alias = _file_stem.split("_", 1)[1]
                sys.modules[f"modules.aim_environment.{_alias}"] = _mod
                globals()[_alias] = _mod
            _pending.remove(_file_stem)
            _progress = True
        except Exception as e:
            _errors[_file_stem] = e
            continue
    if not _progress:
        for _file_stem in _pending:
            _module_path = f"modules.aim_environment.{_file_stem}"
            _err = _errors.get(_file_stem)
            print(f"Warning: Could not import {_module_path}: {_err}", file=sys.stderr)
        break
