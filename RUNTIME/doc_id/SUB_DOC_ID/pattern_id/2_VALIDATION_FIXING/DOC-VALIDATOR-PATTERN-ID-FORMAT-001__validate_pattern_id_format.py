#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-PATTERN-ID-FORMAT-001
# DOC_ID: DOC-VALIDATOR-PATTERN-ID-FORMAT-001
"""
doc_id: DOC-VALIDATOR-PATTERN-ID-FORMAT-001
Validate pattern_id format compliance
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pattern_id.common.rules import validate_pattern_id_format, PATTERN_ID_FORMAT
import yaml

def validate_registry_format():
    """Validate all pattern_ids in registry for format compliance"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "PAT_ID_REGISTRY.yaml"

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    errors = []

    for pattern in registry.get('patterns', []):
        pattern_id = pattern.get('pattern_id')

        is_valid, error_msg = validate_pattern_id_format(pattern_id)

        if not is_valid:
            errors.append({
                'pattern_id': pattern_id,
                'error': error_msg
            })

    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'total_checked': len(registry.get('patterns', [])),
        'format': PATTERN_ID_FORMAT
    }

if __name__ == '__main__':
    result = validate_registry_format()

    print("\n=== Pattern ID Format Validation ===")
    print(f"Expected format: {result['format']}")
    print(f"Total IDs checked: {result['total_checked']}")
    print(f"Errors: {len(result['errors'])}")

    if result['errors']:
        print("\n❌ Format Errors:")
        for error in result['errors']:
            print(f"  - {error['pattern_id']}: {error['error']}")

    if result['passed']:
        print("\n✅ All pattern IDs have valid format")
        sys.exit(0)
    else:
        print("\n❌ Format validation failed")
        sys.exit(1)
