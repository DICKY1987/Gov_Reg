"""IDPKG CLI wrapper."""
from __future__ import annotations

from pathlib import Path
import sys

MODULE_DIR = Path(__file__).parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from P_01999000042260126000__idpkg_runtime import main as idpkg_main


if __name__ == "__main__":
    raise SystemExit(idpkg_main())
