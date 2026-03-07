#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-TRIGGER-ID-SYNC-001
# DOC_ID: DOC-VALIDATOR-TRIGGER-ID-SYNC-001
"""
doc_id: DOC-VALIDATOR-TRIGGER-ID-SYNC-001
Validate trigger_id registry sync with filesystem and inventory
"""

import sys
import json
from pathlib import Path
import yaml

def validate_sync():
    """Validate registry is in sync with actual files and inventory"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "TRG_ID_REGISTRY.yaml"
    inventory_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "triggers_inventory.jsonl"

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    registry_ids = {t['trigger_id']: t for t in registry.get('triggers', [])}

    # Load inventory if exists
    inventory_ids = set()
    if inventory_path.exists():
        with open(inventory_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    if 'trigger_id' in item:
                        inventory_ids.add(item['trigger_id'])

    # Check if files exist
    missing_files = []
    for trigger in registry.get('triggers', []):
        file_path = Path(trigger.get('file_path', ''))
        if not file_path.is_absolute():
            file_path = Path(__file__).parent.parent.parent.parent / file_path

        if not file_path.exists():
            missing_files.append({
                'trigger_id': trigger['trigger_id'],
                'file_path': trigger.get('file_path')
            })

    # Compare registry vs inventory
    registry_id_set = set(registry_ids.keys())
    drift = registry_id_set - inventory_ids  # In registry but not inventory
    missing = inventory_ids - registry_id_set  # In inventory but not registry

    return {
        'passed': len(missing_files) == 0 and len(drift) == 0 and len(missing) == 0,
        'missing_files': missing_files,
        'registry_count': len(registry_ids),
        'inventory_count': len(inventory_ids),
        'drift': list(drift),
        'missing': list(missing),
        'in_sync': len(missing_files) == 0 and len(drift) == 0 and len(missing) == 0
    }

if __name__ == '__main__':
    result = validate_sync()

    print("\n=== Trigger ID Sync Validation ===")
    print(f"Registry count: {result['registry_count']}")
    print(f"Inventory count: {result['inventory_count']}")
    print(f"Missing files: {len(result['missing_files'])}")
    print(f"Drift (in registry not inventory): {len(result['drift'])}")
    print(f"Missing (in inventory not registry): {len(result['missing'])}")

    if result['missing_files']:
        print("\n❌ Files not found:")
        for item in result['missing_files']:
            print(f"   {item['trigger_id']}: {item['file_path']}")

    if result['drift']:
        print("\n⚠️  Drift detected:")
        for tid in result['drift'][:10]:
            print(f"   {tid}")

    if result['missing']:
        print("\n⚠️  Missing from registry:")
        for tid in result['missing'][:10]:
            print(f"   {tid}")

    if result['passed']:
        print("\n✅ PASSED: Registry and inventory are in sync")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Sync issues detected")
        sys.exit(1)

    if result['missing_files']:
        print("\n❌ Files not found:")
        for item in result['missing_files']:
            print(f"  - {item['trigger_id']}: {item['file_path']}")

    if result['passed']:
        print("\n✅ Registry is in sync")
        sys.exit(0)
    else:
        print("\n❌ Sync validation failed")
        sys.exit(1)
