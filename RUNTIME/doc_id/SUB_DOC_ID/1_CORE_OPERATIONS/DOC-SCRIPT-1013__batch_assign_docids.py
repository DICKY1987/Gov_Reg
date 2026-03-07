#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-1013
"""
Batch Doc ID Assignment Script

PURPOSE: Assign doc_ids to Python files missing them in batches
DOC-ID: A-TOOL-BATCH-ASSIGN-001
STATUS: active
CREATED: 2026-01-04
"""

import json
import re
import sys
import yaml
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent.parent.parent
INVENTORY_PATH = BASE_DIR / "5_REGISTRY_DATA" / "docs_inventory.jsonl"
REGISTRY_PATH = BASE_DIR / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"

DOC_ID_PATTERNS = {
    'test': r'test_.*\.py$|.*_test\.py$|conftest\.py$',
    'script': r'.*',  # Default for standalone scripts
}

def load_inventory():
    """Load the docs inventory"""
    entries = []
    with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            entries.append(json.loads(line))
    return entries

def load_registry():
    """Load the YAML registry"""
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def determine_category(path: str) -> str:
    """Determine doc_id category based on file path"""
    path_lower = path.lower()

    # Test files
    if re.search(DOC_ID_PATTERNS['test'], path_lower):
        return 'test'

    # Scripts (tools, validators, generators, etc.)
    if any(x in path_lower for x in ['scripts/', 'tools/', 'validators/', 'generators/']):
        return 'script'

    # Core system
    if any(x in path_lower for x in ['core/', 'engine/', 'orchestrator/', 'executor/']):
        return 'core'

    # Error/recovery
    if any(x in path_lower for x in ['error', 'recovery', 'plugin']):
        return 'error'

    # Patterns
    if 'pattern' in path_lower:
        return 'patterns'

    # Config
    if any(x in path_lower for x in ['config', 'settings']):
        return 'config'

    # Default to script
    return 'script'

def generate_doc_id(category: str, next_id: int) -> str:
    """Generate a doc_id for the given category"""
    category_prefix_map = {
        'core': 'CORE',
        'error': 'ERROR',
        'patterns': 'PAT',
        'guide': 'GUIDE',
        'spec': 'SPEC',
        'test': 'TEST',
        'script': 'SCRIPT',
        'config': 'CONFIG',
    }

    prefix = category_prefix_map.get(category, 'SCRIPT')
    return f"DOC-{prefix}-{next_id:04d}"

def inject_doc_id(file_path: Path, doc_id: str, dry_run=True):
    """Inject doc_id into file"""
    if dry_run:
        print(f"  [DRY-RUN] Would inject {doc_id} into {file_path}")
        return True

    try:
        # Read file
        content = file_path.read_text(encoding='utf-8')

        # Check if already has doc_id (accept both DOC_ID: and DOC-ID:)
        if re.search(r'DOC[-_]ID:', content, re.IGNORECASE):
            print(f"  ⚠️  File already has doc_id: {file_path}")
            return False

        # Find insertion point (after shebang/encoding, before docstring or first code)
        lines = content.splitlines(keepends=True)
        insert_idx = 0

        # Skip shebang
        if lines and lines[0].startswith('#!'):
            insert_idx = 1

        # Skip encoding declaration
        if insert_idx < len(lines) and 'coding' in lines[insert_idx]:
            insert_idx += 1

        # Insert doc_id comment (use underscore, not hyphen!)
        doc_id_line = f"# DOC_ID: {doc_id}\n"
        lines.insert(insert_idx, doc_id_line)

        # Write back
        file_path.write_text(''.join(lines), encoding='utf-8')
        print(f"  ✅ Injected {doc_id}")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Batch assign doc_ids to Python files')
    parser.add_argument('--limit', type=int, default=50, help='Max files to process')
    parser.add_argument('--execute', action='store_true', help='Actually modify files (default is dry-run)')
    parser.add_argument('--filter', choices=['py', 'all'], default='py', help='File type filter')
    args = parser.parse_args()

    dry_run = not args.execute

    print(f"\n{'='*60}")
    print(f"Batch Doc ID Assignment")
    print(f"{'='*60}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY-RUN'}")
    print(f"Limit: {args.limit} files")
    print(f"Filter: {args.filter}")
    print(f"{'='*60}\n")

    # Load data
    print("Loading inventory...")
    inventory = load_inventory()

    print("Loading registry...")
    registry = load_registry()

    # Filter for missing doc_ids
    missing = [
        e for e in inventory
        if e.get('status') == 'missing' and
           (args.filter == 'all' or e.get('file_type') == args.filter)
    ]

    print(f"\nFound {len(missing)} files needing doc_ids")
    print(f"Processing first {min(args.limit, len(missing))} files...\n")

    # Track category counters
    category_counts = {}
    for cat_name, cat_data in registry['categories'].items():
        category_counts[cat_name] = cat_data.get('next_id', 1)

    processed = 0
    success = 0

    for entry in missing[:args.limit]:
        path_str = entry['path']
        file_path = REPO_ROOT / path_str

        # Determine category
        category = determine_category(path_str)

        # Generate doc_id
        next_id = category_counts.get(category, 1)
        doc_id = generate_doc_id(category, next_id)

        print(f"{processed+1}. {path_str}")
        print(f"   Category: {category}, Doc ID: {doc_id}")

        # Inject doc_id
        if inject_doc_id(file_path, doc_id, dry_run):
            category_counts[category] = next_id + 1
            success += 1

        processed += 1
        print()

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Processed: {processed} files")
    print(f"Success:   {success} files")
    print(f"Failed:    {processed - success} files")
    print(f"\nCategory ID allocations:")
    for cat, next_id in category_counts.items():
        original = registry['categories'][cat].get('next_id', 1)
        used = next_id - original
        if used > 0:
            print(f"  {cat:12s}: {original:4d} -> {next_id:4d} ({used} used)")
    print(f"{'='*60}\n")

    if dry_run:
        print("⚠️  This was a DRY-RUN. No files were modified.")
        print("   Run with --execute to actually modify files.\n")
    else:
        print("✅ Files modified successfully!")
        print("   Next steps:")
        print("   1. Review changes: git diff")
        print("   2. Re-scan: python doc_id_scanner.py scan")
        print("   3. Validate: python validate_doc_id_coverage.py\n")

if __name__ == '__main__':
    main()
