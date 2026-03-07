#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-1005
"""
Unified sync validator for all ID types (doc_id, trigger_id, pattern_id)
Phase 1 Task T1.4
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Set, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import REPO_ROOT

def load_doc_id_data() -> Tuple[Set[str], Set[str]]:
    """Load doc_id registry and inventory"""
    registry_path = Path(__file__).parent / "DOC_ID_REGISTRY.yaml"
    inventory_path = Path(__file__).parent / "docs_inventory.jsonl"

    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    registry_ids = {doc['doc_id'] for doc in registry.get('documents', []) if 'doc_id' in doc}

    # Load inventory
    inventory_ids = set()
    with open(inventory_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get('doc_id'):
                    inventory_ids.add(entry['doc_id'])
            except json.JSONDecodeError:
                continue

    return registry_ids, inventory_ids

def load_trigger_id_data() -> Tuple[Set[str], Set[str]]:
    """Load trigger_id registry and inventory"""
    base_path = Path(__file__).parent.parent / "trigger_id"
    registry_path = base_path / "5_REGISTRY_DATA" / "TRIGGER_ID_REGISTRY.yaml"
    inventory_path = base_path / "5_REGISTRY_DATA" / "triggers_inventory.jsonl"

    if not registry_path.exists() or not inventory_path.exists():
        return set(), set()

    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    registry_ids = {t['trigger_id'] for t in registry.get('triggers', []) if 'trigger_id' in t}

    # Load inventory
    inventory_ids = set()
    with open(inventory_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                # Try type-specific field first, then fall back to 'id'
                trigger_id = entry.get('trigger_id') or entry.get('id')
                if trigger_id:
                    inventory_ids.add(trigger_id)
            except json.JSONDecodeError:
                continue

    return registry_ids, inventory_ids

def load_pattern_id_data() -> Tuple[Set[str], Set[str]]:
    """Load pattern_id registry and inventory"""
    base_path = Path(__file__).parent.parent / "pattern_id"
    registry_path = base_path / "5_REGISTRY_DATA" / "PATTERN_ID_REGISTRY.yaml"
    inventory_path = base_path / "5_REGISTRY_DATA" / "patterns_inventory.jsonl"

    if not registry_path.exists() or not inventory_path.exists():
        return set(), set()

    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    registry_ids = {p['pattern_id'] for p in registry.get('patterns', []) if 'pattern_id' in p}

    # Load inventory
    inventory_ids = set()
    with open(inventory_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                # Try type-specific field first, then fall back to 'id'
                pattern_id = entry.get('pattern_id') or entry.get('id')
                if pattern_id:
                    inventory_ids.add(pattern_id)
            except json.JSONDecodeError:
                continue

    return registry_ids, inventory_ids

def check_sync(id_type: str, registry_ids: Set[str], inventory_ids: Set[str]) -> Dict:
    """Check sync status for an ID type"""
    only_in_registry = registry_ids - inventory_ids
    only_in_inventory = inventory_ids - registry_ids
    in_both = registry_ids & inventory_ids

    drift_count = len(only_in_registry) + len(only_in_inventory)

    return {
        'id_type': id_type,
        'total_registry': len(registry_ids),
        'total_inventory': len(inventory_ids),
        'in_both': len(in_both),
        'only_in_registry': len(only_in_registry),
        'only_in_inventory': len(only_in_inventory),
        'drift_count': drift_count,
        'in_sync': drift_count == 0
    }

def main():
    print("🔄 Unified Registry Sync Validator")
    print("=" * 60)

    all_in_sync = True
    results = []

    # Check doc_id
    print("\n📄 Checking doc_id...")
    doc_reg, doc_inv = load_doc_id_data()
    doc_result = check_sync('doc_id', doc_reg, doc_inv)
    results.append(doc_result)

    # Check trigger_id
    print("\n🎯 Checking trigger_id...")
    trig_reg, trig_inv = load_trigger_id_data()
    trig_result = check_sync('trigger_id', trig_reg, trig_inv)
    results.append(trig_result)

    # Check pattern_id
    print("\n🔷 Checking pattern_id...")
    pat_reg, pat_inv = load_pattern_id_data()
    pat_result = check_sync('pattern_id', pat_reg, pat_inv)
    results.append(pat_result)

    # Display results
    print("\n" + "=" * 60)
    print("SYNC STATUS REPORT")
    print("=" * 60)

    for result in results:
        status = "✅ IN SYNC" if result['in_sync'] else "❌ DRIFT DETECTED"
        print(f"\n{result['id_type'].upper()}: {status}")
        print(f"  Registry:  {result['total_registry']:4d} IDs")
        print(f"  Inventory: {result['total_inventory']:4d} IDs")
        print(f"  In Both:   {result['in_both']:4d} IDs")

        if not result['in_sync']:
            print(f"  ⚠️  Only in registry:  {result['only_in_registry']}")
            print(f"  ⚠️  Only in inventory: {result['only_in_inventory']}")
            all_in_sync = False

    print("\n" + "=" * 60)
    if all_in_sync:
        print("✅ ALL ID TYPES IN SYNC")
        return 0
    else:
        print("❌ SYNC ISSUES DETECTED - Review drift above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
