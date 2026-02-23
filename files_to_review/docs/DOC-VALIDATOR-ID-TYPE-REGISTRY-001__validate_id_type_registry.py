#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-ID-TYPE-REGISTRY-001
# DOC_ID: DOC-VALIDATOR-ID-TYPE-REGISTRY-001
"""
doc_id: DOC-VALIDATOR-ID-TYPE-REGISTRY-001
Validate ID_TYPE_REGISTRY.yaml structure and integrity
"""

import sys
import yaml
from pathlib import Path

REGISTRY_FILE = Path(__file__).parent / "ID_TYPE_REGISTRY.yaml"

def validate_registry():
    """Validate the ID type registry"""
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    errors = []
    warnings = []

    # Validate meta section
    if 'meta' not in registry:
        errors.append("Missing 'meta' section")
    else:
        required_meta = ['version', 'created_utc', 'updated_utc', 'total_types', 'description']
        for field in required_meta:
            if field not in registry['meta']:
                errors.append(f"Missing meta.{field}")

    # Validate id_types
    if 'id_types' not in registry:
        errors.append("Missing 'id_types' section")
        return {'passed': False, 'errors': errors, 'warnings': warnings}

    # Check meta.total_types matches actual count
    actual_count = len(registry['id_types'])
    meta_total = registry.get('meta', {}).get('total_types')
    if meta_total != actual_count:
        errors.append(f"meta.total_types mismatch: {meta_total} != {actual_count} actual types")

    seen_type_ids = set()
    status_counts = {}

    for idx, id_type in enumerate(registry['id_types']):
        # Required fields
        required = ['type_id', 'name', 'classification', 'tier', 'format',
                   'format_regex', 'status', 'priority', 'owner', 'description']

        for field in required:
            if field not in id_type:
                errors.append(f"ID type #{idx}: Missing required field '{field}'")

        # Check type_id uniqueness
        type_id = id_type.get('type_id')
        if type_id:
            if type_id in seen_type_ids:
                errors.append(f"Duplicate type_id: {type_id}")
            seen_type_ids.add(type_id)

        # Validate classification
        valid_classifications = ['minted', 'derived', 'runtime', 'natural']
        classification = id_type.get('classification')
        if classification and classification not in valid_classifications:
            errors.append(f"{type_id}: Invalid classification '{classification}'")

        # Derived types must have derivation_rule
        if classification == 'derived' and 'derivation_rule' not in id_type:
            errors.append(f"{type_id}: Derived type missing required 'derivation_rule' field")

        # Validate tier
        tier = id_type.get('tier')
        if tier and tier not in [1, 2, 3]:
            errors.append(f"{type_id}: Invalid tier {tier} (must be 1, 2, or 3)")

        # Validate status
        valid_statuses = ['planned', 'active', 'production', 'deprecated', 'retired']
        status = id_type.get('status')
        if status:
            if status not in valid_statuses:
                errors.append(f"{type_id}: Invalid status '{status}'")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Validate priority
        valid_priorities = ['critical', 'high', 'medium', 'low']
        priority = id_type.get('priority')
        if priority and priority not in valid_priorities:
            errors.append(f"{type_id}: Invalid priority '{priority}'")

        # Warn about production types without validators
        if status == 'production' and 'validators' not in id_type:
            warnings.append(f"{type_id}: Production type has no validators defined")

        # Warn about production types without coverage
        if status == 'production' and 'coverage' not in id_type:
            warnings.append(f"{type_id}: Production type has no coverage metrics")

    # Validate summary
    if 'summary' in registry:
        summary = registry['summary']

        # Check total matches
        if summary.get('total_types') != len(registry['id_types']):
            errors.append(f"Summary total_types mismatch: {summary.get('total_types')} != {len(registry['id_types'])}")

        # Check status counts
        for status, count in status_counts.items():
            if summary.get(status, 0) != count:
                errors.append(f"Summary {status} count mismatch: {summary.get(status, 0)} != {count}")

    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'total_types': len(registry['id_types']),
        'status_counts': status_counts
    }

if __name__ == '__main__':
    result = validate_registry()

    print("\n=== ID Type Registry Validation ===")
    print(f"Total types: {result['total_types']}")

    if result['status_counts']:
        print("\nStatus breakdown:")
        for status, count in result['status_counts'].items():
            print(f"  {status}: {count}")

    print(f"\nErrors: {len(result['errors'])}")
    print(f"Warnings: {len(result['warnings'])}")

    if result['errors']:
        print("\n❌ Errors:")
        for error in result['errors']:
            print(f"  - {error}")

    if result['warnings']:
        print("\n⚠️  Warnings:")
        for warning in result['warnings']:
            print(f"  - {warning}")

    if result['passed']:
        print("\n✅ Registry validation passed")
        sys.exit(0)
    else:
        print("\n❌ Registry validation failed")
        sys.exit(1)
