#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-1323
"""
Migrate all TRIGGER- and PATTERN- references to TRIGGER- and PATTERN- format
Phase 1 Task T1.2
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def migrate_file(file_path: Path) -> Tuple[int, int]:
    """
    Migrate a single file. Returns (trg_count, pat_count)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        # Count replacements
        trg_count = len(re.findall(r'\bTRG-', content))
        pat_count = len(re.findall(r'\bPAT-', content))

        # Replace TRIGGER- with TRIGGER-
        content = re.sub(r'\bTRG-([A-Z]+)-(\d+)', r'TRIGGER-\1-\2', content)
        content = re.sub(r'\bTRG-', 'TRIGGER-', content)

        # Replace PATTERN- with PATTERN-
        content = re.sub(r'\bPAT-([A-Z]+)-(\d+)', r'PATTERN-\1-\2', content)
        content = re.sub(r'\bPAT-', 'PATTERN-', content)

        # Write if changed
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return (trg_count, pat_count)

        return (0, 0)
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return (0, 0)

def main():
    base_dir = Path(__file__).parent

    # File patterns to migrate
    patterns = ['*.py', '*.md', '*.yaml', '*.yml', '*.json', '*.jsonl']

    # Directories to skip
    skip_dirs = {'.git', '__pycache__', '.backups', 'backups_v2_v3', 'ARCHIVE', 'PLANNING_ARCHIVE'}

    total_trg = 0
    total_pat = 0
    files_modified = []

    print("🔄 Starting legacy format migration...")
    print(f"Scanning: {base_dir}")

    for pattern in patterns:
        for file_path in base_dir.rglob(pattern):
            # Skip if in excluded directory
            if any(skip in file_path.parts for skip in skip_dirs):
                continue

            trg, pat = migrate_file(file_path)
            if trg > 0 or pat > 0:
                total_trg += trg
                total_pat += pat
                files_modified.append(file_path.relative_to(base_dir))
                print(f"  ✓ {file_path.relative_to(base_dir)} (TRG:{trg}, PAT:{pat})")

    print(f"\n✅ Migration complete!")
    print(f"   Files modified: {len(files_modified)}")
    print(f"   TRIGGER- replaced: {total_trg}")
    print(f"   PATTERN- replaced: {total_pat}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
