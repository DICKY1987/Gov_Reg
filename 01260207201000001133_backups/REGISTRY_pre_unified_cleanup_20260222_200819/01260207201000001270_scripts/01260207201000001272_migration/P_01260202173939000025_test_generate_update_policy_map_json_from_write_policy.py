#!/usr/bin/env python3
"""
TASK-011: Generate update_policy_map.json from Write Policy
Machine-readable field->update_policy map.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import write_policy_loader, column_dictionary_loader

# Output to Gov_Reg/config/
SCRIPT_DIR = Path(__file__).parent
GOV_REG_ROOT = SCRIPT_DIR.parent.parent.parent
OUTPUT_FILE = GOV_REG_ROOT / "config" / "update_policy_map.json"


def generate_update_policy_map():
    """Generate update_policy_map.json from Write Policy."""
    write_policy = write_policy_loader.load()
    column_dict = column_dictionary_loader.load()

    columns = write_policy.get("columns", {})
    headers = column_dict.get("headers", {})

    update_policy_map = {}

    for header_name in headers.keys():
        if header_name in columns:
            policy = columns[header_name].get("update_policy", "manual_or_automated")
        else:
            # Default policy
            policy = "manual_or_automated"

        update_policy_map[header_name] = policy

    # Write output
    with open(OUTPUT_FILE, "w") as f:
        json.dump(update_policy_map, f, indent=2, sort_keys=True)

    print(f"✓ Generated update_policy_map.json with {len(update_policy_map)} entries")

    # Validation
    assert "record_kind" in update_policy_map
    assert "file_id" in update_policy_map

    print("✓ Validation checks passed")

    return update_policy_map


if __name__ == "__main__":
    generate_update_policy_map()
