#!/usr/bin/env python3
# DOC_LINK: DOC-PATTERN-REPORTING-REPORT-001
"""
Pattern ID Reporting
Generates pattern_id status and coverage reports
"""
# DOC_ID: DOC-PATTERN-REPORTING-REPORT-001

import json
import sys
import yaml
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def generate_report():
    """Generate pattern_id status report."""
    base = Path(__file__).parent.parent
    registry_path = base / '5_REGISTRY_DATA' / 'PAT_ID_REGISTRY.yaml'
    inventory_path = base / '5_REGISTRY_DATA' / 'pattern_id_inventory.jsonl'

    # Load data
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    patterns = registry.get('patterns', [])

    inventory_count = 0
    if inventory_path.exists():
        with open(inventory_path, 'r', encoding='utf-8') as f:
            inventory_count = sum(1 for line in f if line.strip())

    # Count complete triads (spec + executor + test)
    complete_triads = 0
    for pattern in patterns:
        files = pattern.get('files', {})
        has_spec = bool(files.get('spec'))
        has_executor = bool(files.get('executor'))
        has_test = bool(files.get('test'))
        if has_spec and has_executor and has_test:
            complete_triads += 1

    # Generate report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "pattern_id_status": {
            "total_patterns": len(patterns),
            "complete_triads": complete_triads,
            "triad_percentage": round(complete_triads / len(patterns) * 100, 1) if patterns else 0,
            "registry_path": str(registry_path),
            "inventory_files": inventory_count,
        },
        "patterns_by_status": {},
        "recent_patterns": []
    }

    # Count by status
    for pattern in patterns:
        status = pattern.get('status', 'unknown')
        report['patterns_by_status'][status] = report['patterns_by_status'].get(status, 0) + 1

    # Get 10 most recent
    sorted_patterns = sorted(patterns, key=lambda p: p.get('first_seen', ''), reverse=True)
    report['recent_patterns'] = sorted_patterns[:10]

    # Save report
    reports_dir = base / 'reports'
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"pattern_id_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Display summary
    print("\n" + "="*60)
    print("PATTERN_ID STATUS REPORT")
    print("="*60)
    print(f"\nTotal Patterns: {len(patterns)}")
    print(f"Complete Triads: {complete_triads}/{len(patterns)} ({report['pattern_id_status']['triad_percentage']}%)")
    print(f"Inventory Files: {inventory_count}")
    print(f"\nBy Status:")
    for status, count in report['patterns_by_status'].items():
        print(f"  {status}: {count}")
    print(f"\nReport saved: {report_path}")
    print("="*60 + "\n")

    return 0

if __name__ == "__main__":
    sys.exit(generate_report())
