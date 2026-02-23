"""Check if files from migration plan are already in registry"""
import sys
import json
from pathlib import Path

sys.path.insert(0, 'PATH_FILES')
from path_registry import resolve_path

# Keywords from expected migration files
migration_keywords = [
    'registry_writer',
    'registry_dao',
    'governance',
    'validator',
    'generator',
    'orchestrator',
    'transformer',
    'repo_autoops',
    'mapp_py',
    'parser'
]

try:
    registry_path = resolve_path('REGISTRY_UNIFIED')
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    files = registry.get('files', [])

    print(f"Total files in registry: {len(files)}")
    print(f"\nSearching for migration-related files...")
    print("=" * 70)

    found_by_keyword = {}

    for keyword in migration_keywords:
        matches = [f for f in files if keyword.lower() in f.get('relative_path', '').lower()]
        if matches:
            found_by_keyword[keyword] = matches
            print(f"\n{keyword.upper()}: {len(matches)} files")
            for match in matches[:5]:  # Show first 5
                print(f"  - {match.get('relative_path')}")
            if len(matches) > 5:
                print(f"  ... and {len(matches) - 5} more")

    print("\n" + "=" * 70)
    print(f"\nSUMMARY:")
    total_migration_files = sum(len(v) for v in found_by_keyword.values())
    print(f"  Total migration-related files found: {total_migration_files}")
    print(f"  Categories found: {len(found_by_keyword)}")

    # Check for 20-digit IDs
    files_with_20digit_ids = [f for f in files if f.get('file_id', '').startswith('01999000042260124')]
    print(f"\n  Files with 20-digit IDs (01999000042260124XXX): {len(files_with_20digit_ids)}")

    # Check for specific directories expected in migration
    src_dirs = ['src/registry_writer', 'src/repo_autoops', 'src/generators', 'scripts/parsers']
    for dir_path in src_dirs:
        matches = [f for f in files if dir_path in f.get('relative_path', '')]
        if matches:
            print(f"  {dir_path}: {len(matches)} files")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
