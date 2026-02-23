#!/usr/bin/env python3
"""Add merge policies schema for conflict resolution."""

import sys
import json
from pathlib import Path


MERGE_POLICY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Merge Policy Schema",
    "type": "object",
    "properties": {
        "policy_id": {"type": "string"},
        "field": {"type": "string"},
        "strategy": {
            "type": "string",
            "enum": ["NEWEST_WINS", "MANUAL", "MERGE_ARRAY", "SSOT_PROTECTED"]
        },
        "priority": {"type": "integer"},
        "conditions": {"type": "object"}
    },
    "required": ["policy_id", "field", "strategy"]
}


def add_merge_policies_schema(output_path):
    """Generate merge policies schema."""
    print(f"Generating Merge Policies Schema")
    print("=" * 70)
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(MERGE_POLICY_SCHEMA, f, indent=2)
    
    print(f"✓ Schema generated: {output_path}")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'schemas/merge_policy.schema.json'
    sys.exit(add_merge_policies_schema(output))
