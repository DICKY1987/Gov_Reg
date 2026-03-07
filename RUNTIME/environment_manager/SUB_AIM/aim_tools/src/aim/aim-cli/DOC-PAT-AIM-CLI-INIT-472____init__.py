# DOC_LINK: DOC-PAT-AIM-CLI-INIT-472
"""Module: aim-cli

ULID Prefix: 01001A
Layer: api
Files: 1

This module dynamically imports ULID-prefixed files and re-exports their symbols.
Import from this module:

    from modules.aim_cli import function_name  # ?
"""
# DOC_ID: DOC-PAT-AIM-CLI-INIT-472

import importlib
import sys
from pathlib import Path

# Module metadata
__module_id__ = "aim-cli"
__ulid_prefix__ = "01001A"
__layer__ = "api"
module_import_name = "aim_cli"

# Dynamically import all ULID-prefixed files and re-export
_module_dir = Path(__file__).parent
_ulid_files = [
"m01001A_main",
]

_pending = list(_ulid_files)
_errors = {stem: None for stem in _pending}

while _pending:
    _progress = False
    for _file_stem in list(_pending):
        _module_path = f"modules.aim_cli.{_file_stem}"
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
                sys.modules[f"modules.aim_cli.{_alias}"] = _mod
                globals()[_alias] = _mod
            _pending.remove(_file_stem)
            _progress = True
        except Exception as e:
            _errors[_file_stem] = e
            continue
    if not _progress:
        for _file_stem in _pending:
            _module_path = f"modules.aim_cli.{_file_stem}"
            _err = _errors.get(_file_stem)
            print(f"Warning: Could not import {_module_path}: {_err}", file=sys.stderr)
        break
