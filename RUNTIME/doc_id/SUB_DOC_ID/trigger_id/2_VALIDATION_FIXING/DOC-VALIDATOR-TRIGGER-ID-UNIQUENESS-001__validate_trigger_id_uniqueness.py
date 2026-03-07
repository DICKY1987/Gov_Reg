#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-TRIGGER-ID-UNIQUENESS-001
# DOC_ID: DOC-VALIDATOR-TRIGGER-ID-UNIQUENESS-001
"""
doc_id: DOC-VALIDATOR-TRIGGER-ID-UNIQUENESS-001
Validate trigger_id uniqueness in registry
"""

import sys
from pathlib import Path
from collections import defaultdict
import yaml

def validate_uniqueness():
    """Validate all trigger_ids are unique"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "TRG_ID_REGISTRY.yaml"

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    seen = defaultdict(list)
    errors = []

    for trigger in registry.get('triggers', []):
        trigger_id = trigger.get('trigger_id')
        seen[trigger_id].append(trigger.get('file_path'))

    # Find duplicates
    for trigger_id, paths in seen.items():
        if len(paths) > 1:
            errors.append({
                'trigger_id': trigger_id,
                'count': len(paths),
                'paths': paths
            })

    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'total_checked': len(registry.get('triggers', [])),
        'unique_count': len(seen)
    }

if __name__ == '__main__':
    result = validate_uniqueness()

    print("\n=== Trigger ID Uniqueness Validation ===")
    print(f"Total IDs checked: {result['total_checked']}")
    print(f"Unique IDs: {result['unique_count']}")
    print(f"Duplicates found: {len(result['errors'])}")

    if result['errors']:
        print("\n❌ Duplicate IDs:")
        for error in result['errors']:
            print(f"  - {error['trigger_id']} (appears {error['count']} times)")
            for path in error['paths']:
                print(f"    • {path}")

    if result['passed']:
        print("\n✅ All trigger IDs are unique")
        sys.exit(0)
    else:
        print("\n❌ Uniqueness validation failed")
        sys.exit(1)
