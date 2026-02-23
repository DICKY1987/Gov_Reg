#!/usr/bin/env python3
"""Generate Prometheus monitoring configuration."""

import sys
from pathlib import Path


PROMETHEUS_CONFIG = """# Prometheus Configuration for Gov_Reg System
# Generated: 2026-02-08

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'gov-reg-production'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Load rules once and periodically evaluate them
rule_files:
  - "alerts/*.yml"

# Scrape configurations
scrape_configs:
  # Gov_Reg application metrics
  - job_name: 'govreg-app'
    static_configs:
      - targets:
          - localhost:8000
    metrics_path: '/metrics'
    scrape_interval: 10s

  # System metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets:
          - localhost:9100

  # Python application metrics
  - job_name: 'python-metrics'
    static_configs:
      - targets:
          - localhost:8001

# Remote write configuration (optional)
# remote_write:
#   - url: "http://remote-storage:9090/api/v1/write"

# Storage configuration
storage:
  tsdb:
    path: /var/lib/prometheus/data
    retention:
      time: 30d
      size: 50GB
"""


def generate_prometheus_config(output_path):
    """Generate Prometheus configuration file."""
    print(f"Generating Prometheus Configuration")
    print("=" * 70)
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w', encoding='utf-8') as f:
        f.write(PROMETHEUS_CONFIG)
    
    print(f"✓ Configuration generated: {output_path}")
    print(f"\nConfiguration includes:")
    print(f"  - Global settings (15s scrape interval)")
    print(f"  - Alertmanager integration")
    print(f"  - 3 scrape jobs (app, node, python)")
    print(f"  - 30-day retention")
    
    print("=" * 70)
    print(f"✓ PROMETHEUS CONFIG GENERATED")
    
    return 0


if __name__ == '__main__':
    output = None
    
    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output = sys.argv[i + 1]
    
    if not output:
        print("Usage: python generate_prometheus_config.py --output <config.yml>")
        sys.exit(1)
    
    sys.exit(generate_prometheus_config(output))
