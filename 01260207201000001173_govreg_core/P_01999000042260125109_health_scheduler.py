"""Health check scheduler for ID system (GAP-006).

FILE_ID: 01999000042260125109
PURPOSE: Scheduled health checks and reconciliation runs
PHASE: Phase 6 - Continuous Health
BACKLOG: 01999000042260125103 GAP-006

Implements cron-like scheduling for:
- Nightly reconciliation runs
- Coverage analysis
- Orphan detection
- Health reports
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass, asdict
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Check if APScheduler is available
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    BackgroundScheduler = None
    CronTrigger = None


@dataclass
class HealthCheckResult:
    """Result of a scheduled health check."""
    check_type: str
    timestamp: str
    success: bool
    details: Dict
    duration_seconds: float
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class HealthCheckScheduler:
    """Schedules periodic health checks for ID system.
    
    Provides cron-like scheduling for:
    - Reconciliation runs
    - Coverage analysis
    - Orphan cleanup
    - Health reports
    """
    
    def __init__(
        self,
        project_root: Path,
        config: Optional[Dict] = None,
        evidence_dir: Optional[Path] = None
    ):
        """Initialize health check scheduler.
        
        Args:
            project_root: Project root directory
            config: Configuration dict with schedule settings
            evidence_dir: Directory for evidence artifacts
        """
        if not APSCHEDULER_AVAILABLE:
            raise ImportError(
                "APScheduler required for scheduling. "
                "Install with: pip install apscheduler"
            )
        
        self.project_root = project_root
        self.config = config or {}
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "health_checks"
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        self.scheduler = BackgroundScheduler()
        self.health_checks: List[HealthCheckResult] = []
    
    def schedule_reconciliation(
        self,
        schedule: str = "0 2 * * *",  # 2 AM daily
        callback: Optional[Callable] = None
    ):
        """Schedule periodic reconciliation runs.
        
        Args:
            schedule: Cron expression (default: 2 AM daily)
            callback: Optional callback after each run
        """
        def run_reconciliation():
            start_time = datetime.now(timezone.utc)
            
            try:
                # Import here to avoid circular dependency
                from P_01999000042260125106_registry_filesystem_reconciler import reconcile_registry_filesystem
                
                registry_path = self.project_root / "01260207201000001250_REGISTRY" / "01999000042260124503_REGISTRY_file.json"
                result = reconcile_registry_filesystem(
                    self.project_root,
                    registry_path,
                    zone="all",
                    auto_fix=False
                )
                
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                health_result = HealthCheckResult(
                    check_type="reconciliation",
                    timestamp=start_time.isoformat(),
                    success=True,
                    details={
                        "total_issues": len(result.issues),
                        "registry_entries": result.total_registry_entries,
                        "filesystem_files": result.total_filesystem_files
                    },
                    duration_seconds=duration
                )
                
                self.health_checks.append(health_result)
                self._save_health_check(health_result)
                
                if callback:
                    callback(health_result)
                    
            except Exception as e:
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                health_result = HealthCheckResult(
                    check_type="reconciliation",
                    timestamp=start_time.isoformat(),
                    success=False,
                    details={"error": str(e)},
                    duration_seconds=duration
                )
                
                self.health_checks.append(health_result)
                self._save_health_check(health_result)
        
        trigger = CronTrigger.from_crontab(schedule)
        self.scheduler.add_job(run_reconciliation, trigger, id="reconciliation")
    
    def schedule_coverage_analysis(
        self,
        schedule: str = "0 3 * * *",  # 3 AM daily
        callback: Optional[Callable] = None
    ):
        """Schedule periodic coverage analysis.
        
        Args:
            schedule: Cron expression (default: 3 AM daily)
            callback: Optional callback after each run
        """
        def run_coverage_analysis():
            start_time = datetime.now(timezone.utc)
            
            try:
                from P_01999000042260125108_coverage_completer import complete_dir_id_coverage
                
                registry_path = self.project_root / "01260207201000001250_REGISTRY" / "01999000042260124503_REGISTRY_file.json"
                root_id = "01260207201000000000"  # Would read from config
                
                analysis = complete_dir_id_coverage(
                    self.project_root,
                    registry_path,
                    root_id,
                    auto_apply=False
                )
                
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                health_result = HealthCheckResult(
                    check_type="coverage_analysis",
                    timestamp=start_time.isoformat(),
                    success=True,
                    details={
                        "coverage_percentage": analysis.coverage_percentage,
                        "entries_without_dir_id": analysis.entries_without_dir_id,
                        "gaps_found": len(analysis.gaps)
                    },
                    duration_seconds=duration
                )
                
                self.health_checks.append(health_result)
                self._save_health_check(health_result)
                
                if callback:
                    callback(health_result)
                    
            except Exception as e:
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                health_result = HealthCheckResult(
                    check_type="coverage_analysis",
                    timestamp=start_time.isoformat(),
                    success=False,
                    details={"error": str(e)},
                    duration_seconds=duration
                )
                
                self.health_checks.append(health_result)
                self._save_health_check(health_result)
        
        trigger = CronTrigger.from_crontab(schedule)
        self.scheduler.add_job(run_coverage_analysis, trigger, id="coverage_analysis")
    
    def schedule_custom_check(
        self,
        check_name: str,
        check_function: Callable,
        schedule: str
    ):
        """Schedule a custom health check.
        
        Args:
            check_name: Name for the health check
            check_function: Function to run (should return dict)
            schedule: Cron expression
        """
        def run_custom_check():
            start_time = datetime.now(timezone.utc)
            
            try:
                result = check_function()
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                health_result = HealthCheckResult(
                    check_type=check_name,
                    timestamp=start_time.isoformat(),
                    success=True,
                    details=result,
                    duration_seconds=duration
                )
                
                self.health_checks.append(health_result)
                self._save_health_check(health_result)
                
            except Exception as e:
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                health_result = HealthCheckResult(
                    check_type=check_name,
                    timestamp=start_time.isoformat(),
                    success=False,
                    details={"error": str(e)},
                    duration_seconds=duration
                )
                
                self.health_checks.append(health_result)
                self._save_health_check(health_result)
        
        trigger = CronTrigger.from_crontab(schedule)
        self.scheduler.add_job(run_custom_check, trigger, id=check_name)
    
    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
    
    def get_recent_checks(self, count: int = 10) -> List[HealthCheckResult]:
        """Get recent health check results.
        
        Args:
            count: Number of recent checks to return
            
        Returns:
            List of recent health check results
        """
        return self.health_checks[-count:]
    
    def _save_health_check(self, result: HealthCheckResult):
        """Save health check result to evidence."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        evidence_file = self.evidence_dir / f"{result.check_type}_{timestamp}.json"
        
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2)


def start_health_scheduler(
    project_root: Path,
    config_path: Optional[Path] = None,
    daemon: bool = False
) -> HealthCheckScheduler:
    """Start health check scheduler (public API).
    
    Args:
        project_root: Project root directory
        config_path: Optional path to config file
        daemon: If True, run as daemon (blocks)
        
    Returns:
        HealthCheckScheduler: Running scheduler instance
    """
    config = {}
    if config_path and config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    scheduler = HealthCheckScheduler(project_root, config)
    
    # Schedule default checks
    scheduler.schedule_reconciliation(
        schedule=config.get('reconciliation_schedule', '0 2 * * *')
    )
    scheduler.schedule_coverage_analysis(
        schedule=config.get('coverage_schedule', '0 3 * * *')
    )
    
    scheduler.start()
    
    if daemon:
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            scheduler.stop()
    
    return scheduler


if __name__ == "__main__":
    # CLI entry point
    import argparse
    
    parser = argparse.ArgumentParser(description="Start health check scheduler")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--config", type=Path, help="Path to config file")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    print(f"Starting health check scheduler for {args.project_root}")
    scheduler = start_health_scheduler(args.project_root, args.config, args.daemon)
    
    if not args.daemon:
        print("Scheduler started. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            scheduler.stop()
            print("Scheduler stopped")
