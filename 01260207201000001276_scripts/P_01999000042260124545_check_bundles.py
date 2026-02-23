#!/usr/bin/env python3
"""Check bundle assignments after detection."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "PATH_FILES"))

try:
    from path_registry import resolve_path
    REGISTRY_PATH = resolve_path("REGISTRY_UNIFIED")
except ImportError:
    # Fallback: look in parent directory (since we're now in scripts/)
    REGISTRY_PATH = Path(__file__).parent.parent / "01999000042260124503_governance_registry_unified.json"

with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
    registry = json.load(f)

files_with_bundles = [f for f in registry['files'] if f.get('bundle_id')]

print(f"\n✓ Files with bundle assignments: {len(files_with_bundles)}/{len(registry['files'])}\n")
print("Bundle Summary:")
print("-" * 100)

for f in files_with_bundles:
    bundle_key = f.get('bundle_key', 'N/A')
    bundle_role = f.get('bundle_role') or 'N/A'
    bundle_id = f.get('bundle_id', 'N/A')
    file_id = f.get('file_id', 'N/A')
    
    print(f"  {bundle_key:45} | Role: {bundle_role:10} | Bundle: {bundle_id} | File: {file_id}")

print("-" * 100)
print(f"\n✓ Total bundles created: {len(set(f['bundle_id'] for f in files_with_bundles if f.get('bundle_id')))}")
