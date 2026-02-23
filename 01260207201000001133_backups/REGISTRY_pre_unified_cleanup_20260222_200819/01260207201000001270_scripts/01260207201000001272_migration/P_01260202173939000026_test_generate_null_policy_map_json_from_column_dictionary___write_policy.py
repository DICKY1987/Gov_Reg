#!/usr/bin/env python3
"""
TASK-010: Generate null_policy_map.json from Column Dictionary + Write Policy
Machine-readable field->null_policy map.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import column_dictionary_loader, write_policy_loader

# Output to Gov_Reg/config/
SCRIPT_DIR = Path(__file__).parent
GOV_REG_ROOT = SCRIPT_DIR.parent.parent.parent
OUTPUT_FILE = GOV_REG_ROOT / "config" / "null_policy_map.json"


def generate_null_policy_map():
    """Generate null_policy_map.json from Column Dictionary and Write Policy."""
    column_dict = column_dictionary_loader.load()
    write_policy = write_policy_loader.load()

    headers = column_dict.get("headers", {})
    columns = write_policy.get("columns", {})

    null_policy_map = {}

    for header_name in headers.keys():
        # Check write policy first
        if header_name in columns:
            policy = columns[header_name].get("null_policy", "allow_null")
        else:
            # Default from Column Dictionary presence policy
            presence = headers[header_name].get("presence", {})
            presence_policy = presence.get("policy", "OPTIONAL")

            if presence_policy == "REQUIRED":
                policy = "forbid_null"
            else:
                policy = "allow_null"

        null_policy_map[header_name] = policy

    # Add conditional rules
    null_policy_map["_conditionals"] = {
        "entity_kind": {
            "rule": "required when record_kind=='entity'",
            "condition": "record_kind == 'entity'",
            "policy": "forbid_null"
        }
    }

    # Write output
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(null_policy_map, f, indent=2, sort_keys=True)

    print(f"✓ Generated null_policy_map.json with {len(null_policy_map)} entries")

    # Validation
    assert "record_kind" in null_policy_map
    assert "extension" in null_policy_map

    print("✓ Validation checks passed")

    return null_policy_map


if __name__ == "__main__":
    generate_null_policy_map()
