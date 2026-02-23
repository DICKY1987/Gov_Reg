#!/usr/bin/env python3
"""Update schema to include lifecycle state tracking."""

import sys
import json
from pathlib import Path
from datetime import datetime


LIFECYCLE_STATES = [
    "DRAFT",
    "PROPOSED",
    "APPROVED",
    "DEPLOYED",
    "MONITORING",
    "STABLE",
    "DEPRECATED",
    "ARCHIVED"
]


def update_schema_lifecycle_states(schema_path, output_path):
    """Add lifecycle state tracking to schema."""
    print(f"Updating Schema with Lifecycle States")
    print("=" * 70)
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"Schema file not found: {schema_path}")
        print("Creating new schema with lifecycle states...")
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Gov_Reg Enhanced Schema",
            "type": "object"
        }
    
    # Add lifecycle state properties
    if 'properties' not in schema:
        schema['properties'] = {}
    
    schema['properties']['lifecycle_state'] = {
        "type": "string",
        "enum": LIFECYCLE_STATES,
        "description": "Current lifecycle state of the artifact"
    }
    
    schema['properties']['lifecycle_history'] = {
        "type": "array",
        "description": "History of lifecycle state transitions",
        "items": {
            "type": "object",
            "properties": {
                "from_state": {"type": "string"},
                "to_state": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "reason": {"type": "string"},
                "approved_by": {"type": "string"}
            },
            "required": ["to_state", "timestamp"]
        }
    }
    
    schema['properties']['lifecycle_metadata'] = {
        "type": "object",
        "description": "Additional lifecycle tracking metadata",
        "properties": {
            "created_at": {"type": "string", "format": "date-time"},
            "deployed_at": {"type": "string", "format": "date-time"},
            "deprecated_at": {"type": "string", "format": "date-time"},
            "stability_achieved_at": {"type": "string", "format": "date-time"}
        }
    }
    
    # Add version tracking
    schema['version'] = schema.get('version', '1.0.0')
    schema['last_updated'] = datetime.utcnow().isoformat() + 'Z'
    schema['update_description'] = 'Added lifecycle state tracking'
    
    # Save updated schema
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)
    
    print(f"✓ Schema updated with lifecycle states")
    print(f"  States defined: {len(LIFECYCLE_STATES)}")
    print(f"  Output: {output_path}")
    print("=" * 70)
    print(f"✓ SCHEMA UPDATE COMPLETE")
    
    return 0


if __name__ == '__main__':
    schema = None
    output = None
    
    for i, arg in enumerate(sys.argv):
        if arg == '--schema' and i + 1 < len(sys.argv):
            schema = sys.argv[i + 1]
        elif arg == '--output' and i + 1 < len(sys.argv):
            output = sys.argv[i + 1]
    
    if not schema or not output:
        print("Usage: python update_schema_lifecycle_states.py --schema <input.json> --output <output.json>")
        sys.exit(1)
    
    sys.exit(update_schema_lifecycle_states(schema, output))
