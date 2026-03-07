#!/usr/bin/env python
# DOC_LINK: DOC-SCRIPT-ADD-NON-INTERACTIVE-001
"""
Add --non-interactive flag to scripts with input() calls.

PATTERN: EXEC-001 (Batch File Transformation)
DOC_ID: DOC-SCRIPT-ADD-NON-INTERACTIVE-001

Purpose: Quick Win #2 - Enable scripts to run in CI/automation
Time: 3 hours | Saves: 8h/month (enables headless execution)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


class NonInteractiveAdder:
    """Add --non-interactive flag support to interactive scripts."""

    def __init__(self):
        self.files_modified = []
        self.changes_made = 0

    def has_interactive_calls(self, content: str) -> bool:
        """Check if file has interactive input calls."""
        patterns = [
            r'\binput\s*\(',
            r'\bclick\.confirm\s*\(',
            r'\bclick\.prompt\s*\(',
            r'Read-Host',  # PowerShell
        ]
        return any(re.search(pattern, content) for pattern in patterns)

    def has_argparse(self, content: str) -> bool:
        """Check if file uses argparse."""
        return 'argparse' in content and 'ArgumentParser' in content

    def process_python_file(self, filepath: Path) -> Tuple[bool, str]:
        """Add --non-interactive flag to Python script.

        Returns:
            (modified: bool, reason: str)
        """
        try:
            content = filepath.read_text(encoding='utf-8')

            if not self.has_interactive_calls(content):
                return False, "no interactive calls"

            if '--non-interactive' in content or 'non_interactive' in content:
                return False, "already has flag"

            if not self.has_argparse(content):
                return False, "no argparse (manual review needed)"

            # Find argparse setup
            lines = content.split('\n')
            modified_lines = []
            flag_added = False

            for i, line in enumerate(lines):
                modified_lines.append(line)

                # Add flag after parser creation
                if 'ArgumentParser' in line and not flag_added:
                    # Find next few lines for good insertion point
                    # Insert after parser creation, before first add_argument usually
                    next_i = i + 1
                    while next_i < len(lines) and lines[next_i].strip().startswith('#'):
                        modified_lines.append(lines[next_i])
                        next_i += 1

                    # Insert the flag
                    indent = '    '  # Common indentation
                    modified_lines.append('')
                    modified_lines.append(f'{indent}# Enable non-interactive mode for CI/automation')
                    modified_lines.append(f"{indent}parser.add_argument(")
                    modified_lines.append(f"{indent}    '--non-interactive',")
                    modified_lines.append(f"{indent}    action='store_true',")
                    modified_lines.append(f"{indent}    help='Run without interactive prompts (use defaults or fail)'")
                    modified_lines.append(f"{indent})")
                    flag_added = True

                    # Skip the lines we already added
                    while next_i <= i + 1 and next_i < len(lines):
                        next_i += 1

            if flag_added:
                # Also add usage pattern as comment
                modified_content = '\n'.join(modified_lines)

                # Add usage pattern near input() calls
                modified_content = re.sub(
                    r'(\s+)(if\s+.*input\(|.*=\s*input\()',
                    r'\1# TODO: Respect args.non_interactive flag\n\1\2',
                    modified_content,
                    count=1
                )

                filepath.write_text(modified_content, encoding='utf-8')
                return True, "added flag + TODO comment"

            return False, "argparse pattern not recognized"

        except Exception as e:
            return False, f"error: {e}"

    def process_batch(self, filepaths: List[Path], batch_num: int, total_batches: int):
        """Process a batch of files."""
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(filepaths)} files)")

        for filepath in filepaths:
            try:
                relative_path = filepath.relative_to(Path.cwd())
            except ValueError:
                relative_path = filepath

            modified, reason = self.process_python_file(filepath)

            if modified:
                self.files_modified.append(filepath)
                self.changes_made += 1
                print(f"  ✅ {relative_path} ({reason})")
            else:
                print(f"  ⏭️  {relative_path} ({reason})")

    def verify(self) -> dict:
        """Verify changes."""
        verified = 0
        for filepath in self.files_modified:
            if filepath.exists():
                content = filepath.read_text(encoding='utf-8')
                if '--non-interactive' in content:
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
    print("QUICK WIN #2: Add Non-Interactive Flags")
    print("=" * 60)
    print("Pattern: EXEC-001 (Batch File Transformation)")
    print("Purpose: Enable scripts to run in CI/automation")
    print()

    # Discover files with interactive calls
    print("🔍 Discovery: Finding scripts with input() calls...")

    search_dirs = [
        Path('scripts'),
        Path('phase4_routing/modules/tool_adapters/src/tools'),
    ]

    target_files = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for filepath in search_dir.rglob('*.py'):
            if any(part in str(filepath) for part in ['__pycache__', '_ARCHIVE', '.git']):
                continue

            try:
                content = filepath.read_text(encoding='utf-8')
                if re.search(r'\binput\s*\(', content):
                    target_files.append(filepath)
            except:
                pass

    print(f"Found {len(target_files)} scripts with input() calls")
    print()

    if not target_files:
        print("✅ No files need fixing!")
        return 0

    # Process in batches
    adder = NonInteractiveAdder()
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
    print(f"Flags added: {result['changes_made']}")
    print(f"Verified: {result['verified']}/{result['total_files_processed']}")
    print(f"Success: {'✅ YES' if result['success'] else '❌ NO'}")
    print()
    print("⚠️  IMPORTANT: Manual review needed!")
    print("   Each modified file has TODO comments where input() calls")
    print("   need to be updated to respect the --non-interactive flag.")
    print()
    print("Pattern:")
    print("  # Before:")
    print("  confirm = input('Continue? [y/N]: ')")
    print()
    print("  # After:")
    print("  if args.non_interactive:")
    print("      confirm = 'y'  # Auto-confirm in non-interactive mode")
    print("  else:")
    print("      confirm = input('Continue? [y/N]: ')")
    print()
    print("Next steps:")
    print("1. Review files with TODO comments")
    print("2. Update input() calls to respect args.non_interactive")
    print("3. Test: python script.py --non-interactive")
    print("4. Commit: git commit -m 'feat: add --non-interactive flags'")
    print()

    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
