#!/usr/bin/env python3
"""Generate SSOT validator to protect immutable fields."""

import sys
from pathlib import Path


SSOT_VALIDATOR = '''#!/usr/bin/env python3
"""SSOT validator - prevents modification of SSOT fields."""

import json
import sys


def validate_ssot(original_path, modified_path, schema_path):
    """Validate SSOT fields haven't changed."""
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    ssot_fields = []
    for field, spec in schema.get('properties', {}).items():
        if spec.get('x-ssot', False):
            ssot_fields.append(field)
    
    with open(original_path, 'r') as f:
        original = json.load(f)
    with open(modified_path, 'r') as f:
        modified = json.load(f)
    
    violations = []
    for field in ssot_fields:
        if field in original and field in modified:
            if original[field] != modified[field]:
                violations.append(field)
    
    if violations:
        print(f"✗ SSOT VIOLATION: {len(violations)} field(s) modified")
        for v in violations:
            print(f"  - {v}")
        return 1
    else:
        print("✓ SSOT FIELDS UNCHANGED")
        return 0


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: ssot_validator.py <original> <modified> <schema>")
        sys.exit(1)
    sys.exit(validate_ssot(sys.argv[1], sys.argv[2], sys.argv[3]))
'''


def generate_ssot_validator(output_path):
    """Generate SSOT validator script."""
    print(f"Generating SSOT Validator")
    print("=" * 70)
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(SSOT_VALIDATOR)
    
    try:
        output.chmod(0o755)
    except:
        pass
    
    print(f"✓ Validator generated: {output_path}")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'validators/ssot_validator.py'
    sys.exit(generate_ssot_validator(output))
