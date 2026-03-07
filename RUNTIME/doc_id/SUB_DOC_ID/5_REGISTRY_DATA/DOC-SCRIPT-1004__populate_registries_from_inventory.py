#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-1004
"""
Populate empty registries from their inventories
"""

import json
import sys
import yaml
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import REPO_ROOT

def populate_trigger_registry():
    """Populate TRIGGER_ID_REGISTRY from triggers_inventory.jsonl"""
    base_path = Path(__file__).parent.parent / "trigger_id" / "5_REGISTRY_DATA"
    registry_path = base_path / "TRIGGER_ID_REGISTRY.yaml"
    inventory_path = base_path / "triggers_inventory.jsonl"

    if not inventory_path.exists():
        print(f"❌ Inventory not found: {inventory_path}")
        return

    # Load existing registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    # Load inventory
    triggers = []
    with open(inventory_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                trigger_id = entry.get('trigger_id')
                if trigger_id:
                    triggers.append({
                        'trigger_id': trigger_id,
                        'name': entry.get('name', ''),
                        'type': entry.get('trigger_type', entry.get('type', '')),
                        'status': entry.get('status', 'active'),
                        'file_path': entry.get('file_path', ''),
                        'discovered': entry.get('discovered', datetime.now().isoformat())
                    })
            except json.JSONDecodeError:
                continue

    # Update registry
    registry['triggers'] = triggers
    registry['metadata']['total_triggers'] = len(triggers)
    registry['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    # Save registry
    with open(registry_path, 'w', encoding='utf-8') as f:
        yaml.dump(registry, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Populated trigger registry: {len(triggers)} triggers")

def populate_pattern_registry():
    """Populate PATTERN_ID_REGISTRY from patterns_inventory.jsonl"""
    base_path = Path(__file__).parent.parent / "pattern_id" / "5_REGISTRY_DATA"
    registry_path = base_path / "PATTERN_ID_REGISTRY.yaml"
    inventory_path = base_path / "patterns_inventory.jsonl"

    if not inventory_path.exists():
        print(f"❌ Inventory not found: {inventory_path}")
        return

    # Load existing registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    # Load inventory
    patterns = []
    with open(inventory_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                pattern_id = entry.get('pattern_id')
                if pattern_id:
                    patterns.append({
                        'pattern_id': pattern_id,
                        'name': entry.get('name', entry.get('pattern_name', '')),
                        'type': entry.get('type', ''),
                        'status': entry.get('status', 'active'),
                        'file_path': entry.get('file_path', ''),
                        'discovered': entry.get('discovered', datetime.now().isoformat())
                    })
            except json.JSONDecodeError:
                continue

    # Update registry
    registry['patterns'] = patterns
    registry['metadata']['total_patterns'] = len(patterns)
    registry['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    # Save registry
    with open(registry_path, 'w', encoding='utf-8') as f:
        yaml.dump(registry, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Populated pattern registry: {len(patterns)} patterns")

def main():
    print("🔄 Populating registries from inventories...")
    print()

    populate_trigger_registry()
    populate_pattern_registry()

    print()
    print("✅ Registry population complete")

if __name__ == "__main__":
    main()
