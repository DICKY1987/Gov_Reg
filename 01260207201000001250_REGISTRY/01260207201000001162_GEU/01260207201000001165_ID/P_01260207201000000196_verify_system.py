#!/usr/bin/env python3
"""IDPKG system verification runner."""
from __future__ import annotations

from pathlib import Path
import json
import sys

repo_root = Path(__file__).parent
core_path = repo_root / "01260207201000001173_govreg_core"
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))

from P_01999000042260126000__idpkg_runtime import IdpkgEngine


def main() -> int:
    engine = IdpkgEngine()
    result = engine.verify()
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
