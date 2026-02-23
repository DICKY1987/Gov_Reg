#!/usr/bin/env python3
"""Generate drift validator for baseline comparison."""

import sys
import json
from pathlib import Path


DRIFT_VALIDATOR = '''#!/usr/bin/env python3
"""Drift validator for baseline metrics."""

import json
import sys


def validate_drift(baseline_path, current_path, threshold_percent=20):
    """Validate drift from baseline."""
    with open(baseline_path, 'r') as f:
        baseline = json.load(f)
    with open(current_path, 'r') as f:
        current = json.load(f)
    
    baseline_metrics = baseline.get('metrics', {})
    current_metrics = current.get('metrics', {})
    
    drifts = []
    for key in baseline_metrics:
        if key in current_metrics:
            base_val = baseline_metrics[key]
            curr_val = current_metrics[key]
            if base_val > 0:
                drift_percent = abs((curr_val - base_val) / base_val * 100)
                if drift_percent > threshold_percent:
                    drifts.append({
                        'metric': key,
                        'baseline': base_val,
                        'current': curr_val,
                        'drift_percent': drift_percent
                    })
    
    if drifts:
        print(f"✗ DRIFT DETECTED ({len(drifts)} metrics)")
        for d in drifts:
            print(f"  {d['metric']}: {d['drift_percent']:.1f}% drift")
        return 1
    else:
        print("✓ NO SIGNIFICANT DRIFT")
        return 0


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: drift_validator.py <baseline.json> <current.json> [threshold]")
        sys.exit(1)
    
    baseline = sys.argv[1]
    current = sys.argv[2]
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
    sys.exit(validate_drift(baseline, current, threshold))
'''


def generate_drift_validator(output_path):
    """Generate drift validator script."""
    print(f"Generating Drift Validator")
    print("=" * 70)
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(DRIFT_VALIDATOR)
    
    try:
        output.chmod(0o755)
    except:
        pass
    
    print(f"✓ Validator generated: {output_path}")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'validators/drift_validator.py'
    sys.exit(generate_drift_validator(output))
