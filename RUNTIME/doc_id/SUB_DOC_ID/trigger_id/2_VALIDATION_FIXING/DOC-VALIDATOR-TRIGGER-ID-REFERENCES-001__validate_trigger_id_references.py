#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-TRIGGER-ID-REFERENCES-001
# DOC_ID: DOC-VALIDATOR-TRIGGER-ID-REFERENCES-001
"""
doc_id: DOC-VALIDATOR-TRIGGER-ID-REFERENCES-001
Validate trigger_id references in codebase
"""

import sys
import re
from pathlib import Path
import yaml

def find_references():
    """Find all trigger_id references in codebase"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "TRG_ID_REGISTRY.yaml"
    repo_root = Path(__file__).parent.parent.parent.parent.parent

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    valid_ids = {t['trigger_id'] for t in registry.get('triggers', [])}

    # Find all TRIGGER-* references
    pattern = re.compile(r'TRIGGER-[A-Z0-9]+-[A-Z0-9-]+-[0-9]+')
    broken_refs = []

    search_dirs = [
        repo_root / "RUNTIME",
        repo_root / "WORKFLOWS",
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for file_path in search_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.yaml', '.yml', '.md']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        found_ids = set(pattern.findall(content))

                        for found_id in found_ids:
                            if found_id not in valid_ids:
                                broken_refs.append({
                                    'id': found_id,
                                    'file': str(file_path.relative_to(repo_root))
                                })
                except Exception:
                    pass

    return {
        'passed': len(broken_refs) == 0,
        'broken_refs': broken_refs,
        'valid_ids_count': len(valid_ids)
    }

if __name__ == '__main__':
    result = find_references()

    print("\n=== Trigger ID References Validation ===")
    print(f"Valid IDs in registry: {result['valid_ids_count']}")
    print(f"Broken references: {len(result['broken_refs'])}")

    if result['broken_refs']:
        print("\n❌ Broken references found:")
        for ref in result['broken_refs'][:20]:  # Show first 20
            print(f"  - {ref['id']} in {ref['file']}")
        if len(result['broken_refs']) > 20:
            print(f"  ... and {len(result['broken_refs']) - 20} more")

    if result['passed']:
        print("\n✅ All references are valid")
        sys.exit(0)
    else:
        print("\n❌ Reference validation failed")
        sys.exit(1)
