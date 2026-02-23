"""Phase 0.1d: Check third-party dependencies"""
import json
from datetime import datetime

deps = {}
for module in ['structlog', 'pydantic', 'watchdog']:
    try:
        __import__(module)
        deps[module] = {'status': 'available', 'fallback_needed': False}
    except ImportError:
        deps[module] = {
            'status': 'missing',
            'fallback_needed': True,
            'stdlib_alternative': {
                'structlog': 'logging',
                'pydantic': 'dataclasses + typing',
                'watchdog': 'none (remove watchdog code)'
            }.get(module)
        }

result = {
    'dependencies': deps,
    'action_required': any(d['fallback_needed'] for d in deps.values()),
    'timestamp': datetime.utcnow().isoformat() + 'Z'
}

with open('.migration/reports/DEPENDENCIES_STATUS.json', 'w') as f:
    json.dump(result, f, indent=2)

print('✓ Phase 0.1d: Dependencies checked')
for module, info in deps.items():
    print(f'  {module}: {info["status"]}')

if result['action_required']:
    print('\n⚠ Action required: Some dependencies missing')
