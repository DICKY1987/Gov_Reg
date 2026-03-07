#!/usr/bin/env python
# DOC_LINK: DOC-SCRIPT-ADD-JSON-OUTPUT-001
"""
Add --json output flag to utility scripts.

PATTERN: EXEC-001 (Batch File Transformation)
DOC_ID: DOC-SCRIPT-ADD-JSON-OUTPUT-001

Purpose: Quick Win #5 - Enable machine-readable output from scripts
Time: 2 hours | Saves: 6h/month (automated parsing of script output)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


class JsonOutputAdder:
    """Add --json output flag to scripts."""

    def __init__(self):
        self.files_modified = []
        self.changes_made = 0

    def has_print_statements(self, content: str) -> bool:
        """Check if script outputs to console."""
        return 'print(' in content

    def has_argparse(self, content: str) -> bool:
        """Check if file uses argparse."""
        return 'argparse' in content and 'ArgumentParser' in content

    def process_script(self, filepath: Path) -> Tuple[bool, str]:
        """Add --json flag to script.

        Returns:
            (modified: bool, reason: str)
        """
        try:
            content = filepath.read_text(encoding='utf-8')

            if not self.has_print_statements(content):
                return False, "no console output"

            if '--json' in content or 'output_json' in content:
                return False, "already has json flag"

            if not self.has_argparse(content):
                return False, "no argparse"

            # Add json flag to argparse
            lines = content.split('\n')
            modified_lines = []
            flag_added = False

            for i, line in enumerate(lines):
                modified_lines.append(line)

                # Add flag after parser creation
                if 'ArgumentParser' in line and not flag_added:
                    # Find next add_argument or skip comments
                    next_i = i + 1
                    while next_i < len(lines) and lines[next_i].strip().startswith('#'):
                        modified_lines.append(lines[next_i])
                        next_i += 1

                    # Insert the flag
                    indent = '    '
                    modified_lines.append('')
                    modified_lines.append(f'{indent}# Output format')
                    modified_lines.append(f"{indent}parser.add_argument(")
                    modified_lines.append(f"{indent}    '--json',")
                    modified_lines.append(f"{indent}    action='store_true',")
                    modified_lines.append(f"{indent}    help='Output results as JSON instead of human-readable text'")
                    modified_lines.append(f"{indent})")
                    flag_added = True

            if flag_added:
                modified_content = '\n'.join(modified_lines)

                # Add helper comment near main output
                modified_content = re.sub(
                    r'(def main\(\).*?\n)',
                    r'\1    # TODO: Add json.dumps() output when args.json is True\n',
                    modified_content,
                    flags=re.DOTALL,
                    count=1
                )

                filepath.write_text(modified_content, encoding='utf-8')
                return True, "added --json flag"

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

            modified, reason = self.process_script(filepath)

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
                if '--json' in content:
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
    print("QUICK WIN #5: Add JSON Output Flags")
    print("=" * 60)
    print("Pattern: EXEC-001 (Batch File Transformation)")
    print("Purpose: Enable machine-readable output")
    print()

    # Find utility scripts
    print("🔍 Discovery: Finding utility scripts...")

    search_dirs = [
        Path('scripts'),
    ]

    # Exclude certain patterns
    exclude_patterns = [
        'automation_fixes',  # Our fix scripts
        'dev',  # Dev utilities
        '__pycache__',
        '_ARCHIVE',
    ]

    target_files = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for filepath in search_dir.rglob('*.py'):
            if any(pattern in str(filepath) for pattern in exclude_patterns):
                continue

            try:
                content = filepath.read_text(encoding='utf-8')
                # Must have argparse and print statements
                if 'argparse' in content and 'print(' in content:
                    target_files.append(filepath)
            except:
                pass

    print(f"Found {len(target_files)} candidate scripts")
    print()

    if not target_files:
        print("✅ No files need modification!")
        return 0

    # Process in batches
    adder = JsonOutputAdder()
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
    print(f"Scripts modified: {result['total_files_processed']}")
    print(f"Flags added: {result['changes_made']}")
    print(f"Verified: {result['verified']}/{result['total_files_processed']}")
    print(f"Success: {'✅ YES' if result['success'] else '❌ NO'}")
    print()

    if result['success'] and result['total_files_processed'] > 0:
        print("⚠️  Manual review needed:")
        print("   Each script needs logic to output JSON when --json is True")
        print()
        print("Pattern:")
        print("  if args.json:")
        print("      print(json.dumps({'status': 'success', 'data': results}))")
        print("  else:")
        print("      print('Results:', results)")
        print()

    print("Next steps:")
    print("1. Review modified scripts")
    print("2. Implement JSON output logic")
    print("3. Test: python script.py --json | jq")
    print("4. Commit: git commit -m 'feat: add --json output flags'")
    print()

    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
