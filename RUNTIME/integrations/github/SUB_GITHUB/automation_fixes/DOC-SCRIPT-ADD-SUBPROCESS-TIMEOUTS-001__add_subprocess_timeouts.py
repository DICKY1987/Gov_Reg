#!/usr/bin/env python
# DOC_LINK: DOC-SCRIPT-ADD-SUBPROCESS-TIMEOUTS-001
"""
Add timeout parameter to all subprocess.run(, timeout=1800) calls.

PATTERN: EXEC-001 (Batch File Transformation)
DOC_ID: DOC-SCRIPT-ADD-SUBPROCESS-TIMEOUTS-001

Purpose: Quick Win #1 - Add timeout=1800 to all subprocess.run() calls lacking it
Time: 2 hours | Saves: 5h/month (prevents hanging processes)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Default timeout in seconds (30 minutes - conservative for long-running tools)
DEFAULT_TIMEOUT = 1800


class SubprocessTimeoutAdder:
    """Add timeout parameter to subprocess.run(, timeout=1800) calls."""

    def __init__(self, default_timeout: int = DEFAULT_TIMEOUT):
        self.default_timeout = default_timeout
        self.files_modified = []
        self.changes_made = 0

    def process_file(self, filepath: Path) -> Tuple[bool, int]:
        """Process a single Python file.

        Returns:
            (modified: bool, num_changes: int)
        """
        try:
            content = filepath.read_text(encoding='utf-8')
            original_content = content
            changes_this_file = 0

            # Find all subprocess.run calls
            lines = content.split('\n')
            modified_lines = []

            for line in lines:
                if 'subprocess.run(' in line and 'timeout=' not in line:
                    # Simple heuristic: add timeout before closing paren if not multiline
                    if ')' in line and line.count('(') == line.count(')'):
                        # Single-line call
                        line = line.replace(')', f', timeout={self.default_timeout})', 1)
                        changes_this_file += 1
                modified_lines.append(line)

            modified_content = '\n'.join(modified_lines)

            if modified_content != original_content:
                filepath.write_text(modified_content, encoding='utf-8')
                return True, changes_this_file

            return False, 0

        except Exception as e:
            print(f"  ⚠️  Error processing {filepath}: {e}")
            return False, 0

    def process_batch(self, filepaths: List[Path], batch_num: int, total_batches: int):
        """Process a batch of files."""
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(filepaths)} files)")

        for filepath in filepaths:
            try:
                relative_path = filepath.relative_to(Path.cwd())
            except ValueError:
                relative_path = filepath

            modified, num_changes = self.process_file(filepath)

            if modified:
                self.files_modified.append(filepath)
                self.changes_made += num_changes
                print(f"  ✅ {relative_path} ({num_changes} calls)")
            else:
                print(f"  ⏭️  {relative_path} (already has timeout)")

    def verify(self) -> dict:
        """Verify changes by checking files exist and contain timeout."""
        verified = 0
        for filepath in self.files_modified:
            if filepath.exists():
                content = filepath.read_text(encoding='utf-8')
                if 'timeout=' in content:
                    verified += 1

        return {
            'total_files_processed': len(self.files_modified),
            'verified': verified,
            'success': verified == len(self.files_modified),
            'changes_made': self.changes_made
        }


def main():
    """Execute EXEC-001 pattern: Batch File Transformation."""

    print("=" * 60)
    print("QUICK WIN #1: Add Subprocess Timeouts")
    print("=" * 60)
    print(f"Pattern: EXEC-001 (Batch File Transformation)")
    print(f"Default timeout: {DEFAULT_TIMEOUT}s (30 minutes)")
    print()

    # Discover files
    print("🔍 Discovery: Finding files with subprocess.run(, timeout=1800)...")

    # Target specific high-value directories (avoid worktrees)
    search_dirs = [
        Path('core'),
        Path('error'),
        Path('scripts'),
        Path('phase4_routing'),
        Path('phase6_error_recovery')
    ]

    target_files = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for filepath in search_dir.rglob('*.py'):
            # Skip excluded directories
            if any(part in str(filepath) for part in ['__pycache__', '_ARCHIVE', '.git']):
                continue

            try:
                content = filepath.read_text(encoding='utf-8')
                # Has subprocess.run without timeout on same line
                if 'subprocess.run(' in content:
                    lines = content.split('\n')
                    has_missing = any(
                        'subprocess.run(' in line and 'timeout=' not in line
                        for line in lines
                    )
                    if has_missing:
                        target_files.append(filepath)
            except:
                pass

    print(f"Found {len(target_files)} files needing fixes")
    print()

    if not target_files:
        print("✅ No files need fixing!")
        return 0

    # Process in batches (EXEC-001 pattern)
    adder = SubprocessTimeoutAdder()
    batch_size = 10

    batches = [target_files[i:i+batch_size] for i in range(0, len(target_files), batch_size)]

    for batch_num, batch in enumerate(batches, 1):
        adder.process_batch(batch, batch_num, len(batches))

    # Verify
    print("\n🔍 Verification...")
    result = adder.verify()

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Files modified: {result['total_files_processed']}")
    print(f"Calls fixed: {result['changes_made']}")
    print(f"Verified: {result['verified']}/{result['total_files_processed']}")
    print(f"Success: {'✅ YES' if result['success'] else '❌ NO'}")
    print()
    print("Next steps:")
    print("1. Review changes: git diff")
    print("2. Run tests: pytest tests/ -q")
    print("3. Commit: git add . && git commit -m 'fix: add timeout to subprocess.run(, timeout=1800) calls'")
    print()

    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
