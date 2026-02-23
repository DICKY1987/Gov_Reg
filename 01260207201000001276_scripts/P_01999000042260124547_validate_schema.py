#!/usr/bin/env python3
"""Validate schema structure after updates."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "PATH_FILES"))

try:
    from path_registry import resolve_path
    SCHEMA_PATH = resolve_path("SCHEMA_V3")
    REGISTRY_PATH = resolve_path("REGISTRY_UNIFIED")
except ImportError:
    # Fallback: look in parent directory (since we're now in scripts/)
    SCHEMA_PATH = Path(__file__).parent.parent / "01999000042260124012_governance_registry_schema.v3.json"
    REGISTRY_PATH = Path(__file__).parent.parent / "01999000042260124503_governance_registry_unified.json"

def main():
    # Load and validate schema
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    print("✓ Schema is valid JSON")
    print(f"  Title: {schema.get('title')}")
    
    file_props = schema['definitions']['FileRecord']['properties']
    print(f"  FileRecord properties: {len(file_props)}")
    
    # Check for new bundle fields
    bundle_fields = ['bundle_id', 'bundle_key', 'bundle_role', 'bundle_version', 'anchor_file_id']
    linkage_fields = ['enforced_by_file_ids', 'enforces_rule_ids', 'depends_on_file_ids', 'test_file_ids', 'evidence_outputs', 'report_outputs']
    status_fields = ['coverage_status', 'superseded_by']
    
    print("\n  Bundle Identity Fields:")
    for field in bundle_fields:
        present = "✓" if field in file_props else "✗"
        print(f"    {present} {field}")
    
    print("\n  Linkage Fields:")
    for field in linkage_fields:
        present = "✓" if field in file_props else "✗"
        print(f"    {present} {field}")
    
    print("\n  Status Fields:")
    for field in status_fields:
        present = "✓" if field in file_props else "✗"
        print(f"    {present} {field}")
    
    # Load and check registry
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    print(f"\n✓ Registry is valid JSON")
    print(f"  Schema version: {registry.get('schema_version')}")
    print(f"  File entries: {len(registry.get('files', []))}")
    print(f"  Edge entries: {len(registry.get('edges', []))}")
    
    # Check first file has new fields
    if registry.get('files'):
        first_file = registry['files'][0]
        missing = []
        for field in bundle_fields + linkage_fields + status_fields:
            if field not in first_file:
                missing.append(field)
        
        if missing:
            print(f"\n✗ First file missing fields: {', '.join(missing)}")
        else:
            print(f"\n✓ All new fields present in file entries")
    
    print("\n✓ Validation complete")

if __name__ == "__main__":
    main()
