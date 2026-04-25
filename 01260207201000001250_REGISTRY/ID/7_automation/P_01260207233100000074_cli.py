"""IDPKG CLI wrapper."""
from __future__ import annotations

from pathlib import Path
import sys

MODULE_DIR = Path(__file__).parent
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = PROJECT_ROOT / "ID" / "1_runtime"
WATCHERS_PATH = RUNTIME_ROOT / "watchers"

for import_path in (MODULE_DIR, RUNTIME_ROOT, WATCHERS_PATH):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from P_01999000042260126000__idpkg_runtime import main as idpkg_main


if __name__ == "__main__":
    raise SystemExit(idpkg_main())
