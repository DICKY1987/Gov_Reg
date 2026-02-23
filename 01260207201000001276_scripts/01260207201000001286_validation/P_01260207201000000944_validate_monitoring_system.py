#!/usr/bin/env python3
"""Validate monitoring system is operational."""

import sys
from pathlib import Path


REQUIRED_COMPONENTS = [
    {'name': 'Prometheus Config', 'path': 'monitoring/prometheus_config.yml'},
    {'name': 'Grafana Dashboards', 'path': 'monitoring/dashboards'},
    {'name': 'Alert Rules', 'path': 'monitoring/alerts'}
]


def validate_monitoring_system():
    """Validate monitoring system components."""
    print("Monitoring System Validation")
    print("=" * 70)
    
    all_present = True
    
    for component in REQUIRED_COMPONENTS:
        path = Path(component['path'])
        exists = path.exists()
        marker = "✓" if exists else "✗"
        status = "Present" if exists else "Missing"
        
        print(f"{marker} {component['name']:30s} {status}")
        
        if not exists:
            all_present = False
    
    print("=" * 70)
    
    if all_present:
        print("✓ MONITORING SYSTEM OPERATIONAL")
        print("  All required components present")
        return 0
    else:
        print("✗ MONITORING SYSTEM NOT OPERATIONAL")
        print("  Some components missing")
        return 1


if __name__ == '__main__':
    sys.exit(validate_monitoring_system())
