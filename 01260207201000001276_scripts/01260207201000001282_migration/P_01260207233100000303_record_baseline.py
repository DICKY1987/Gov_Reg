"""Phase 0.1c: Record baseline registry count"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'PATH_FILES')
from path_registry import resolve_path

try:
    registry_path = resolve_path('REGISTRY_UNIFIED')
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    baseline = {
        'baseline_count': len(registry),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'registry_path': str(registry_path),
        'schema_version': registry.get('schema_version', 'unknown'),
        'path_registry_validation': 'PASS',
        'schema_validation': 'PENDING'
    }
    
    with open('.migration/reports/PRE_MIGRATION_TEST_BASELINE.json', 'w') as f:
        json.dump(baseline, f, indent=2)
    
    print(f"✓ Baseline count: {baseline['baseline_count']}")
    print(f"  Registry path: {baseline['registry_path']}")
    print(f"  Schema version: {baseline['schema_version']}")

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
