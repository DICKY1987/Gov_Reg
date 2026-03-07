# DOC_LINK: DOC-SCRIPT-1348
"""Local DOC_ID loader for ui_core."""

from __future__ import annotations

from importlib import util
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]


def load_docid(relative_path: str, module_name: str):
    module_path = SRC_DIR / relative_path
    spec = util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {module_path}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
