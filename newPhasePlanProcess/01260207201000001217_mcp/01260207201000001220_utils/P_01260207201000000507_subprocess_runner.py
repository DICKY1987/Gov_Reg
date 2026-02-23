"""Subprocess runner with timeout support."""

from __future__ import annotations

import subprocess
import sys
from typing import List, Tuple


def run_command(args: List[str], timeout_s: int) -> Tuple[int, str, str]:
    completed = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def python_executable() -> str:
    return sys.executable
