#!/usr/bin/env python3
"""
Update GEU Registry with Real Files

Merges the mapped real files from GOVERNANCE directory into the consolidated
GEU registry, replacing placeholder file IDs with real ones.
"""

import json
from pathlib import Path
from typing import Dict


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path) as f:
        return json.load(f)


def save_json(path: Path, data: dict):
    """Save JSON file with formatting."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def update_registry_with_real_files(
    registry_path: Path,
    geu_mapping_path: Path,
    output_path: Path
):
    """
    Update GEU registry with real file mappings.
    """
    print(f"\n{'='*80}")
    print("UPDATING GEU REGISTRY WITH REAL FILES")
    print(f"{'='*80}\n")

    # Load data
    registry = load_json(registry_path)
    geu_mapping = load_json(geu_mapping_path)

    print(f"📥 Loaded registry: {len(registry['geus'])} GEUs")
    print(f"📥 Loaded mapping: {len(geu_mapping)} GEUs with real files\n")

    # Update GEUs with real files
    updated_count = 0

    for geu in registry['geus']:
        geu_key = geu['geu_key']
        geu_id = geu['geu_id']

        # Find matching mapped data
        mapped_data = geu_mapping.get(geu_key)

        if not mapped_data:
            print(f"⏭️  {geu_key}: No mapped files (keeping placeholders)")
            continue

        print(f"🔄 {geu_key}")

        # Replace members with real files
        if mapped_data['members']:
            old_count = len(geu['members'])
            geu['members'] = mapped_data['members']

            # Update anchor if it's in members
            if geu['members']:
                first_member = geu['members'][0]
                geu['anchor_file_id'] = first_member['file_id']

            print(f"   ✅ Updated {len(geu['members'])} members (was {old_count} placeholders)")

            # Show file paths
            for member in geu['members']:
                file_path = Path(member.get('file_path', ''))
                print(f"      • {member['role_slot']:15} {file_path.name}")

        # Replace outputs with real files
        if mapped_data['outputs']:
            geu['outputs'] = mapped_data['outputs']
            print(f"   ✅ Updated {len(geu['outputs'])} outputs")

        # Replace tests with real files
        if mapped_data['tests']:
            geu['tests'] = mapped_data['tests']
            print(f"   ✅ Updated {len(geu['tests'])} tests")

        print()
        updated_count += 1

    # Save updated registry
    save_json(output_path, registry)

    print(f"{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Updated {updated_count} GEUs with real files")
    print(f"✅ Saved to: {output_path}")
    print(f"\nNext step: Validate with python scripts/validate_geu_registry.py")


def main():
    base_dir = Path("C:/Users/richg/Gov_Reg")
    registry_path = base_dir / "governance/geu-registry/geu_registry.json"
    geu_mapping_path = base_dir / "governance_geu_mapping.json"
    output_path = base_dir / "governance/geu-registry/geu_registry_with_real_files.json"

    if not registry_path.exists():
        print(f"❌ Registry not found: {registry_path}")
        return 1

    if not geu_mapping_path.exists():
        print(f"❌ GEU mapping not found: {geu_mapping_path}")
        print("   Run map_real_files_to_geus.py first")
        return 1

    update_registry_with_real_files(registry_path, geu_mapping_path, output_path)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
