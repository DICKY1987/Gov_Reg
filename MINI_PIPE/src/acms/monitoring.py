"""ACMS Monitoring and Metrics System

Tracks pipeline performance, health metrics, and historical trends.
Provides dashboards and alerting for anomaly detection.
"""

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict


@dataclass
class PipelineMetrics:
    """Metrics for a single pipeline run"""

    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    phase_durations: Dict[str, float] = None
    gaps_discovered: int = 0
    gaps_fixed: int = 0
    tasks_executed: int = 0
    tasks_failed: int = 0
    success: bool = True
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.phase_durations is None:
            self.phase_durations = {}

    def complete(self, success: bool = True, error: Optional[str] = None):
        """Mark pipeline run as completed"""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.error_message = error


@dataclass
class HealthStatus:
    """Overall system health status"""

    status: str  # 'healthy', 'degraded', 'unhealthy'
    last_successful_run: Optional[datetime]
    consecutive_failures: int
    avg_duration_seconds: float
    gaps_pending: int
    alerts: List[str]


class MetricsCollector:
    """Collects and persists pipeline metrics"""

    def __init__(self, metrics_dir: Path):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.metrics_dir / "pipeline_metrics.jsonl"

    def record_run(self, metrics: PipelineMetrics):
        """Record metrics for a pipeline run"""
        with open(self.metrics_file, "a") as f:
            data = asdict(metrics)
            data["start_time"] = metrics.start_time.isoformat()
            data["end_time"] = (
                metrics.end_time.isoformat() if metrics.end_time else None
            )
            f.write(json.dumps(data) + "\n")

    def get_recent_runs(self, limit: int = 10) -> List[PipelineMetrics]:
        """Get most recent pipeline runs"""
        if not self.metrics_file.exists():
            return []

        runs = []
        with open(self.metrics_file, "r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    data["start_time"] = datetime.fromisoformat(data["start_time"])
                    if data["end_time"]:
                        data["end_time"] = datetime.fromisoformat(data["end_time"])
                    runs.append(PipelineMetrics(**data))

        return sorted(runs, key=lambda x: x.start_time, reverse=True)[:limit]

    def get_metrics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get aggregated metrics for specified time period"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_runs = [
            r for r in self.get_recent_runs(limit=1000) if r.start_time > cutoff
        ]

        if not recent_runs:
            return {
                "total_runs": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "total_gaps_discovered": 0,
                "total_gaps_fixed": 0,
            }

        successful = [r for r in recent_runs if r.success]

        return {
            "total_runs": len(recent_runs),
            "successful_runs": len(successful),
            "success_rate": len(successful) / len(recent_runs) * 100,
            "avg_duration": sum(r.duration_seconds for r in recent_runs)
            / len(recent_runs),
            "total_gaps_discovered": sum(r.gaps_discovered for r in recent_runs),
            "total_gaps_fixed": sum(r.gaps_fixed for r in recent_runs),
            "avg_gaps_per_run": sum(r.gaps_discovered for r in recent_runs)
            / len(recent_runs),
        }


class HealthMonitor:
    """Monitors system health and generates alerts"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.collector = metrics_collector
        self.thresholds = {
            "max_consecutive_failures": 3,
            "max_duration_seconds": 600,  # 10 minutes
            "min_success_rate": 80.0,
            "max_gaps_pending": 100,
        }

    def check_health(self) -> HealthStatus:
        """Check overall system health"""
        recent_runs = self.collector.get_recent_runs(limit=20)
        summary = self.collector.get_metrics_summary(days=7)
        alerts = []

        # Check for consecutive failures
        consecutive_failures = 0
        for run in recent_runs:
            if not run.success:
                consecutive_failures += 1
            else:
                break

        if consecutive_failures >= self.thresholds["max_consecutive_failures"]:
            alerts.append(f"🚨 {consecutive_failures} consecutive pipeline failures")

        # Check success rate
        if summary["success_rate"] < self.thresholds["min_success_rate"]:
            alerts.append(
                f"⚠️  Success rate below threshold: {summary['success_rate']:.1f}%"
            )

        # Check duration
        if summary["avg_duration"] > self.thresholds["max_duration_seconds"]:
            alerts.append(
                f"⚠️  Average duration exceeds threshold: {summary['avg_duration']:.1f}s"
            )

        # Determine overall status
        status = "healthy"
        if alerts:
            status = "degraded"
        if consecutive_failures >= self.thresholds["max_consecutive_failures"]:
            status = "unhealthy"

        # Find last successful run
        last_success = None
        for run in recent_runs:
            if run.success:
                last_success = run.end_time or run.start_time
                break

        return HealthStatus(
            status=status,
            last_successful_run=last_success,
            consecutive_failures=consecutive_failures,
            avg_duration_seconds=summary.get("avg_duration", 0.0),
            gaps_pending=summary.get("total_gaps_discovered", 0)
            - summary.get("total_gaps_fixed", 0),
            alerts=alerts,
        )

    def generate_health_report(self) -> str:
        """Generate human-readable health report"""
        health = self.check_health()
        summary = self.collector.get_metrics_summary(days=7)

        icons = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}

        report = f"""
# ACMS Pipeline Health Report
Generated: {datetime.now().isoformat()}

## Overall Status: {icons[health.status]} {health.status.upper()}

## Recent Performance (7 days)
- Total Runs: {summary['total_runs']}
- Success Rate: {summary['success_rate']:.1f}%
- Average Duration: {summary['avg_duration']:.1f}s
- Gaps Discovered: {summary['total_gaps_discovered']}
- Gaps Fixed: {summary['total_gaps_fixed']}

## Health Indicators
- Last Successful Run: {health.last_successful_run or 'Never'}
- Consecutive Failures: {health.consecutive_failures}
- Gaps Pending: {health.gaps_pending}

"""

        if health.alerts:
            report += "## Active Alerts\n"
            for alert in health.alerts:
                report += f"- {alert}\n"
        else:
            report += "## Active Alerts\nNone - All systems operational ✓\n"

        return report


class PerformanceTracker:
    """Tracks performance metrics and trends"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.collector = metrics_collector

    def analyze_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        cutoff = datetime.now() - timedelta(days=days)
        runs = [
            r
            for r in self.collector.get_recent_runs(limit=1000)
            if r.start_time > cutoff
        ]

        if not runs:
            return {}

        # Group by week
        weekly_stats = defaultdict(lambda: {"runs": 0, "duration": 0, "gaps": 0})

        for run in runs:
            week = run.start_time.strftime("%Y-W%U")
            weekly_stats[week]["runs"] += 1
            weekly_stats[week]["duration"] += run.duration_seconds
            weekly_stats[week]["gaps"] += run.gaps_discovered

        # Calculate trends
        weeks = sorted(weekly_stats.keys())
        if len(weeks) < 2:
            return {"trend": "insufficient_data"}

        first_week = weekly_stats[weeks[0]]
        last_week = weekly_stats[weeks[-1]]

        return {
            "weeks_analyzed": len(weeks),
            "runs_trend": (
                (last_week["runs"] - first_week["runs"]) / first_week["runs"] * 100
            )
            if first_week["runs"] > 0
            else 0,
            "duration_trend": (
                (last_week["duration"] - first_week["duration"])
                / first_week["duration"]
                * 100
            )
            if first_week["duration"] > 0
            else 0,
            "gaps_trend": (
                (last_week["gaps"] - first_week["gaps"]) / first_week["gaps"] * 100
            )
            if first_week["gaps"] > 0
            else 0,
            "weekly_stats": dict(weekly_stats),
        }

    def get_phase_breakdown(self) -> Dict[str, float]:
        """Get average duration by phase"""
        recent_runs = self.collector.get_recent_runs(limit=50)

        phase_totals = defaultdict(float)
        phase_counts = defaultdict(int)

        for run in recent_runs:
            for phase, duration in run.phase_durations.items():
                phase_totals[phase] += duration
                phase_counts[phase] += 1

        return {
            phase: phase_totals[phase] / phase_counts[phase] for phase in phase_totals
        }


def create_monitoring_system(base_dir: Path) -> tuple:
    """Create complete monitoring system"""
    metrics_dir = base_dir / "logs" / "metrics"
    collector = MetricsCollector(metrics_dir)
    health_monitor = HealthMonitor(collector)
    performance_tracker = PerformanceTracker(collector)

    return collector, health_monitor, performance_tracker
