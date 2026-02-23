#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-1014
"""
Sync DOC_ID_REGISTRY with docs_inventory.jsonl
"""

import json
import sys
import yaml
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import REPO_ROOT

def sync_doc_id_registry():
    """Sync DOC_ID_REGISTRY with docs_inventory.jsonl"""
    registry_path = Path(__file__).parent / "DOC_ID_REGISTRY.yaml"
    inventory_path = Path(__file__).parent / "docs_inventory.jsonl"

    print(f"📂 Loading registry: {registry_path.name}")
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    print(f"📂 Loading inventory: {inventory_path.name}")

    # Build inventory dict
    inventory_docs = {}
    with open(inventory_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                doc_id = entry.get('doc_id')
                if doc_id:
                    inventory_docs[doc_id] = entry
            except json.JSONDecodeError:
                continue

    print(f"📊 Registry: {len(registry.get('documents', []))} docs")
    print(f"📊 Inventory: {len(inventory_docs)} docs")

    # Build registry dict
    registry_docs = {doc['doc_id']: doc for doc in registry.get('documents', []) if 'doc_id' in doc}

    # Find differences
    only_in_registry = set(registry_docs.keys()) - set(inventory_docs.keys())
    only_in_inventory = set(inventory_docs.keys()) - set(registry_docs.keys())

    print(f"\n🔍 Analysis:")
    print(f"  ⚠️  Only in registry: {len(only_in_registry)}")
    print(f"  ⚠️  Only in inventory: {len(only_in_inventory)}")

    if only_in_inventory:
        print(f"\n➕ Adding {len(only_in_inventory)} new docs from inventory...")
        for doc_id in sorted(only_in_inventory):
            inv_entry = inventory_docs[doc_id]
            # Create registry entry from inventory
            registry_entry = {
                'doc_id': doc_id,
                'category': inv_entry.get('category', 'unknown'),
                'name': inv_entry.get('name', ''),
                'title': inv_entry.get('title', inv_entry.get('name', '')),
                'status': inv_entry.get('status', 'active'),
                'artifacts': [{'type': 'source', 'path': inv_entry.get('file_path', '')}] if inv_entry.get('file_path') else [],
                'created': inv_entry.get('created', datetime.now().strftime('%Y-%m-%d')),
                'last_modified': inv_entry.get('last_modified', datetime.now().strftime('%Y-%m-%d')),
                'tags': inv_entry.get('tags', [])
            }
            registry['documents'].append(registry_entry)

    if only_in_registry:
        print(f"\n🗑️  {len(only_in_registry)} docs in registry but not in inventory (keeping them)")

    # Update metadata
    registry['metadata']['total_docs'] = len(registry['documents'])
    registry['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    # Save registry
    print(f"\n💾 Saving updated registry...")
    with open(registry_path, 'w', encoding='utf-8') as f:
        yaml.dump(registry, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"✅ Registry updated: {len(registry['documents'])} total docs")

def main():
    print("🔄 Syncing DOC_ID_REGISTRY with inventory...\n")
    sync_doc_id_registry()
    print("\n✅ Sync complete")

if __name__ == "__main__":
    main()
