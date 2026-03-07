# DOC_LINK: DOC-TEST-1353
"""Pytest config for SUB_GUI tests."""

from __future__ import annotations

from pathlib import Path
import sys

TESTS_DIR = Path(__file__).resolve().parent
SRC_DIR = TESTS_DIR.parent / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
