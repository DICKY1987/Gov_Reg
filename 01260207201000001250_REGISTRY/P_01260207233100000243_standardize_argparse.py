#!/usr/bin/env python3
"""
Standardize all gate scripts to use --plan-file instead of positional plan_file argument.
"""

import re
from pathlib import Path


def standardize_script(script_path: Path) -> bool:
    """Convert positional plan_file to --plan-file named argument."""

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Pattern 1: parser.add_argument('plan_file', ...)
    content = re.sub(
        r"parser\.add_argument\(\s*['\"]plan_file['\"]\s*,\s*help=['\"]Path to plan JSON file['\"]\s*\)",
        "parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')",
        content,
    )

    # Pattern 2: parser.add_argument('plan_file', help=...)
    content = re.sub(
        r"parser\.add_argument\(\s*['\"]plan_file['\"]\s*,\s*help=",
        "parser.add_argument('--plan-file', required=True, help=",
        content,
    )

    # Pattern 3: args.plan_file references need to stay (argparse auto-converts - to _)
    # No change needed - argparse handles --plan-file -> args.plan_file automatically

    if content != original_content:
        with open(script_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        return True
    return False


def main():
    """Standardize all gate scripts."""

    base_dir = Path(__file__).parent

    # Find all Python files in scripts/
    scripts = []
    scripts_dir = base_dir / "scripts"
    if scripts_dir.exists():
        scripts.extend(scripts_dir.glob("*.py"))
        wiring_dir = scripts_dir / "wiring"
        if wiring_dir.exists():
            scripts.extend(wiring_dir.glob("*.py"))

    # Also check root-level validate scripts
    scripts.extend(base_dir.glob("validate_*.py"))

    print(f"Checking {len(scripts)} scripts for argparse standardization...\n")

    updated = 0
    for script in sorted(scripts):
        if script.exists() and standardize_script(script):
            print(f"  ✓ {script.name}")
            updated += 1

    print(f"\n✓ Updated {updated} scripts to use --plan-file")


if __name__ == "__main__":
    main()
