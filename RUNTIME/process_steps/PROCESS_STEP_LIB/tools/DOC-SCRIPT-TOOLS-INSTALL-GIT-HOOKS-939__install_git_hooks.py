#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-INSTALL-GIT-HOOKS-939
"""
Install Git Hooks - Set up automatic pipeline runs on commit

Creates git hooks that automatically run the pipeline when source schemas
are modified and committed.

Usage:
    python install_git_hooks.py            # Install hooks
    python install_git_hooks.py --remove   # Remove hooks
"""
DOC_ID: DOC-SCRIPT-TOOLS-INSTALL-GIT-HOOKS-939

import sys
import os
from pathlib import Path
import shutil

# Add parent to path for imports
.parent.parent))
from DOC-SCRIPT-TOOLS-PFA-COMMON-944__pfa_common import print_success, print_error, print_warning, print_info

# Pre-commit hook content
PRE_COMMIT_HOOK = """#!/usr/bin/env python3
# Auto-generated git hook - Do not edit manually
# Regenerates pipeline when source schemas change

import sys
import subprocess
from pathlib import Path

def get_changed_files():
    \"\"\"Get list of files staged for commit\"\"\"
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split('\\n') if result.stdout else []

def main():
    changed_files = get_changed_files()

    # Check if any source schemas changed
    schema_changed = any(
        'schemas/source/' in f and f.endswith('.yaml')
        for f in changed_files
    )

    if not schema_changed:
        # No schema changes, allow commit
        return 0

    print("=" * 70)
    print("🔄 Source schemas changed - Auto-regenerating pipeline...")
    print("=" * 70)
    print()

    # Get repo root
    repo_root = Path(__file__).parent.parent.parent / 'PROCESS_STEP_LIB'
    tools_dir = repo_root / 'tools'

    # Run pipeline in quick mode
    result = subprocess.run(
        [sys.executable, str(tools_dir / 'pfa_run_pipeline.py'), '--quick'],
        cwd=str(tools_dir)
    )

    if result.returncode != 0:
        print()
        print("❌ Pipeline regeneration failed!")
        print("   Fix errors before committing.")
        return 1

    # Add generated files to commit
    generated_files = [
        'PROCESS_STEP_LIB/schemas/unified/PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml',
        'PROCESS_STEP_LIB/indices/master_index.json',
        'PROCESS_STEP_LIB/indices/merge_report.json',
        'PROCESS_STEP_LIB/guides/ALL_274_STEPS.md',
        'PROCESS_STEP_LIB/guides/ALL_274_STEPS_EXPLAINED.md'
    ]

    for f in generated_files:
        subprocess.run(['git', 'add', f], capture_output=True)

    print()
    print("✅ Pipeline regeneration complete!")
    print("   Generated files added to commit.")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
"""

def find_git_dir():
    """Find the .git directory"""
    current = Path(__file__).parent.parent  # Start at PROCESS_STEP_LIB

    # Walk up to find .git
    for _ in range(5):  # Check up to 5 levels
        git_dir = current / '.git'
        if git_dir.exists() and git_dir.is_dir():
            return git_dir
        current = current.parent

    return None

def install_hooks():
    """Install git hooks"""
    git_dir = find_git_dir()

    if not git_dir:
        print_error("Could not find .git directory")
        print("Make sure you're in a git repository")
        return False

    hooks_dir = git_dir / 'hooks'
    hooks_dir.mkdir(exist_ok=True)

    # Install pre-commit hook
    pre_commit_path = hooks_dir / 'pre-commit'

    # Backup existing hook if it exists
    if pre_commit_path.exists():
        backup_path = hooks_dir / 'pre-commit.backup'
        print_warning(f"Backing up existing pre-commit hook to {backup_path}")
        shutil.copy2(pre_commit_path, backup_path)

    # Write new hook
    pre_commit_path.write_text(PRE_COMMIT_HOOK, encoding='utf-8')

    # Make executable (on Unix-like systems)
    if os.name != 'nt':  # Not Windows
        os.chmod(pre_commit_path, 0o755)

    print_success(f"✅ Installed pre-commit hook: {pre_commit_path}")
    print()
    print("The hook will:")
    print("  1. Detect when source schemas change")
    print("  2. Auto-run pipeline regeneration")
    print("  3. Add generated files to your commit")
    print()
    print("To disable temporarily: git commit --no-verify")

    return True

def remove_hooks():
    """Remove git hooks"""
    git_dir = find_git_dir()

    if not git_dir:
        print_error("Could not find .git directory")
        return False

    hooks_dir = git_dir / 'hooks'
    pre_commit_path = hooks_dir / 'pre-commit'

    if not pre_commit_path.exists():
        print_warning("No pre-commit hook installed")
        return True

    # Check if it's our hook
    content = pre_commit_path.read_text(encoding='utf-8')
    if 'Auto-generated git hook' not in content:
        print_warning("Pre-commit hook exists but was not created by this script")
        print("Not removing it to be safe")
        return False

    # Remove hook
    pre_commit_path.unlink()
    print_success("✅ Removed pre-commit hook")

    # Restore backup if it exists
    backup_path = hooks_dir / 'pre-commit.backup'
    if backup_path.exists():
        print_info("Restoring previous hook from backup")
        shutil.copy2(backup_path, pre_commit_path)
        backup_path.unlink()
        print_success("✅ Restored previous hook")

    return True

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Install git hooks for automatic pipeline regeneration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install_git_hooks.py          # Install hooks
  python install_git_hooks.py --remove # Remove hooks

What the hooks do:
  - Watch for changes to schemas/source/*.yaml
  - Auto-run pfa_run_pipeline.py when schemas change
  - Add generated files to your commit
        """
    )

    parser.add_argument('--remove', action='store_true',
                        help='Remove installed git hooks')

    args = parser.parse_args()

    print("=" * 70)
    print("🔧 GIT HOOKS INSTALLER")
    print("=" * 70)
    print()

    if args.remove:
        success = remove_hooks()
    else:
        success = install_hooks()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
