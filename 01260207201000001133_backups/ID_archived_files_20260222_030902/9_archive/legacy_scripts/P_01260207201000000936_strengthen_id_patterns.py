#!/usr/bin/env python3
"""Strengthen ID patterns for better validation."""

import sys
import json
from pathlib import Path


ID_PATTERNS = {
    "artifact_id": "^ART-[0-9]{14}-[A-Z0-9]{8}$",
    "phase_id": "^PH-[A-Z]+-[0-9]{3}$",
    "gate_id": "^GATE-[0-9]{3}$",
    "baseline_id": "^BASELINE-[0-9]{14}$",
    "backup_id": "^BACKUP-[0-9]{14}$"
}


def strengthen_id_patterns(schema_path, output_path):
    """Add stronger ID validation patterns to schema."""
    print(f"Strengthening ID Patterns")
    print("=" * 70)
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except FileNotFoundError:
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "properties": {}
        }
    
    if 'properties' not in schema:
        schema['properties'] = {}
    
    for id_field, pattern in ID_PATTERNS.items():
        if id_field not in schema['properties']:
            schema['properties'][id_field] = {"type": "string"}
        schema['properties'][id_field]['pattern'] = pattern
        schema['properties'][id_field]['description'] = \
            f"Strongly validated ID following pattern: {pattern}"
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)
    
    print(f"✓ ID patterns strengthened: {len(ID_PATTERNS)}")
    print(f"✓ Output: {output_path}")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: strengthen_id_patterns.py <schema> <output>")
        sys.exit(1)
    sys.exit(strengthen_id_patterns(sys.argv[1], sys.argv[2]))
