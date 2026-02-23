#!/usr/bin/env python3
"""
TASK-016: Patch Column Dictionary Predicates
Fix uppercase predicates to match lowercase normalization.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

DICT_PATH = Path("2026012816000001_COLUMN_DICTIONARY.json")
BACKUP_SUFFIX = ".pre-task016-backup"


def patch_predicates(dict_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert uppercase predicates to lowercase."""
    changes = []

    for header_name, header_spec in dict_data["headers"].items():
        scope = header_spec.get("scope", {})

        # Fix record_kinds_in
        if "record_kinds_in" in scope:
            old_vals = scope["record_kinds_in"]
            new_vals = [v.lower() for v in old_vals]
            if old_vals != new_vals:
                scope["record_kinds_in"] = new_vals
                changes.append((header_name, "record_kinds_in", old_vals, new_vals))

        # Fix entity_kinds_in
        if "entity_kinds_in" in scope:
            old_vals = scope["entity_kinds_in"]
            new_vals = [v.lower() for v in old_vals]
            if old_vals != new_vals:
                scope["entity_kinds_in"] = new_vals
                changes.append((header_name, "entity_kinds_in", old_vals, new_vals))

        # Fix presence rules with when conditions
        presence = header_spec.get("presence", {})
        if "rules" in presence:
            for rule in presence["rules"]:
                if "when" in rule:
                    for key, val in list(rule["when"].items()):
                        if isinstance(val, str):
                            new_val = val.lower()
                            if val != new_val:
                                rule["when"][key] = new_val
                                changes.append((header_name, f"when.{key}", val, new_val))

    return dict_data, changes


def validate_consistency(dict_data: Dict[str, Any]) -> List[tuple]:
    """Validate predicates match normalization transforms."""
    violations = []

    for header_name, header_spec in dict_data["headers"].items():
        transforms = header_spec.get("normalization", {}).get("transforms", [])
        scope = header_spec.get("scope", {})

        if "LOWERCASE" in transforms:
            # Check record_kinds_in
            if "record_kinds_in" in scope:
                for val in scope["record_kinds_in"]:
                    if val != val.lower():
                        violations.append((header_name, "record_kinds_in", val))

            # Check entity_kinds_in
            if "entity_kinds_in" in scope:
                for val in scope["entity_kinds_in"]:
                    if val != val.lower():
                        violations.append((header_name, "entity_kinds_in", val))

        # Check when conditions in presence rules
        presence = header_spec.get("presence", {})
        if "rules" in presence:
            for rule in presence.get("rules", []):
                if "when" in rule:
                    for key, val in rule["when"].items():
                        # Check against field's normalization
                        field_spec = dict_data["headers"].get(key, {})
                        field_transforms = field_spec.get("normalization", {}).get("transforms", [])
                        if "LOWERCASE" in field_transforms and isinstance(val, str):
                            if val != val.lower():
                                violations.append((header_name, f"when.{key}", val))

    return violations


def main():
    print("TASK-016: Patching Column Dictionary Predicates")
    print("=" * 60)

    # Load dictionary
    with open(DICT_PATH) as f:
        dict_data = json.load(f)

    print(f"✓ Loaded {DICT_PATH}")
    print(f"  Headers: {len(dict_data['headers'])}")

    # Check initial violations
    print("\n1. Checking for violations...")
    violations_before = validate_consistency(dict_data)
    print(f"   Found {len(violations_before)} violations")

    if not violations_before:
        print("✓ No violations found - dictionary already consistent!")
        return 0

    # Show first few violations
    print("\n   Sample violations:")
    for header, field, val in violations_before[:5]:
        print(f"   - {header}.{field}: '{val}' should be lowercase")

    # Create backup
    backup_path = DICT_PATH.with_suffix(DICT_PATH.suffix + BACKUP_SUFFIX)
    with open(backup_path, 'w') as f:
        json.dump(dict_data, f, indent=2)
    print(f"\n2. Created backup: {backup_path.name}")

    # Apply patches
    print("\n3. Applying patches...")
    dict_data, changes = patch_predicates(dict_data)
    print(f"   Applied {len(changes)} changes")

    # Validate after patching
    print("\n4. Validating fixes...")
    violations_after = validate_consistency(dict_data)

    if violations_after:
        print(f"   ✗ Still have {len(violations_after)} violations!")
        for header, field, val in violations_after[:10]:
            print(f"     - {header}.{field}: '{val}'")
        return 1

    print("   ✓ All violations fixed!")

    # Write patched dictionary
    with open(DICT_PATH, 'w') as f:
        json.dump(dict_data, f, indent=2)

    print(f"\n5. Wrote patched dictionary to {DICT_PATH}")

    # Summary
    print("\nSummary:")
    print(f"  Violations before: {len(violations_before)}")
    print(f"  Changes applied: {len(changes)}")
    print(f"  Violations after: {len(violations_after)}")
    print(f"  Backup: {backup_path}")

    print("\n✓ TASK-016 COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
