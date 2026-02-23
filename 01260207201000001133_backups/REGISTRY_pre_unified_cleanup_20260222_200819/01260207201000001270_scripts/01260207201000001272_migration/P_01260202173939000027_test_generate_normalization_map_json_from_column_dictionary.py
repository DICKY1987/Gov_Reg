#!/usr/bin/env python3
"""
TASK-009: Generate normalization_map.json from Column Dictionary
Machine-readable field->normalization transforms map (147 entries).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import column_dictionary_loader

# Output to Gov_Reg/config/
SCRIPT_DIR = Path(__file__).parent
GOV_REG_ROOT = SCRIPT_DIR.parent.parent.parent
OUTPUT_FILE = GOV_REG_ROOT / "config" / "normalization_map.json"


def generate_normalization_map():
    """Generate normalization_map.json from Column Dictionary."""
    column_dict = column_dictionary_loader.load()
    headers = column_dict.get("headers", {})

    normalization_map = {}

    for header_name, header_def in headers.items():
        transforms = header_def.get("normalization", {}).get("transforms", [])
        normalization_map[header_name] = transforms

    # Write output
    with open(OUTPUT_FILE, "w") as f:
        json.dump(normalization_map, f, indent=2, sort_keys=True)

    print(f"✓ Generated normalization_map.json with {len(normalization_map)} entries")

    # Validation
    assert (
        len(normalization_map) == 147
    ), f"Expected 147 entries, got {len(normalization_map)}"
    assert normalization_map.get("record_kind") == [
        "LOWERCASE"
    ], "record_kind should have LOWERCASE transform"
    assert (
        normalization_map.get("artifact_kind") == []
    ), "artifact_kind should have empty transforms"
    assert normalization_map.get("relative_path") == [
        "NORMALIZE_SLASHES"
    ], "relative_path should have NORMALIZE_SLASHES"

    print("✓ Validation checks passed")

    return normalization_map


if __name__ == "__main__":
    generate_normalization_map()
