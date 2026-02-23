#!/usr/bin/env python3
"""Enable migration phase in the system."""

import sys
import json
from pathlib import Path
from datetime import datetime


VALID_PHASES = [
    'PHASE_0_PREP',
    'PHASE_1_FOUNDATION',
    'PHASE_2_CORE',
    'PHASE_3_REGISTRY',
    'PHASE_4_OPTIMIZATION',
    'PHASE_5_COMPLETE'
]


def enable_migration_phase(phase, output_path=None):
    """Enable a migration phase."""
    print(f"Migration Phase Enablement")
    print("=" * 70)
    
    if phase not in VALID_PHASES:
        print(f"ERROR: Invalid phase '{phase}'")
        print(f"Valid phases: {', '.join(VALID_PHASES)}")
        return 1
    
    print(f"Phase: {phase}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    
    phase_config = {
        'phase': phase,
        'enabled_at': datetime.utcnow().isoformat() + 'Z',
        'status': 'ENABLED',
        'previous_phase': None,
        'features_enabled': []
    }
    
    # Phase-specific features
    if phase == 'PHASE_0_PREP':
        phase_config['features_enabled'] = ['canonical_hash']
    elif phase == 'PHASE_1_FOUNDATION':
        phase_config['features_enabled'] = ['registry_writer', 'cas_validation']
    elif phase == 'PHASE_2_CORE':
        phase_config['features_enabled'] = ['conflict_validators', 'cross_phase_validation']
    elif phase == 'PHASE_3_REGISTRY':
        phase_config['features_enabled'] = ['schema_v3', 'lifecycle_tracking', 'ssot_marking']
    elif phase == 'PHASE_4_OPTIMIZATION':
        phase_config['features_enabled'] = ['performance_optimization', 'advanced_monitoring']
    elif phase == 'PHASE_5_COMPLETE':
        phase_config['features_enabled'] = ['all_features']
    
    print(f"\nFeatures Enabled:")
    for feature in phase_config['features_enabled']:
        print(f"  ✓ {feature}")
    
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(phase_config, f, indent=2)
        print(f"\nPhase configuration saved: {output_path}")
    
    print("=" * 70)
    print(f"✓ PHASE {phase} ENABLED")
    
    return 0


if __name__ == '__main__':
    phase = None
    output_path = None
    
    for i, arg in enumerate(sys.argv):
        if arg == '--phase' and i + 1 < len(sys.argv):
            phase = sys.argv[i + 1]
        elif arg == '--output' and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
    
    if not phase:
        print("Usage: python enable_migration_phase.py --phase <phase_name> [--output <path>]")
        sys.exit(1)
    
    sys.exit(enable_migration_phase(phase, output_path))
