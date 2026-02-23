#!/usr/bin/env python3
"""Generate merge conflict resolver."""

import sys
from pathlib import Path


MERGE_RESOLVER = '''#!/usr/bin/env python3
"""Merge conflict resolver with policy-based strategies."""

import json
import sys
from datetime import datetime


STRATEGIES = {
    "NEWEST_WINS": lambda base, theirs, ours: theirs if theirs.get('timestamp', '') > ours.get('timestamp', '') else ours,
    "MANUAL": lambda base, theirs, ours: {"conflict": True, "requires_manual_resolution": True},
    "MERGE_ARRAY": lambda base, theirs, ours: list(set(theirs + ours)) if isinstance(theirs, list) and isinstance(ours, list) else theirs,
    "SSOT_PROTECTED": lambda base, theirs, ours: base
}


def resolve_conflicts(base_path, theirs_path, ours_path, policy_path, output_path):
    """Resolve merge conflicts using policies."""
    with open(base_path, 'r') as f:
        base = json.load(f)
    with open(theirs_path, 'r') as f:
        theirs = json.load(f)
    with open(ours_path, 'r') as f:
        ours = json.load(f)
    with open(policy_path, 'r') as f:
        policies = json.load(f)
    
    result = {}
    conflicts = []
    
    for key in set(list(base.keys()) + list(theirs.keys()) + list(ours.keys())):
        if key not in theirs or key not in ours or theirs[key] == ours[key]:
            result[key] = theirs.get(key, ours.get(key))
        else:
            policy = next((p for p in policies if p['field'] == key), None)
            if policy:
                strategy = STRATEGIES.get(policy['strategy'], STRATEGIES['MANUAL'])
                result[key] = strategy(base.get(key), theirs[key], ours[key])
                if isinstance(result[key], dict) and result[key].get('conflict'):
                    conflicts.append(key)
            else:
                conflicts.append(key)
                result[key] = {"conflict": True, "theirs": theirs[key], "ours": ours[key]}
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    if conflicts:
        print(f"⚠ {len(conflicts)} conflict(s) require manual resolution")
        return 1
    else:
        print(f"✓ Merge completed successfully")
        return 0


if __name__ == '__main__':
    if len(sys.argv) < 6:
        print("Usage: merge_resolver.py <base> <theirs> <ours> <policy> <output>")
        sys.exit(1)
    sys.exit(resolve_conflicts(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
'''


def generate_merge_resolver(output_path):
    """Generate merge resolver script."""
    print(f"Generating Merge Resolver")
    print("=" * 70)
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(MERGE_RESOLVER)
    
    try:
        output.chmod(0o755)
    except:
        pass
    
    print(f"✓ Resolver generated: {output_path}")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'validators/merge_resolver.py'
    sys.exit(generate_merge_resolver(output))
