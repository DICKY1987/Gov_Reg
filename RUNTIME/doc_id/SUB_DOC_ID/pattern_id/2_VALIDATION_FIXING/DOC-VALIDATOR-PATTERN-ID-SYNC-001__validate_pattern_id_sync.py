#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-PATTERN-ID-SYNC-001
# DOC_ID: DOC-VALIDATOR-PATTERN-ID-SYNC-001
"""
doc_id: DOC-VALIDATOR-PATTERN-ID-SYNC-001
Validate pattern_id registry sync with filesystem and inventory
"""

import sys
import json
from pathlib import Path
import yaml

def validate_sync():
    """Validate registry is in sync with actual files and inventory"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "PAT_ID_REGISTRY.yaml"
    inventory_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "patterns_inventory.jsonl"

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    # Load inventory if exists
    inventory_ids = set()
    if inventory_path.exists():
        with open(inventory_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    if 'pattern_id' in item:
                        inventory_ids.add(item['pattern_id'])

    missing_files = []

    for pattern in registry.get('patterns', []):
        files_section = pattern.get('files', {})

        for file_type, file_list in files_section.items():
            if isinstance(file_list, list):
                for file_entry in file_list:
                    path_str = file_entry.get('path') if isinstance(file_entry, dict) else file_entry
                    if path_str:
                        file_path = Path(path_str)
                        if not file_path.is_absolute():
                            file_path = Path(__file__).parent.parent.parent.parent / path_str

                        if not file_path.exists():
                            missing_files.append({
                                'pattern_id': pattern['pattern_id'],
                                'file_path': path_str,
                                'type': file_type
                            })

    # Compare registry vs inventory
    registry_ids = {p['pattern_id'] for p in registry.get('patterns', []) if 'pattern_id' in p}
    drift = registry_ids - inventory_ids  # In registry but not inventory
    missing = inventory_ids - registry_ids  # In inventory but not registry

    return {
        'passed': len(missing_files) == 0 and len(drift) == 0 and len(missing) == 0,
        'missing_files': missing_files,
        'registry_count': len(registry.get('patterns', [])),
        'inventory_count': len(inventory_ids),
        'drift': list(drift),
        'missing': list(missing),
        'in_sync': len(missing_files) == 0 and len(drift) == 0 and len(missing) == 0
    }

if __name__ == '__main__':
    result = validate_sync()

    print("\n=== Pattern ID Sync Validation ===")
    print(f"Registry count: {result['registry_count']}")
    print(f"Inventory count: {result['inventory_count']}")
    print(f"Missing files: {len(result['missing_files'])}")
    print(f"Drift (in registry not inventory): {len(result['drift'])}")
    print(f"Missing (in inventory not registry): {len(result['missing'])}")

    if result['missing_files']:
        print("\n❌ Files not found:")
        for item in result['missing_files'][:20]:
            print(f"  - {item['pattern_id']} ({item['type']}): {item['file_path']}")
        if len(result['missing_files']) > 20:
            print(f"  ... and {len(result['missing_files']) - 20} more")

    if result['drift']:
        print("\n⚠️  Drift detected:")
        for pid in result['drift'][:10]:
            print(f"   {pid}")

    if result['missing']:
        print("\n⚠️  Missing from registry:")
        for pid in result['missing'][:10]:
            print(f"   {pid}")

    if result['passed']:
        print("\n✅ PASSED: Registry and inventory are in sync")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Sync issues detected")
        sys.exit(1)

    if result['missing_files']:
        print("\n❌ Files not found:")
        for item in result['missing_files'][:20]:
            print(f"  - {item['pattern_id']} ({item['type']}): {item['file_path']}")
        if len(result['missing_files']) > 20:
            print(f"  ... and {len(result['missing_files']) - 20} more")

    if result['passed']:
        print("\n✅ Registry is in sync")
        sys.exit(0)
    else:
        print("\n❌ Sync validation failed")
        sys.exit(1)
