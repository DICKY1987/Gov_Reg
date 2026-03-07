#!/usr/bin/env python3
# DOC_LINK: DOC-TRIGGER-REPORTING-REPORT-001
"""
Trigger ID Reporting
Generates trigger_id status and coverage reports
"""
# DOC_ID: DOC-TRIGGER-REPORTING-REPORT-001

import json
import sys
import yaml
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def generate_report():
    """Generate trigger_id status report."""
    base = Path(__file__).parent.parent
    registry_path = base / '5_REGISTRY_DATA' / 'TRIGGER_ID_REGISTRY.yaml'
    inventory_path = base / '5_REGISTRY_DATA' / 'trigger_id_inventory.jsonl'

    # Load data
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    triggers = registry.get('triggers', [])

    inventory_count = 0
    if inventory_path.exists():
        with open(inventory_path, 'r', encoding='utf-8') as f:
            inventory_count = sum(1 for line in f if line.strip())

    # Generate report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "trigger_id_status": {
            "total_triggers": len(triggers),
            "registry_path": str(registry_path),
            "inventory_files": inventory_count,
        },
        "triggers_by_status": {},
        "recent_triggers": []
    }

    # Count by status
    for trigger in triggers:
        status = trigger.get('status', 'unknown')
        report['triggers_by_status'][status] = report['triggers_by_status'].get(status, 0) + 1

    # Get 10 most recent
    sorted_triggers = sorted(triggers, key=lambda t: t.get('first_seen', ''), reverse=True)
    report['recent_triggers'] = sorted_triggers[:10]

    # Save report
    reports_dir = base / 'reports'
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"trigger_id_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Display summary
    print("\n" + "="*60)
    print("TRIGGER_ID STATUS REPORT")
    print("="*60)
    print(f"\nTotal Triggers: {len(triggers)}")
    print(f"Inventory Files: {inventory_count}")
    print(f"\nBy Status:")
    for status, count in report['triggers_by_status'].items():
        print(f"  {status}: {count}")
    print(f"\nReport saved: {report_path}")
    print("="*60 + "\n")

    return 0

if __name__ == "__main__":
    sys.exit(generate_report())
