"""
Root pytest configuration - Centralizes sys.path setup.

This ensures consistent module resolution across all test files.
Automatically loaded by pytest before any tests run.
"""

import sys
from pathlib import Path

# Repository root (where this conftest.py lives)
REPO_ROOT = Path(__file__).parent

# Add root to path (for govreg_core, config, validators)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Add src/ to path (for registry_transition, registry_writer, etc.)
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

def pytest_configure(config):
    """Verify import environment at startup."""
    try:
        import govreg_core
        from registry_transition import LifecycleState
        print("✓ Import environment configured successfully")
    except ImportError as e:
        print(f"✗ Import verification failed: {e}")
        print(f"  REPO_ROOT: {REPO_ROOT}")
        print(f"  SRC_DIR: {SRC_DIR}")
        raise
