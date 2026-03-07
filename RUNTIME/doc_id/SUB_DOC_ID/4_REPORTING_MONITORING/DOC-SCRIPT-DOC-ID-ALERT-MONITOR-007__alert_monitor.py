#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_LINK: DOC-SCRIPT-DOC-ID-ALERT-MONITOR-007
"""
DOC_ID System Alert Monitor

PATTERN: EXEC-002 Batch Validation
Ground Truth: Alerts generated and logged

USAGE:
    python doc_id/alert_monitor.py
    python doc_id/alert_monitor.py --thresholds alert_thresholds.yaml
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, MODULE_ROOT

ALERTS_DIR = REPO_ROOT / ".state"
THRESHOLDS_FILE = MODULE_ROOT / "4_REPORTING_MONITORING" / "alert_thresholds.yaml"


@dataclass
class Threshold:
    """Alert threshold definition"""
    name: str
    metric: str
    operator: str  # <, >, ==
    value: float
    severity: str  # critical, warning, info


@dataclass
class Alert:
    """Alert instance"""
    threshold_name: str
    metric: str
    actual_value: float
    threshold_value: float
    operator: str
    message: str
    severity: str


# Default thresholds
DEFAULT_THRESHOLDS = [
    Threshold("coverage_critical", "coverage", "<", 90.0, "critical"),
    Threshold("coverage_warning", "coverage", "<", 95.0, "warning"),
    Threshold("invalid_ids_critical", "invalid_count", ">", 10, "critical"),
    Threshold("drift_warning", "drift_count", ">", 50, "warning"),
    Threshold("duplicates_critical", "duplicate_count", ">", 5, "critical"),
]


def load_thresholds(thresholds_file: Path = None) -> List[Threshold]:
    """Load threshold configuration"""
    if thresholds_file and thresholds_file.exists():
        try:
            import yaml
            with open(thresholds_file) as f:
                data = yaml.safe_load(f)
                return [Threshold(**t) for t in data['thresholds']]
        except Exception as e:
            print(f"Warning: Failed to load thresholds: {e}", file=sys.stderr)
    return DEFAULT_THRESHOLDS


def extract_metrics_from_report(report: Dict) -> Dict[str, float]:
    """Extract metrics from daily report"""
    metrics = {}

    # Coverage from scanner output
    scanner_output = report.get('scanner', {}).get('output', '')
    coverage_match = re.search(r'Coverage: (\d+\.?\d*)%', scanner_output)
    if coverage_match:
        metrics['coverage'] = float(coverage_match.group(1))

    # Invalid IDs from cleanup output
    cleanup_output = report.get('cleanup', {}).get('output', '')
    invalid_match = re.search(r'Malformed: (\d+)', cleanup_output)
    if invalid_match:
        metrics['invalid_count'] = float(invalid_match.group(1))

    # Drift from sync output
    sync_output = report.get('sync', {}).get('output', '')
    drift_match = re.search(r'Total drift: (\d+)', sync_output)
    if drift_match:
        metrics['drift_count'] = float(drift_match.group(1))

    return metrics


def extract_metrics_from_scan(scanner_stats: str) -> Dict[str, float]:
    """Extract metrics from scanner stats output"""
    metrics = {}

    coverage_match = re.search(r'Coverage: (\d+\.?\d*)%', scanner_stats)
    if coverage_match:
        metrics['coverage'] = float(coverage_match.group(1))

    return metrics


def check_thresholds(metrics: Dict[str, float],
                     thresholds: List[Threshold]) -> List[Alert]:
    """Check metrics against thresholds"""
    alerts = []

    for threshold in thresholds:
        if threshold.metric not in metrics:
            continue

        actual = metrics[threshold.metric]
        triggered = False

        if threshold.operator == '<' and actual < threshold.value:
            triggered = True
        elif threshold.operator == '>' and actual > threshold.value:
            triggered = True
        elif threshold.operator == '==' and actual == threshold.value:
            triggered = True

        if triggered:
            message = f"{threshold.name}: {threshold.metric} is {actual} (threshold: {threshold.operator}{threshold.value})"
            alerts.append(Alert(
                threshold_name=threshold.name,
                metric=threshold.metric,
                actual_value=actual,
                threshold_value=threshold.value,
                operator=threshold.operator,
                message=message,
                severity=threshold.severity
            ))

    return alerts


def save_alerts(alerts: List[Alert]):
    """Save alerts to state file"""
    ALERTS_DIR.mkdir(exist_ok=True)

    alert_file = ALERTS_DIR / "doc_id_alerts.log"

    with open(alert_file, 'w') as f:
        for alert in alerts:
            f.write(f"[{alert.severity.upper()}] {alert.message}\n")

    # Also save as JSON for programmatic access
    json_file = ALERTS_DIR / "doc_id_alerts.json"
    with open(json_file, 'w') as f:
        json.dump([asdict(a) for a in alerts], f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="DOC_ID Alert Monitor")
    parser.add_argument('--thresholds', type=Path,
                       help='Path to thresholds configuration file')
    parser.add_argument('--report', type=Path,
                       help='Path to daily report file')
    args = parser.parse_args()

    # Load thresholds
    thresholds_file = args.thresholds or THRESHOLDS_FILE
    thresholds = load_thresholds(thresholds_file)

    # Extract metrics
    metrics = {}

    if args.report and args.report.exists():
        # Load from specified report
        with open(args.report) as f:
            report = json.load(f)
        metrics = extract_metrics_from_report(report)
    else:
        # Try to load latest daily report
        reports_dir = REPO_ROOT / "doc_id" / "DOC_ID_reports"
        if reports_dir.exists():
            daily_reports = sorted(reports_dir.glob("daily_report_*.json"))
            if daily_reports:
                with open(daily_reports[-1]) as f:
                    report = json.load(f)
                metrics = extract_metrics_from_report(report)

    # If no metrics from report, try scanner stats
    if not metrics:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'doc_id/doc_id_scanner.py', 'stats'],
            capture_output=True, text=True, cwd=REPO_ROOT
        )
        if result.returncode == 0:
            metrics = extract_metrics_from_scan(result.stdout)

    if not metrics:
        print("⚠️  No metrics available for threshold checking")
        sys.exit(0)

    # Check thresholds
    alerts = check_thresholds(metrics, thresholds)

    # Save and report
    if alerts:
        save_alerts(alerts)

        print(f"🚨 {len(alerts)} alert(s) triggered:")
        for alert in alerts:
            symbol = "🔴" if alert.severity == "critical" else "⚠️"
            print(f"{symbol} [{alert.severity.upper()}] {alert.message}")

        # Exit non-zero for CI
        sys.exit(1)
    else:
        print("✅ All thresholds passed")
        # Clear old alerts
        alert_file = ALERTS_DIR / "doc_id_alerts.log"
        json_file = ALERTS_DIR / "doc_id_alerts.json"
        if alert_file.exists():
            alert_file.unlink()
        if json_file.exists():
            json_file.unlink()
        sys.exit(0)


if __name__ == '__main__':
    main()
