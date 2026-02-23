"""Path safety helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple


def _norm_case(path: Path) -> str:
    return os.path.normcase(str(path))


def resolve_under_root(path_str: str, repo_root: str) -> Tuple[Path, bool]:
    root = Path(repo_root).resolve()
    raw_path = Path(path_str).expanduser()
    if not raw_path.is_absolute():
        raw_path = root / raw_path
    candidate = raw_path.resolve()
    try:
        common = os.path.commonpath([_norm_case(root), _norm_case(candidate)])
    except ValueError:
        return candidate, False
    return candidate, common == _norm_case(root)
