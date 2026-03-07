# DOC_LINK: DOC-CORE-3-AUTOMATION-HOOKS-V3-AUTOMATION-RUNNER-520
# TRIGGER_ID: TRIGGER-RUNNER-V3-AUTOMATION-RUNNER-001
"""
V3 Automation Runner
DOC_LINK: A-REGV3-AUTORUNNER-011
Work ID: WORK-REGV3-002

Unified entry point for all V3 automation tasks.
Supports: scan, validate, health-check, dashboard
"""

import argparse
import sys
import uuid
from pathlib import Path
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class V3AutomationRunner:
    """Unified automation runner for V3 operations"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.db_path = repo_root / "SUB_DOC_ID" / "migration_v3" / "data" / "registry_v3.db"
        self.tools_dir = repo_root / "SUB_DOC_ID" / "migration_v3" / "tools"

    def scan(self, scope='all', batch_size=100):
        """Run V3 scan"""
        run_id = str(uuid.uuid4())
        trace_id = f"AUTOSCAN-{run_id[:8]}"

        logger.info(f"Starting V3 scan (scope={scope}, trace_id={trace_id})")

        cmd = [
            sys.executable,
            str(self.tools_dir / "backfill_tier2_tier3.py"),
            "--db", str(self.db_path),
            "--repo-root", str(self.repo_root),
            "--batch-size", str(batch_size),
            "--run-id", run_id,
            "--trace-id", trace_id
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        logger.info(f"Scan completed with exit code: {result.returncode}")

        return result.returncode == 0

    def validate(self):
        """Run V3 validation (pre-commit checks)"""
        logger.info("Running V3 validation...")

        cmd = [
            sys.executable,
            str(self.repo_root / "SUB_DOC_ID" / "3_AUTOMATION_HOOKS" / "v3_pre_commit.py")
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)

        return result.returncode == 0

    def health_check(self, fail_on_warning=False):
        """Run V3 health check"""
        logger.info("Running V3 health check...")

        cmd = [
            sys.executable,
            str(self.tools_dir / "v3_health_check.py"),
            "--db", str(self.db_path)
        ]

        if fail_on_warning:
            cmd.append("--fail-on-warning")

        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)

        return result.returncode == 0

    def dashboard(self, output_path=None):
        """Generate V3 dashboard"""
        run_id = str(uuid.uuid4())

        if not output_path:
            output_path = self.repo_root / "SUB_DOC_ID" / "4_REPORTING_MONITORING" / "v3_dashboard.html"

        logger.info(f"Generating dashboard: {output_path}")

        cmd = [
            sys.executable,
            str(self.tools_dir / "v3_dashboard.py"),
            "--db", str(self.db_path),
            "--output", str(output_path),
            "--run-id", run_id
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"Dashboard generated successfully: {output_path}")

        return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="V3 Automation Runner")
    parser.add_argument("action", choices=['scan', 'validate', 'health-check', 'dashboard'],
                        help="Action to perform")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for scan")
    parser.add_argument("--fail-on-warning", action="store_true", help="Fail on warnings (health-check)")
    parser.add_argument("--output", help="Output path (dashboard)")

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.parent
    runner = V3AutomationRunner(repo_root)

    if args.action == 'scan':
        success = runner.scan(batch_size=args.batch_size)
    elif args.action == 'validate':
        success = runner.validate()
    elif args.action == 'health-check':
        success = runner.health_check(args.fail_on_warning)
    elif args.action == 'dashboard':
        success = runner.dashboard(args.output)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
