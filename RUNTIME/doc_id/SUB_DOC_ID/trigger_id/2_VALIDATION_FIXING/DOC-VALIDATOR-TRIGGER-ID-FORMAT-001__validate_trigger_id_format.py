#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-TRIGGER-ID-FORMAT-001
# DOC_ID: DOC-VALIDATOR-TRIGGER-ID-FORMAT-001
"""
doc_id: DOC-VALIDATOR-TRIGGER-ID-FORMAT-001
Validate trigger_id format compliance
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from trigger_id.common.rules import validate_trigger_id_format, TRIGGER_ID_FORMAT
import yaml

def validate_registry_format():
    """Validate all trigger_ids in registry for format compliance"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "TRG_ID_REGISTRY.yaml"

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    errors = []
    warnings = []

    for trigger in registry.get('triggers', []):
        trigger_id = trigger.get('trigger_id')

        is_valid, error_msg = validate_trigger_id_format(trigger_id)

        if not is_valid:
            errors.append({
                'trigger_id': trigger_id,
                'error': error_msg,
                'file_path': trigger.get('file_path')
            })

    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'total_checked': len(registry.get('triggers', [])),
        'format': TRIGGER_ID_FORMAT
    }

if __name__ == '__main__':
    result = validate_registry_format()

    print("\n=== Trigger ID Format Validation ===")
    print(f"Expected format: {result['format']}")
    print(f"Total IDs checked: {result['total_checked']}")
    print(f"Errors: {len(result['errors'])}")
    print(f"Warnings: {len(result['warnings'])}")

    if result['errors']:
        print("\n❌ Format Errors:")
        for error in result['errors']:
            print(f"  - {error['trigger_id']}: {error['error']}")
            print(f"    File: {error['file_path']}")

    if result['passed']:
        print("\n✅ All trigger IDs have valid format")
        sys.exit(0)
    else:
        print("\n❌ Format validation failed")
        sys.exit(1)
