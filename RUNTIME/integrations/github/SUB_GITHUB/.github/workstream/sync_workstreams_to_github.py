#!/usr/bin/env python3
"""
Sync workstreams to GitHub Project Manager
- Creates feature branch for all workstreams
- Commits each workstream separately
- Pushes to remote
- Generates workstream summary report
- NO STOPPING - Continues through all tasks even if errors occur
"""
import json
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).parent.parent
WORKSTREAMS_DIR = REPO_ROOT / "workstreams"
REPORTS_DIR = REPO_ROOT / "reports"
LOGS_DIR = REPO_ROOT / "logs"


class WorkstreamSyncEngine:
    """Syncs workstreams to GitHub with no-stop execution"""

    def __init__(self, feature_branch: str = None):
        self.feature_branch = (
            feature_branch
            or f"feature/ws-sync-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        self.errors: List[Dict[str, Any]] = []
        self.successes: List[Dict[str, Any]] = []
        self.summary: Dict[str, Any] = {
            "sync_timestamp": datetime.now().isoformat(),
            "feature_branch": self.feature_branch,
            "workstreams_processed": 0,
            "commits_created": 0,
            "errors_count": 0,
            "success_count": 0,
        }

    def run_git_command(self, args: List[str], cwd: Path = REPO_ROOT) -> Optional[str]:
        """Run git command and capture output"""
        try:
            result = subprocess.run(
                ["git"] + args, cwd=cwd, capture_output=True, text=True, check=False
            )
            if result.returncode != 0:
                return None
            return result.stdout.strip()
        except Exception as e:
            self.log_error(f"Git command failed: {' '.join(args)}", str(e))
            return None

    def log_error(self, context: str, error: str):
        """Log error but continue execution"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "error": error,
        }
        self.errors.append(error_entry)
        print(f"[X] ERROR [{context}]: {error}", file=sys.stderr)

    def log_success(self, context: str, details: str):
        """Log success"""
        success_entry = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "details": details,
        }
        self.successes.append(success_entry)
        print(f"[OK] SUCCESS [{context}]: {details}")

    def ensure_branch(self) -> bool:
        """Create and checkout feature branch"""
        print(f"\n[*] Creating feature branch: {self.feature_branch}")

        # Get current branch
        current_branch = self.run_git_command(["branch", "--show-current"])
        if not current_branch:
            self.log_error("Branch detection", "Could not detect current branch")
            return False

        print(f"[*] Current branch: {current_branch}")

        # Create new branch
        if not self.run_git_command(["checkout", "-b", self.feature_branch]):
            # Branch might exist, try to checkout
            if not self.run_git_command(["checkout", self.feature_branch]):
                self.log_error(
                    "Branch creation",
                    f"Failed to create/checkout {self.feature_branch}",
                )
                return False

        self.log_success("Branch ready", self.feature_branch)
        return True

    def load_workstream(self, ws_path: Path) -> Optional[Dict[str, Any]]:
        """Load workstream JSON file"""
        try:
            with open(ws_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            self.log_error(f"Load workstream {ws_path.name}", str(e))
            return None

    def commit_workstream(self, ws_path: Path, ws_data: Dict[str, Any]) -> bool:
        """Commit single workstream file"""
        ws_id = ws_data.get("id", ws_path.stem)

        # Add file
        if not self.run_git_command(["add", str(ws_path)]):
            self.log_error(f"Git add {ws_id}", "Failed to stage file")
            return False

        # Create commit
        commit_msg = f"sync: {ws_id}\n\n"
        commit_msg += f"Workstream: {ws_data.get('id', 'N/A')}\n"
        commit_msg += f"Doc ID: {ws_data.get('doc_id', 'N/A')}\n"
        commit_msg += f"Tool: {ws_data.get('tool', 'N/A')}\n"
        commit_msg += f"Gate: {ws_data.get('gate', 'N/A')}\n"

        if not self.run_git_command(["commit", "-m", commit_msg]):
            # Check if there's nothing to commit
            status = self.run_git_command(["status", "--porcelain", str(ws_path)])
            if not status:
                self.log_success(f"Commit {ws_id}", "No changes needed")
                return True
            self.log_error(f"Git commit {ws_id}", "Commit failed")
            return False

        self.log_success(f"Commit {ws_id}", "Committed successfully")
        self.summary["commits_created"] += 1
        return True

    def process_all_workstreams(self):
        """Process all workstream files"""
        print("\n[*] Processing workstreams...")

        ws_files = sorted(WORKSTREAMS_DIR.glob("ws-*.json"))
        print(f"Found {len(ws_files)} workstream files")

        for ws_path in ws_files:
            print(f"\n[*] Processing: {ws_path.name}")
            self.summary["workstreams_processed"] += 1

            # Load workstream
            ws_data = self.load_workstream(ws_path)
            if not ws_data:
                self.summary["errors_count"] += 1
                continue

            # Commit workstream
            if self.commit_workstream(ws_path, ws_data):
                self.summary["success_count"] += 1
            else:
                self.summary["errors_count"] += 1

    def push_to_remote(self) -> bool:
        """Push feature branch to remote"""
        print(f"\n[*] Pushing to remote: {self.feature_branch}")

        # Try to push
        result = self.run_git_command(["push", "-u", "origin", self.feature_branch])
        if result is None:
            # Try without -u flag
            result = self.run_git_command(["push", "origin", self.feature_branch])
            if result is None:
                self.log_error("Git push", "Failed to push to remote")
                return False

        self.log_success("Git push", f"Pushed {self.feature_branch} to origin")
        return True

    def generate_summary_report(self) -> Path:
        """Generate summary report from template"""
        REPORTS_DIR.mkdir(exist_ok=True)

        report_path = (
            REPORTS_DIR
            / f"workstream_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )

        # Build report content
        content = f"""# Workstream Sync Summary Report

**Generated**: {self.summary['sync_timestamp']}
**Feature Branch**: `{self.summary['feature_branch']}`

## Overview

- **Workstreams Processed**: {self.summary['workstreams_processed']}
- **Commits Created**: {self.summary['commits_created']}
- **Successful Operations**: {self.summary['success_count']}
- **Errors Encountered**: {self.summary['errors_count']}

## Execution Status

{'[OK] **All workstreams synced successfully**' if self.summary['errors_count'] == 0 else f"[WARN] **{self.summary['errors_count']} errors occurred during sync**"}

"""

        # Add successes
        if self.successes:
            content += "\n## [OK] Successful Operations\n\n"
            for success in self.successes:
                content += f"- **{success['context']}**: {success['details']}\n"

        # Add errors
        if self.errors:
            content += "\n## [X] Errors Encountered\n\n"
            for error in self.errors:
                content += f"### {error['context']}\n"
                content += f"```\n{error['error']}\n```\n\n"

        # Write report
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.log_success("Report generated", str(report_path))
        except Exception as e:
            self.log_error("Report generation", str(e))

        return report_path

    def run(self):
        """Execute full sync workflow - NO STOPPING"""
        print("=" * 80)
        print("[*] WORKSTREAM SYNC TO GITHUB - NO STOP MODE")
        print("=" * 80)

        try:
            # Ensure branch
            if not self.ensure_branch():
                print("\n⚠️ Branch creation failed, continuing anyway...")

            # Process all workstreams
            self.process_all_workstreams()

            # Push to remote
            self.push_to_remote()

            # Generate report
            report_path = self.generate_summary_report()

            print("\n" + "=" * 80)
            print("[DONE] SYNC COMPLETE")
            print("=" * 80)
            print(f"\n[*] Summary Report: {report_path}")
            print(f"[*] Feature Branch: {self.feature_branch}")
            print(f"[OK] Successes: {self.summary['success_count']}")
            print(f"[X] Errors: {self.summary['errors_count']}")

        except Exception as e:
            self.log_error("Fatal error in sync workflow", traceback.format_exc())
            print("\n⚠️ Fatal error occurred, but continuing to generate report...")
            self.generate_summary_report()

        # Exit with error code if errors occurred
        return 1 if self.errors else 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Sync workstreams to GitHub PM")
    parser.add_argument(
        "--branch", help="Feature branch name (auto-generated if not provided)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )

    args = parser.parse_args()

    if args.dry_run:
        print("[*] DRY RUN MODE - No changes will be made")
        ws_files = list(WORKSTREAMS_DIR.glob("ws-*.json"))
        print(f"Would process {len(ws_files)} workstream files:")
        for ws in ws_files:
            print(f"  - {ws.name}")
        return 0

    engine = WorkstreamSyncEngine(feature_branch=args.branch)
    return engine.run()


if __name__ == "__main__":
    sys.exit(main())
