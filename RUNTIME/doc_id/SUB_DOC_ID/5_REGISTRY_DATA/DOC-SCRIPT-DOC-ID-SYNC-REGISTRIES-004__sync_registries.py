#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_LINK: DOC-SCRIPT-DOC-ID-SYNC-REGISTRIES-004
"""
Registry Synchronization Tool

PURPOSE: Sync doc_ids between DOC_ID_REGISTRY.yaml and docs_inventory.jsonl
PATTERN: PATTERN-DOC-ID-SYNC-004

USAGE:
    python doc_id/sync_registries.py check
    python doc_id/sync_registries.py sync --dry-run
    python doc_id/sync_registries.py sync
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Set

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, REGISTRY_PATH, INVENTORY_PATH
from common.utils import load_yaml, save_yaml, load_jsonl

# Category mapping
CATEGORY_MAP = {
    "CORE": "core", "ERROR": "error", "PAT": "patterns", "GUIDE": "guide",
    "SPEC": "spec", "TEST": "test", "SCRIPT": "script", "CONFIG": "config",
    "LEGACY": "legacy", "TASK": "task", "INFRA": "infra", "AIM": "aim",
    "PM": "pm", "ENGINE": "engine", "GUI": "gui", "GLOSSARY": "glossary",
}

SPECIAL_PATTERNS = {
    r"^DOC-TESTS-": "test", r"^DOC-SCRIPTS-": "script", r"^DOC-BATCH-": "patterns",
    r"^DOC-WORKTREE-": "guide", r"^DOC-SELF-HEAL-": "patterns", r"^DOC-ATOMIC-": "patterns",
    r"^DOC-MODULE-": "guide", r"^DOC-PHASE-": "guide", r"^DOC-QUICK-": "guide",
    r"^DOC-GLOSS-": "glossary", r"^DOC-REFACTOR-": "guide", r"^DOC-REG-": "guide",
    r"^DOC-LIB-": "guide", r"^DOC-VERIFY-": "script",
}


def extract_category_from_doc_id(doc_id: str) -> str:
    """Extract category from doc_id prefix"""
    import re
    match = re.match(r"^DOC-([A-Z]+)-", doc_id)
    if match:
        category = CATEGORY_MAP.get(match.group(1))
        if category:
            return category
    for pattern, category in SPECIAL_PATTERNS.items():
        if re.match(pattern, doc_id):
            return category
    return "unknown"


def load_registry() -> Dict:
    """Load DOC_ID_REGISTRY.yaml"""
    if not REGISTRY_PATH.exists():
        return {"docs": []}
    return load_yaml(REGISTRY_PATH)


def load_inventory() -> Set[str]:
    """Load doc_ids from docs_inventory.jsonl"""
    doc_ids = set()
    if not INVENTORY_PATH.exists():
        return doc_ids

    for line in INVENTORY_PATH.read_text(encoding="utf-8").strip().split("\n"):
        if line:
            try:
                entry = json.loads(line)
                if entry.get("doc_id"):
                    doc_ids.add(entry["doc_id"])
            except json.JSONDecodeError:
                continue
    return doc_ids


def check_sync() -> Dict:
    """Check synchronization status"""
    registry = load_registry()
    inventory_ids = load_inventory()

    # Extract doc_ids from registry - now under 'documents' key
    registry_ids = {
        doc["doc_id"] for doc in registry.get("documents", []) if "doc_id" in doc
    }

    only_in_registry = registry_ids - inventory_ids
    only_in_inventory = inventory_ids - registry_ids
    in_both = registry_ids & inventory_ids

    return {
        "in_both": len(in_both),
        "only_registry": list(only_in_registry),
        "only_inventory": list(only_in_inventory),
        "total_registry": len(registry_ids),
        "total_inventory": len(inventory_ids),
    }


def sync_registries(dry_run: bool = True, auto_sync: bool = False, max_drift: int = 50):
    """Synchronize registries with optional auto-sync"""
    status = check_sync()

    drift_count = len(status['only_registry']) + len(status['only_inventory'])

    print("=== Registry Synchronization ===")
    print(f"In both: {status['in_both']}")
    print(f"Only in registry: {len(status['only_registry'])}")
    print(f"Only in inventory: {len(status['only_inventory'])}")
    print(f"Total drift: {drift_count}")

    # PATTERN: EXEC-002 Batch Validation with threshold
    if auto_sync:
        if drift_count <= max_drift:
            print(f"\n✅ Auto-syncing (drift {drift_count} ≤ threshold {max_drift})")
            # Proceed with sync below
        else:
            print(f"\n❌ Drift {drift_count} exceeds threshold {max_drift}")
            print("Manual review required")
            sys.exit(1)
    else:
        if drift_count > 0:
            print(f"\nRun with --auto-sync to enable automatic sync (if drift ≤ {max_drift})")

    if status["only_inventory"]:
        print(
            f"\n{'DRY RUN: Would add' if dry_run else 'Adding'} {len(status['only_inventory'])} entries to registry..."
        )

        if not dry_run:
            registry = load_registry()
            for doc_id in status["only_inventory"]:
                category = extract_category_from_doc_id(doc_id)
                registry["docs"].append(
                    {
                        "doc_id": doc_id,
                        "category": category,
                        "status": "active",
                        "source": "inventory_sync",
                    }
                )

            save_yaml(REGISTRY_PATH, registry)
            print(f"✅ Registry updated: {REGISTRY_PATH}")

    if status["only_registry"]:
        print(
            f"\n⚠️  {len(status['only_registry'])} doc_ids in registry not found in inventory"
        )
        print("Run doc_id_scanner.py to update inventory")

    # Exit successfully
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Registry Sync Tool")
    parser.add_argument("action", choices=["check", "sync"], help="Action to perform")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--auto-sync", action="store_true",
                       help="Sync automatically if drift below threshold")
    parser.add_argument("--max-drift", type=int, default=50,
                       help="Maximum drift for auto-sync (default: 50)")

    args = parser.parse_args()

    if args.action == "check":
        status = check_sync()
        print(json.dumps(status, indent=2))
    elif args.action == "sync":
        sync_registries(dry_run=args.dry_run, auto_sync=args.auto_sync,
                       max_drift=args.max_drift)


if __name__ == "__main__":
    main()
