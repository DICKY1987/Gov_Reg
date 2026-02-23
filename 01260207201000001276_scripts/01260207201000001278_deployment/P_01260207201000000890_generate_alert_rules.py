#!/usr/bin/env python3
"""Generate alert rules for monitoring system."""

import sys
from pathlib import Path


CRITICAL_ALERTS = """# Critical Alert Rules
# Generated: 2026-02-08

groups:
  - name: critical_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_errors_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # Service down
      - alert: ServiceDown
        expr: up{job="govreg-app"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "Gov_Reg application is not responding"

      # High response time
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 0.5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High response time"
          description: "P95 response time is {{ $value }}s (threshold: 500ms)"

      # Registry lock timeout
      - alert: RegistryLockTimeout
        expr: rate(registry_lock_timeouts_total[5m]) > 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Registry lock timeouts occurring"
          description: "{{ $value }} lock timeouts per second"

      # Disk space low
      - alert: DiskSpaceLow
        expr: 100 * (1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) > 80
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space low"
          description: "Disk usage is {{ $value | humanizePercentage }}"

      # Memory pressure
      - alert: MemoryPressure
        expr: 100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Memory pressure high"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # CPU overload
      - alert: CPUOverload
        expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "CPU overload"
          description: "CPU usage is {{ $value | humanizePercentage }}"
"""


def generate_alert_rules(severity, output_path):
    """Generate alert rules for specified severity."""
    print(f"Generating Alert Rules")
    print("=" * 70)
    print(f"Severity: {severity}")
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    if severity == 'critical':
        content = CRITICAL_ALERTS
        rule_count = 7
    else:
        content = f"# {severity.title()} Alert Rules\n# No rules defined\n"
        rule_count = 0
    
    with open(output, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Alert rules generated: {output_path}")
    print(f"  Rules defined: {rule_count}")
    
    if severity == 'critical':
        print(f"\nCritical Alerts:")
        print(f"  - HighErrorRate (>5% error rate)")
        print(f"  - ServiceDown (service unavailable)")
        print(f"  - HighResponseTime (>500ms p95)")
        print(f"  - RegistryLockTimeout (lock timeouts)")
        print(f"  - DiskSpaceLow (>80% usage)")
        print(f"  - MemoryPressure (>90% usage)")
        print(f"  - CPUOverload (>90% usage)")
    
    print("=" * 70)
    print(f"✓ ALERT RULES GENERATED")
    
    return 0


if __name__ == '__main__':
    severity = 'critical'
    output = None
    
    for i, arg in enumerate(sys.argv):
        if arg == '--severity' and i + 1 < len(sys.argv):
            severity = sys.argv[i + 1]
        elif arg == '--output' and i + 1 < len(sys.argv):
            output = sys.argv[i + 1]
    
    if not output:
        print("Usage: python generate_alert_rules.py --severity <level> --output <file.yml>")
        sys.exit(1)
    
    sys.exit(generate_alert_rules(severity, output))
