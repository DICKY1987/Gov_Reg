#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TRIGGER_ID: TRIGGER-HOOK-INSTALL-PRE-COMMIT-HOOK-002
# DOC_LINK: DOC-SCRIPT-INSTALL-PRE-COMMIT-HOOK-008
"""
Install Pre-Commit Hook

PATTERN: EXEC-004 Atomic Operations
Ground Truth: Hook file exists and is executable

USAGE:
    python doc_id/install_pre_commit_hook.py
    python doc_id/install_pre_commit_hook.py --verify
"""

import argparse
import shutil
import sys
from pathlib import Path

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, MODULE_ROOT

HOOK_SOURCE = MODULE_ROOT / "3_AUTOMATION_HOOKS" / "pre_commit_hook.py"
HOOK_TARGET = REPO_ROOT / ".git" / "hooks" / "pre-commit"


def install_hook():
    """Install pre-commit hook"""
    # Verify source exists
    if not HOOK_SOURCE.exists():
        print(f"❌ Source not found: {HOOK_SOURCE}")
        sys.exit(1)

    # Create hooks directory if needed
    HOOK_TARGET.parent.mkdir(parents=True, exist_ok=True)

    # Backup existing hook
    if HOOK_TARGET.exists():
        backup = HOOK_TARGET.with_suffix('.backup')
        shutil.copy2(HOOK_TARGET, backup)
        print(f"📦 Backed up existing hook to {backup}")

    # Copy hook
    shutil.copy2(HOOK_SOURCE, HOOK_TARGET)

    # Make executable (Unix)
    if sys.platform != 'win32':
        HOOK_TARGET.chmod(0o755)

    # Verify
    if HOOK_TARGET.exists():
        print(f"✅ Pre-commit hook installed: {HOOK_TARGET}")
        return True
    else:
        print("❌ Installation failed")
        return False


def verify_hook():
    """Verify pre-commit hook is installed"""
    if HOOK_TARGET.exists():
        # Check if it's our hook
        try:
            content = HOOK_TARGET.read_text()
            if 'DOC_ID' in content or 'doc_id' in content:
                print(f"✅ Pre-commit hook verified: {HOOK_TARGET}")
                return True
            else:
                print(f"⚠️  Hook exists but may not be DOC_ID hook")
                return True
        except Exception:
            return HOOK_TARGET.exists()
    else:
        print(f"❌ Pre-commit hook not found: {HOOK_TARGET}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Install Pre-Commit Hook")
    parser.add_argument('--verify', action='store_true',
                       help='Verify hook is installed')
    args = parser.parse_args()

    if args.verify:
        success = verify_hook()
        sys.exit(0 if success else 1)

    success = install_hook()

    # Verify installation
    if verify_hook():
        print("✅ Installation complete and verified")
        sys.exit(0)
    else:
        print("❌ Installation failed verification")
        sys.exit(1)


if __name__ == '__main__':
    main()
