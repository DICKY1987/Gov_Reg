"""Phase 0.2a: Locate ID Counter"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'PATH_FILES')
from path_registry import resolve_path

try:
    # Try to resolve from path_index.yaml semantic key
    id_counter_path = resolve_path('ID_COUNTER')
    exists = Path(id_counter_path).exists()

    # Load and inspect
    if exists:
        with open(id_counter_path, 'r', encoding='utf-8') as f:
            id_counter = json.load(f)

        next_id = id_counter.get('next_available_id', id_counter.get('current_id', 'unknown'))
    else:
        next_id = None

    result = {
        'primary_path': str(id_counter_path),
        'primary_exists': exists,
        'next_available_id': next_id,
        'source': 'path_index.yaml',
        'action': 'backup' if exists else 'reconstruct',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

except Exception as e:
    # Fallback: check known location
    fallback_path = Path('REGISTRY/01999000042260124026_ID_COUNTER.json')
    fallback_exists = fallback_path.exists()

    if fallback_exists:
        with open(fallback_path, 'r', encoding='utf-8') as f:
            id_counter = json.load(f)
        next_id = id_counter.get('next_available_id', id_counter.get('current_id', 'unknown'))
    else:
        next_id = None

    result = {
        'primary_path': None,
        'primary_exists': False,
        'fallback_path': str(fallback_path),
        'fallback_exists': fallback_exists,
        'next_available_id': next_id,
        'source': 'fallback' if fallback_exists else 'missing',
        'action': 'backup' if fallback_exists else 'reconstruct',
        'error': str(e),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

with open('.migration/reports/ID_COUNTER_SOURCE.json', 'w') as f:
    json.dump(result, f, indent=2)

print(f"✓ Phase 0.2a: ID Counter located")
print(f"  Source: {result['source']}")
print(f"  Path: {result.get('primary_path') or result.get('fallback_path')}")
print(f"  Exists: {result.get('primary_exists') or result.get('fallback_exists')}")
if result.get('next_available_id'):
    print(f"  Next available ID: {result['next_available_id']}")
print(f"  Action: {result['action']}")
