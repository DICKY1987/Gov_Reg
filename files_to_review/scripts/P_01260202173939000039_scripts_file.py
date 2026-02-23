#!/usr/bin/env python3
"""Analyze registry files to understand bundle grouping opportunities."""
import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / "PATH_FILES"))

try:
    from path_registry import resolve_path
    REGISTRY_PATH = resolve_path("REGISTRY_UNIFIED")
except ImportError:
    # Fallback: look in parent directory (since we're now in scripts/)
    REGISTRY_PATH = Path(__file__).parent.parent / "01999000042260124503_governance_registry_unified.json"

with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
    registry = json.load(f)

print("\n=== Registry Analysis ===\n")

# Group by artifact_kind
by_kind = defaultdict(list)
for f in registry['files']:
    by_kind[f.get('artifact_kind')].append(f)

print("Files by artifact_kind:")
for kind, files in sorted(by_kind.items()):
    print(f"  {kind:20} : {len(files):2} files")

# Group by layer
print("\nFiles by layer:")
by_layer = defaultdict(list)
for f in registry['files']:
    by_layer[f.get('layer')].append(f)

for layer, files in sorted(by_layer.items()):
    print(f"  {layer:20} : {len(files):2} files")

# Group by geu_role
print("\nFiles by geu_role:")
by_geu_role = defaultdict(list)
for f in registry['files']:
    role = f.get('geu_role')
    by_geu_role[role].append(f)

for role, files in sorted(by_geu_role.items(), key=lambda x: (x[0] is None, x[0])):
    role_str = role if role else "(none)"
    print(f"  {role_str:20} : {len(files):2} files")

# Show files without bundles
print("\n=== Files Without Bundle Assignment ===\n")
files_without_bundles = [f for f in registry['files'] if not f.get('bundle_id')]
print(f"Total: {len(files_without_bundles)}/{len(registry['files'])}\n")

for f in files_without_bundles[:10]:  # Show first 10
    rel_path = f.get('relative_path', 'N/A')
    artifact_kind = f.get('artifact_kind', 'N/A')
    layer = f.get('layer', 'N/A')
    geu_role = f.get('geu_role') or '(none)'

    print(f"  {artifact_kind:15} | {layer:15} | {geu_role:12} | {Path(rel_path).name[:50]}")

if len(files_without_bundles) > 10:
    print(f"  ... and {len(files_without_bundles) - 10} more")
