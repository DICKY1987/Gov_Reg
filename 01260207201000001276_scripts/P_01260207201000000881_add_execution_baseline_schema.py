#!/usr/bin/env python3
"""Add execution baseline schema for phase tracking."""

import sys
import json
from pathlib import Path


BASELINE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Execution Baseline Schema",
    "type": "object",
    "properties": {
        "baseline_id": {"type": "string", "pattern": "^BASELINE-[0-9]{14}$"},
        "phase": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "metrics": {
            "type": "object",
            "properties": {
                "performance_baseline_ms": {"type": "number"},
                "throughput_baseline_rps": {"type": "number"},
                "error_rate_baseline_percent": {"type": "number"}
            }
        },
        "thresholds": {
            "type": "object",
            "properties": {
                "max_drift_percent": {"type": "number", "default": 20},
                "alert_threshold_percent": {"type": "number", "default": 10}
            }
        }
    },
    "required": ["baseline_id", "phase", "timestamp", "metrics"]
}


def add_execution_baseline_schema(output_path):
    """Generate execution baseline schema."""
    print(f"Generating Execution Baseline Schema")
    print("=" * 70)
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(BASELINE_SCHEMA, f, indent=2)
    
    print(f"✓ Schema generated: {output_path}")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'schemas/execution_baseline.schema.json'
    sys.exit(add_execution_baseline_schema(output))
