#!/usr/bin/env python3
# DOC_LINK: DOC-TOOL-UNIFIED-SYNC-001
# DOC_ID: DOC-TOOL-UNIFIED-SYNC-001
"""
doc_id: DOC-TOOL-UNIFIED-SYNC-001
Unified sync system for all ID types
"""

import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Public API
__all__ = ['sync_all', 'sync_id_type', 'sync_all_registries', 'REGISTRY_CONFIGS']

# Registry configurations for all ID types
REGISTRY_CONFIGS = {
    'doc_id': {
        'registry_file': 'RUNTIME/doc_id/SUB_DOC_ID/5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml',
        'inventory_file': 'RUNTIME/doc_id/SUB_DOC_ID/5_REGISTRY_DATA/docs_inventory.jsonl',
        'scanner': 'RUNTIME/doc_id/SUB_DOC_ID/1_CORE_OPERATIONS/doc_id_scanner.py',
        'enabled': True
    },
    'trigger_id': {
        'registry_file': 'RUNTIME/doc_id/SUB_DOC_ID/trigger_id/5_REGISTRY_DATA/TRG_ID_REGISTRY.yaml',
        'inventory_file': 'RUNTIME/doc_id/SUB_DOC_ID/trigger_id/5_REGISTRY_DATA/triggers_inventory.jsonl',
        'scanner': 'RUNTIME/doc_id/SUB_DOC_ID/trigger_id/1_CORE_OPERATIONS/trigger_id_scanner.py',
        'enabled': True
    },
    'pattern_id': {
        'registry_file': 'RUNTIME/doc_id/SUB_DOC_ID/pattern_id/5_REGISTRY_DATA/PAT_ID_REGISTRY.yaml',
        'inventory_file': 'RUNTIME/doc_id/SUB_DOC_ID/pattern_id/5_REGISTRY_DATA/patterns_inventory.jsonl',
        'scanner': 'RUNTIME/doc_id/SUB_DOC_ID/pattern_id/1_CORE_OPERATIONS/pattern_id_scanner.py',
        'enabled': False  # Scanner doesn't exist yet
    },
    'dir_id': {
        'registry_file': 'RUNTIME/path_registry/SUB_PATH_REGISTRY/directory_registry.yaml',
        'enabled': False  # Different sync mechanism
    }
}

def sync_id_type(id_type, config, repo_root):
    """Sync a single ID type"""
    result = {
        'id_type': id_type,
        'success': False,
        'registry_count': 0,
        'inventory_count': 0,
        'drift': [],
        'missing': [],
        'error': None
    }

    try:
        registry_path = repo_root / config['registry_file']

        if not registry_path.exists():
            result['error'] = f"Registry not found: {registry_path}"
            return result

        # Load registry
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f)

        # Count registry entries
        if id_type == 'doc_id':
            result['registry_count'] = len(registry.get('documents', []))
        elif id_type == 'trigger_id':
            result['registry_count'] = len(registry.get('triggers', []))
        elif id_type == 'pattern_id':
            result['registry_count'] = len(registry.get('patterns', []))

        # Load inventory if available
        inventory_path = repo_root / config.get('inventory_file', '')
        if inventory_path.exists():
            with open(inventory_path, 'r', encoding='utf-8') as f:
                inventory = [json.loads(line) for line in f if line.strip()]
            result['inventory_count'] = len(inventory)

            # Compare registry vs inventory (basic drift detection)
            registry_ids = set()
            inventory_ids = set()

            if id_type == 'doc_id':
                registry_ids = {d.get('doc_id') for d in registry.get('documents', []) if d.get('doc_id')}
                inventory_ids = {item.get('doc_id') for item in inventory if item.get('doc_id')}
            elif id_type == 'trigger_id':
                registry_ids = {t.get('trigger_id') for t in registry.get('triggers', []) if t.get('trigger_id')}
                inventory_ids = {item.get('trigger_id') for item in inventory if item.get('trigger_id')}
            elif id_type == 'pattern_id':
                registry_ids = {p.get('pattern_id') for p in registry.get('patterns', []) if p.get('pattern_id')}
                inventory_ids = {item.get('pattern_id') for item in inventory if item.get('pattern_id')}

            result['drift'] = list(registry_ids - inventory_ids)  # In registry but not inventory
            result['missing'] = list(inventory_ids - registry_ids)  # In inventory but not registry

        result['success'] = True

    except Exception as e:
        result['error'] = str(e)

    return result

def sync_all(parallel=True):
    """Sync all enabled ID types"""
    repo_root = Path(__file__).parent.parent.parent.parent

    enabled_types = {k: v for k, v in REGISTRY_CONFIGS.items() if v.get('enabled')}

    print(f"\n{'='*80}")
    print(f"UNIFIED SYNC - {len(enabled_types)} ID types")
    print(f"{'='*80}\n")

    results = []

    if parallel and len(enabled_types) > 1:
        # Parallel sync
        with ThreadPoolExecutor(max_workers=min(4, len(enabled_types))) as executor:
            futures = {
                executor.submit(sync_id_type, id_type, config, repo_root): id_type
                for id_type, config in enabled_types.items()
            }

            for future in as_completed(futures):
                results.append(future.result())
    else:
        # Sequential sync
        for id_type, config in enabled_types.items():
            results.append(sync_id_type(id_type, config, repo_root))

    # Report results
    total_success = sum(1 for r in results if r['success'])
    total_registry = sum(r['registry_count'] for r in results)
    total_inventory = sum(r['inventory_count'] for r in results)

    for result in results:
        icon = "✅" if result['success'] else "❌"
        print(f"{icon} {result['id_type']:<15} Registry: {result['registry_count']:>5} IDs")

        if result['inventory_count'] > 0:
            print(f"   {'':15} Inventory: {result['inventory_count']:>5} files")

        if result['drift']:
            print(f"   ⚠️  {len(result['drift'])} IDs in registry but not in inventory (drift)")

        if result['missing']:
            print(f"   ⚠️  {len(result['missing'])} IDs in inventory but not in registry (missing)")

        if result['error']:
            print(f"   ❌ Error: {result['error']}")

        print()

    print(f"{'='*80}")
    print(f"SUMMARY: {total_success}/{len(results)} types synced successfully")
    print(f"Total Registry IDs: {total_registry}")
    print(f"Total Inventory Files: {total_inventory}")
    print(f"{'='*80}\n")

    return {
        'success': total_success == len(results),
        'results': results,
        'total_registry': total_registry,
        'total_inventory': total_inventory
    }

# Alias for backward compatibility
sync_all_registries = sync_all

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Unified sync for all ID types')
    parser.add_argument('--sequential', action='store_true', help='Run synchronously (not parallel)')
    parser.add_argument('--type', help='Sync only this ID type')
    parser.add_argument('--json', action='store_true', help='Output JSON format')

    args = parser.parse_args()

    if args.type:
        if args.type not in REGISTRY_CONFIGS:
            print(f"❌ Unknown ID type: {args.type}")
            return 1

        if not REGISTRY_CONFIGS[args.type].get('enabled'):
            print(f"⚠️  ID type '{args.type}' is not enabled for sync")
            return 1

        repo_root = Path(__file__).parent.parent.parent.parent
        result = sync_id_type(args.type, REGISTRY_CONFIGS[args.type], repo_root)

        if args.json:
            print(json.dumps(result, indent=2))

        return 0 if result['success'] else 1

    # Sync all
    summary = sync_all(parallel=not args.sequential)

    if args.json:
        print(json.dumps(summary, indent=2))

    return 0 if summary['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
