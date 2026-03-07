#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-AUTOMATION-HEALTH-001
# -*- coding: utf-8 -*-
# DOC_ID: DOC-VALIDATOR-AUTOMATION-HEALTH-001
"""
DOC-ID Automation Health Validator

PURPOSE: Validate that all DOC-ID automation infrastructure is operational
PATTERN: PATTERN-DOC-ID-HEALTH-CHECK-001

USAGE:
    python validate_automation_health.py --check all
    python validate_automation_health.py --check tasks
    python validate_automation_health.py --check hook
    python validate_automation_health.py --check scan
    python validate_automation_health.py --check registry
    python validate_automation_health.py --mode diagnose
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import REPO_ROOT, REGISTRY_PATH, INVENTORY_PATH


class AutomationHealthValidator:
    """Validate DOC-ID automation health"""

    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []

    def check_scheduled_tasks(self) -> bool:
        """Check if scheduled tasks exist and have correct paths"""
        print("\n🔍 Checking scheduled tasks...")

        try:
            # Get scheduled tasks (Windows)
            result = subprocess.run(
                ["powershell", "-Command", "Get-ScheduledTask -TaskName 'DOC_ID_V3_*' | Select-Object TaskName,State,@{Name='Execute';Expression={$_.Actions[0].Execute}} | ConvertTo-Json"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                self.issues.append("Unable to query scheduled tasks")
                return False

            if not result.stdout.strip():
                self.issues.append("No DOC_ID_V3_* scheduled tasks found")
                return False

            tasks_data = json.loads(result.stdout)
            if not isinstance(tasks_data, list):
                tasks_data = [tasks_data]

            # Check each task
            expected_tasks = ["DOC_ID_V3_Nightly_Scan", "DOC_ID_V3_Health_Check", "DOC_ID_V3_Dashboard"]
            found_tasks = [task['TaskName'] for task in tasks_data]

            missing = set(expected_tasks) - set(found_tasks)
            if missing:
                self.issues.append(f"Missing scheduled tasks: {', '.join(missing)}")

            # Check paths
            for task in tasks_data:
                task_name = task['TaskName']
                execute_path = task.get('Execute', '')

                if not execute_path:
                    self.warnings.append(f"{task_name}: No execution path found")
                    continue

                # Check if path exists
                if not Path(execute_path).exists():
                    self.issues.append(f"{task_name}: Path does not exist: {execute_path}")
                # Check for obsolete migration_v3 path
                elif 'migration_v3' in execute_path:
                    self.issues.append(f"{task_name}: Still points to obsolete migration_v3 path")
                else:
                    self.passed.append(f"{task_name}: Path valid")

                    # Check last run status
                    info_result = subprocess.run(
                        ["powershell", "-Command", f"(Get-ScheduledTaskInfo -TaskName '{task_name}').LastTaskResult"],
                        capture_output=True,
                        text=True,
                        check=False
                    )

                    if info_result.returncode == 0:
                        last_result = info_result.stdout.strip()
                        if last_result == "0":
                            self.passed.append(f"{task_name}: Last run successful (exit code 0)")
                        else:
                            self.warnings.append(f"{task_name}: Last run failed (exit code {last_result})")

            return len([i for i in self.issues if "scheduled tasks" in i.lower()]) == 0

        except Exception as e:
            self.issues.append(f"Error checking scheduled tasks: {e}")
            return False

    def check_pre_commit_hook(self) -> bool:
        """Check if pre-commit hook exists and enforces DOC-IDs"""
        print("\n🔍 Checking pre-commit hook...")

        hook_path = REPO_ROOT / ".git" / "hooks" / "pre-commit"

        if not hook_path.exists():
            self.issues.append("Pre-commit hook not installed")
            return False

        try:
            content = hook_path.read_text(encoding="utf-8", errors="ignore")

            # Check for DOC-ID enforcement logic
            if "Missing DOC-ID" in content or "DOC_ID" in content:
                self.passed.append("Pre-commit hook contains DOC-ID enforcement logic")
                return True
            else:
                self.issues.append("Pre-commit hook exists but lacks DOC-ID enforcement")
                return False

        except Exception as e:
            self.issues.append(f"Error reading pre-commit hook: {e}")
            return False

    def check_scanner_health(self) -> bool:
        """Check if scanner is operational"""
        print("\n🔍 Checking scanner health...")

        scanner_path = REPO_ROOT / "RUNTIME" / "doc_id" / "SUB_DOC_ID" / "1_CORE_OPERATIONS" / "doc_id_scanner.py"

        if not scanner_path.exists():
            self.issues.append(f"Scanner not found: {scanner_path}")
            return False

        self.passed.append("Scanner script exists")

        # Check if inventory file exists and is recent
        if not INVENTORY_PATH.exists():
            self.warnings.append("Inventory file not found - scanner may not have run")
            return True  # Warning, not error

        # Check inventory age
        mtime = INVENTORY_PATH.stat().st_mtime
        age_hours = (datetime.now().timestamp() - mtime) / 3600

        if age_hours > 48:
            self.warnings.append(f"Inventory is {age_hours:.1f} hours old - consider running scanner")
        else:
            self.passed.append(f"Inventory is recent ({age_hours:.1f} hours old)")

        return True

    def check_registry_sync(self) -> bool:
        """Check if registry is in sync with filesystem"""
        print("\n🔍 Checking registry synchronization...")

        if not REGISTRY_PATH.exists():
            self.issues.append(f"Registry not found: {REGISTRY_PATH}")
            return False

        if not INVENTORY_PATH.exists():
            self.issues.append(f"Inventory not found: {INVENTORY_PATH}")
            return False

        self.passed.append("Registry and inventory files exist")

        # Check if sync script exists
        sync_script = REPO_ROOT / "RUNTIME" / "doc_id" / "SUB_DOC_ID" / "5_REGISTRY_DATA" / "sync_registries.py"
        if sync_script.exists():
            self.passed.append("Registry sync script exists")
        else:
            self.warnings.append("Registry sync script not found")

        return True

    def run_checks(self, check_type="all"):
        """Run specified health checks"""
        checks = {
            "tasks": self.check_scheduled_tasks,
            "hook": self.check_pre_commit_hook,
            "scan": self.check_scanner_health,
            "registry": self.check_registry_sync,
        }

        if check_type == "all":
            results = {name: func() for name, func in checks.items()}
        elif check_type in checks:
            results = {check_type: checks[check_type]()}
        else:
            print(f"❌ Invalid check type: {check_type}")
            print(f"Available: {', '.join(checks.keys())}, all")
            return False

        return all(results.values())

    def print_report(self):
        """Print health check report"""
        print("\n" + "=" * 60)
        print("DOC-ID AUTOMATION HEALTH REPORT")
        print("=" * 60)

        if self.passed:
            print(f"\n✅ PASSED ({len(self.passed)}):")
            for item in self.passed:
                print(f"   ✓ {item}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for item in self.warnings:
                print(f"   ! {item}")

        if self.issues:
            print(f"\n❌ ISSUES ({len(self.issues)}):")
            for item in self.issues:
                print(f"   ✗ {item}")

        print("\n" + "=" * 60)

        if not self.issues:
            print("✅ OVERALL: HEALTHY")
            return 0
        elif not self.warnings:
            print("⚠️  OVERALL: DEGRADED")
            return 1
        else:
            print("❌ OVERALL: UNHEALTHY")
            return 2

    def diagnose(self):
        """Run comprehensive diagnosis"""
        print("\n🔬 Running comprehensive diagnosis...")

        self.run_checks("all")

        # Additional diagnostic info
        print("\n📊 Additional Information:")
        print(f"   Repository Root: {REPO_ROOT}")
        print(f"   Registry Path: {REGISTRY_PATH}")
        print(f"   Inventory Path: {INVENTORY_PATH}")

        if INVENTORY_PATH.exists():
            print(f"   Inventory Size: {INVENTORY_PATH.stat().st_size:,} bytes")
            print(f"   Inventory Modified: {datetime.fromtimestamp(INVENTORY_PATH.stat().st_mtime)}")

        return self.print_report()


def main():
    parser = argparse.ArgumentParser(description="Validate DOC-ID automation health")
    parser.add_argument("--check", choices=["all", "tasks", "hook", "scan", "registry"],
                       default="all", help="Which component to check")
    parser.add_argument("--mode", choices=["diagnose", "report", "enforce"],
                       default="report", help="Execution mode")

    args = parser.parse_args()

    validator = AutomationHealthValidator()

    if args.mode == "diagnose":
        return validator.diagnose()
    else:
        validator.run_checks(args.check)
        return validator.print_report()


if __name__ == "__main__":
    sys.exit(main())
