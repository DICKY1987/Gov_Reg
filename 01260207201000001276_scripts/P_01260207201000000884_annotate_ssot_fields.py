#!/usr/bin/env python3
"""Annotate schema fields as SSOT (Single Source of Truth)."""

import sys
import json
from pathlib import Path


def annotate_ssot_fields(schema_path, ssot_fields, output_path):
    """Add SSOT annotations to schema fields."""
    print(f"Annotating SSOT Fields")
    print("=" * 70)
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Schema not found: {schema_path}")
        return 1
    
    ssot_list = ssot_fields.split(',')
    
    if 'properties' not in schema:
        schema['properties'] = {}
    
    for field in ssot_list:
        field = field.strip()
        if field in schema['properties']:
            if 'x-ssot' not in schema['properties'][field]:
                schema['properties'][field]['x-ssot'] = True
                schema['properties'][field]['x-ssot-description'] = \
                    "This field is the Single Source of Truth and must not be modified"
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)
    
    print(f"✓ SSOT fields annotated: {len(ssot_list)}")
    print(f"✓ Output: {output_path}")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: annotate_ssot_fields.py <schema> <fields> <output>")
        sys.exit(1)
    sys.exit(annotate_ssot_fields(sys.argv[1], sys.argv[2], sys.argv[3]))
