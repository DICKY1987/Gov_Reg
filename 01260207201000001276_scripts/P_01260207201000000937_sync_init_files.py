#!/usr/bin/env python3
"""
Sync __init__.py files from P_-prefixed sources.

Usage:
    python scripts/sync_init_files.py [--dry-run] [--check]
"""

import sys
import argparse
from pathlib import Path
import re

REPO_ROOT = Path(__file__).parent.parent
TEMPLATE = '''"""
Package initialization - Auto-generated from P_-prefixed source.

Source: {p_filename}
Auto-generated: DO NOT EDIT
"""

from .{p_module_name} import *

try:
    from .{p_module_name} import __all__
except ImportError:
    pass
'''

def find_p_init_files(root: Path) -> list[tuple[Path, Path]]:
    """Find all P_*___init__.py files and their target __init__.py paths."""
    results = []
    seen_targets = set()
    pattern = re.compile(r'P_\d+.*___init__\.py$')

    for p_init in root.rglob('P_*___init__.py'):
        # Skip archived files
        if any(part.lower().startswith('archive') for part in p_init.parts):
            continue
        
        if pattern.match(p_init.name):
            init_path = p_init.parent / '__init__.py'
            
            # Skip duplicates (happens when both P_ and regular __init__.py exist)
            if init_path in seen_targets:
                continue
            
            seen_targets.add(init_path)
            results.append((p_init, init_path))

    return results

def sync_init_file(p_init: Path, init_path: Path, dry_run: bool = False) -> bool:
    """Create or update __init__.py from P_-prefixed source."""
    p_filename = p_init.name
    p_module_name = p_filename.replace('.py', '')

    expected_content = TEMPLATE.format(
        p_filename=p_filename,
        p_module_name=p_module_name
    )

    if init_path.exists():
        with open(init_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        if current_content == expected_content:
            return False  # Already in sync

    if not dry_run:
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(expected_content)

    return True

def main():
    parser = argparse.ArgumentParser(description='Sync __init__.py files')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    p_init_files = find_p_init_files(REPO_ROOT)
    print(f"Found {len(p_init_files)} P_*___init__.py files")

    changes = []
    for p_init, init_path in p_init_files:
        if sync_init_file(p_init, init_path, dry_run=args.dry_run or args.check):
            changes.append(init_path.relative_to(REPO_ROOT))

    if changes:
        action = 'Would create/update' if args.dry_run or args.check else 'Created/updated'
        print(f"\n{action} {len(changes)} files:")
        for path in changes:
            print(f"  {path}")
        return 1 if args.check else 0

    print("\n✓ All __init__.py files are in sync")
    return 0

if __name__ == '__main__':
    sys.exit(main())
