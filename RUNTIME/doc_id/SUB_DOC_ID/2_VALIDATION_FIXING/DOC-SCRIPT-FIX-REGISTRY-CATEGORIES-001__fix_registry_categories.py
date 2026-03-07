#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_LINK: DOC-SCRIPT-FIX-REGISTRY-CATEGORIES-001
"""
Fix DOC_ID_REGISTRY.yaml Category Assignments

PURPOSE: Re-categorize entries marked as 'unknown' by extracting category from doc_id prefix
PATTERN: PATTERN-DOC-ID-CATEGORY-FIX-001

USAGE:
    python doc_id/fix_registry_categories.py --dry-run
    python doc_id/fix_registry_categories.py
"""

import argparse
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = REPO_ROOT / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"

# Category mapping based on doc_id prefix
CATEGORY_MAP = {
    "CORE": "core",
    "ERROR": "error",
    "PAT": "patterns",
    "GUIDE": "guide",
    "SPEC": "spec",
    "TEST": "test",
    "SCRIPT": "script",
    "CONFIG": "config",
    "LEGACY": "legacy",
    "TASK": "task",
    "INFRA": "infra",
    "AIM": "aim",
    "PM": "pm",
    "ENGINE": "engine",
    "GUI": "gui",
    "GLOSSARY": "glossary",
}

# Special pattern mappings for non-standard doc_ids
SPECIAL_PATTERNS = {
    r"^DOC-TESTS-": "test",
    r"^DOC-SCRIPTS-": "script",
    r"^DOC-BATCH-": "patterns",
    r"^DOC-WORKTREE-": "guide",
    r"^DOC-SELF-HEAL-": "patterns",
    r"^DOC-ATOMIC-": "patterns",
    r"^DOC-MODULE-": "guide",
    r"^DOC-PHASE-": "guide",
    r"^DOC-QUICK-": "guide",
    r"^DOC-GLOSS-": "glossary",
    r"^DOC-REFACTOR-": "guide",
    r"^DOC-REG-": "guide",
    r"^DOC-LIB-": "guide",
    r"^DOC-VERIFY-": "script",
}


def extract_category_from_doc_id(doc_id: str) -> str:
    """Extract category from doc_id prefix (e.g., DOC-GUIDE-* -> guide)"""
    # Try standard pattern first
    match = re.match(r"^DOC-([A-Z]+)-", doc_id)
    if match:
        prefix = match.group(1)
        category = CATEGORY_MAP.get(prefix)
        if category:
            return category

    # Try special patterns
    for pattern, category in SPECIAL_PATTERNS.items():
        if re.match(pattern, doc_id):
            return category

    return "unknown"


def fix_categories(dry_run: bool = True):
    """Fix category assignments in registry"""
    print("=== Fixing DOC_ID_REGISTRY.yaml Categories ===\n")

    # Load registry
    if not REGISTRY_PATH.exists():
        print(f"❌ Registry not found: {REGISTRY_PATH}")
        sys.exit(1)

    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))

    # Track changes
    fixed_count = 0
    category_changes = Counter()

    # Process each doc entry
    for doc in registry.get("docs", []):
        if doc.get("category") == "unknown":
            doc_id = doc.get("doc_id", "")
            new_category = extract_category_from_doc_id(doc_id)

            if new_category != "unknown":
                doc["category"] = new_category
                category_changes[new_category] += 1
                fixed_count += 1

    # Recalculate category counts
    actual_counts = Counter()
    for doc in registry.get("docs", []):
        cat = doc.get("category", "unknown")
        actual_counts[cat] += 1

    # Update metadata
    if "categories" in registry:
        for cat_key, cat_data in registry["categories"].items():
            if isinstance(cat_data, dict):
                actual = actual_counts.get(cat_key, 0)
                cat_data["count"] = actual

    # Update total count
    if "metadata" in registry:
        registry["metadata"]["total_docs"] = len(registry.get("docs", []))
        registry["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    # Report
    print(f"{'DRY RUN: Would fix' if dry_run else 'Fixed'} {fixed_count} entries\n")
    print("Category changes:")
    for cat, count in sorted(category_changes.items()):
        print(f"  {cat}: +{count}")

    print(f"\nActual category counts:")
    for cat, count in sorted(actual_counts.items()):
        print(f"  {cat}: {count}")

    remaining_unknown = actual_counts.get("unknown", 0)
    if remaining_unknown > 0:
        print(f"\n⚠️  Still {remaining_unknown} entries with category 'unknown'")
    else:
        print(f"\n✅ All entries categorized!")

    # Save if not dry run
    if not dry_run:
        REGISTRY_PATH.write_text(
            yaml.dump(registry, sort_keys=False, allow_unicode=True),
            encoding="utf-8"
        )
        print(f"\n✅ Registry updated: {REGISTRY_PATH}")
    else:
        print(f"\n💡 Run without --dry-run to apply changes")


def main():
    parser = argparse.ArgumentParser(description="Fix Registry Categories")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")

    args = parser.parse_args()
    fix_categories(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
