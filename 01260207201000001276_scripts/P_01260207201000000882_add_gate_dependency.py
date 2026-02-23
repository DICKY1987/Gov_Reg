#!/usr/bin/env python3
"""Add gate dependency tracking to schema."""

import sys
import json
from pathlib import Path


def add_gate_dependency(schema_path, gate_id, dependencies, output_path):
    """Add gate dependencies to schema."""
    print(f"Adding Gate Dependencies")
    print("=" * 70)
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except FileNotFoundError:
        schema = {"gates": {}}
    
    if 'gates' not in schema:
        schema['gates'] = {}
    
    if gate_id not in schema['gates']:
        schema['gates'][gate_id] = {}
    
    dep_list = [d.strip() for d in dependencies.split(',')]
    schema['gates'][gate_id]['dependencies'] = dep_list
    schema['gates'][gate_id]['dependency_count'] = len(dep_list)
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)
    
    print(f"✓ Gate {gate_id} dependencies added: {len(dep_list)}")
    print(f"✓ Output: {output_path}")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: add_gate_dependency.py <schema> <gate_id> <deps> <output>")
        sys.exit(1)
    sys.exit(add_gate_dependency(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
