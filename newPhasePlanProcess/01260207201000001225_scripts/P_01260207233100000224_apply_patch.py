#!/usr/bin/env python3
"""
Apply RFC-6902 JSON patches to the Autonomous Delivery Template.

Usage:
  python P_01260207233100000224_apply_patch.py <template_path> <patch_path>

Requires: pip install jsonpatch
"""

import json
import shutil
import sys
from pathlib import Path

try:
    import jsonpatch
except ImportError:
    print("Error: jsonpatch not installed. Run: pip install jsonpatch")
    sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    template_path = Path(sys.argv[1])
    patch_path = Path(sys.argv[2])

    # Load template
    with open(template_path, "r", encoding="utf-8") as f:
        template = json.load(f)

    # Load patch
    with open(patch_path, "r", encoding="utf-8") as f:
        raw_ops = json.load(f)

    # Strip _comment keys (not part of RFC-6902)
    ops = [{k: v for k, v in op.items() if k != "_comment"} for op in raw_ops]

    # Create backup
    backup_path = template_path.with_suffix(".pre-tmp-patch-backup.json")
    shutil.copy2(template_path, backup_path)
    print(f"Backup created: {backup_path}")

    # Apply patch
    patch = jsonpatch.JsonPatch(ops)
    patched = patch.apply(template)

    # Write result
    with open(template_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(patched, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Verification summary
    version = patched.get("template_metadata", {}).get("version", "?")
    rules_count = len(patched.get("critical_constraint", {}).get("rules", []))
    gates_count = len(patched.get("validation_gates", []))

    print(f"\nPatch applied successfully.")
    print(f"  Version:          {version}")
    print(f"  Rules count:      {rules_count}")
    print(f"  Gates count:      {gates_count}")

    # Check new sections
    new_sections = []
    if "evidence_write_rule" in patched.get("ground_truth_levels", {}).get(
        "enforcement", {}
    ):
        new_sections.append("evidence_write_rule")
    if "assumption_schema" in patched.get("assumptions_scope", {}):
        new_sections.append("assumption_schema")
    if "command_platform_audit" in patched.get("infrastructure", {}):
        new_sections.append("command_platform_audit")
    if "_output_schema_extensions" in patched.get("phase_contracts", {}):
        new_sections.append("_output_schema_extensions")
    if "threshold_enforcement_policy" in patched.get("metrics", {}):
        new_sections.append("threshold_enforcement_policy")

    print(f"  New sections:     {', '.join(new_sections)}")


if __name__ == "__main__":
    main()
