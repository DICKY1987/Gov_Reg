#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-PATTERN-ID-UNIQUENESS-001
# DOC_ID: DOC-VALIDATOR-PATTERN-ID-UNIQUENESS-001
"""
doc_id: DOC-VALIDATOR-PATTERN-ID-UNIQUENESS-001
Validate pattern_id uniqueness in registry
"""

import sys
from pathlib import Path
from collections import defaultdict
import yaml

def validate_uniqueness():
    """Validate all pattern_ids are unique"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "PAT_ID_REGISTRY.yaml"

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    seen = defaultdict(list)
    errors = []

    for pattern in registry.get('patterns', []):
        pattern_id = pattern.get('pattern_id')
        seen[pattern_id].append(pattern.get('name'))

    for pattern_id, names in seen.items():
        if len(names) > 1:
            errors.append({
                'pattern_id': pattern_id,
                'count': len(names),
                'names': names
            })

    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'total_checked': len(registry.get('patterns', [])),
        'unique_count': len(seen)
    }

if __name__ == '__main__':
    result = validate_uniqueness()

    print("\n=== Pattern ID Uniqueness Validation ===")
    print(f"Total IDs checked: {result['total_checked']}")
    print(f"Unique IDs: {result['unique_count']}")
    print(f"Duplicates found: {len(result['errors'])}")

    if result['errors']:
        print("\n❌ Duplicate IDs:")
        for error in result['errors']:
            print(f"  - {error['pattern_id']} (appears {error['count']} times)")

    if result['passed']:
        print("\n✅ All pattern IDs are unique")
        sys.exit(0)
    else:
        print("\n❌ Uniqueness validation failed")
        sys.exit(1)
