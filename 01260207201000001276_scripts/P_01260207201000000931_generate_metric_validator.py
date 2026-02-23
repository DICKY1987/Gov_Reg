#!/usr/bin/env python3
"""Generate metric validator for monitoring data."""

import sys
from pathlib import Path


METRIC_VALIDATOR = '''#!/usr/bin/env python3
"""Metric validator for monitoring data."""

import json
import sys


REQUIRED_METRICS = [
    'uptime_percent',
    'avg_response_time_ms',
    'critical_errors',
    'requests_processed'
]

THRESHOLDS = {
    'uptime_percent': {'min': 99.9, 'max': 100},
    'avg_response_time_ms': {'min': 0, 'max': 200},
    'critical_errors': {'min': 0, 'max': 0}
}


def validate_metrics(metrics_path):
    """Validate monitoring metrics."""
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    errors = []
    
    # Check required metrics
    for req in REQUIRED_METRICS:
        if req not in metrics:
            errors.append(f"Missing required metric: {req}")
    
    # Check thresholds
    for metric, bounds in THRESHOLDS.items():
        if metric in metrics:
            value = metrics[metric]
            if 'min' in bounds and value < bounds['min']:
                errors.append(f"{metric} below threshold: {value} < {bounds['min']}")
            if 'max' in bounds and value > bounds['max']:
                errors.append(f"{metric} above threshold: {value} > {bounds['max']}")
    
    if errors:
        print(f"✗ METRIC VALIDATION FAILED ({len(errors)} error(s))")
        for e in errors:
            print(f"  - {e}")
        return 1
    else:
        print("✓ METRICS VALID")
        return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: metric_validator.py <metrics.json>")
        sys.exit(1)
    sys.exit(validate_metrics(sys.argv[1]))
'''


def generate_metric_validator(output_path):
    """Generate metric validator script."""
    print(f"Generating Metric Validator")
    print("=" * 70)
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(METRIC_VALIDATOR)
    
    try:
        output.chmod(0o755)
    except:
        pass
    
    print(f"✓ Validator generated: {output_path}")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'validators/metric_validator.py'
    sys.exit(generate_metric_validator(output))
