#!/usr/bin/env python3
"""
ACMS Show Run - Run Status Viewer

Display detailed status information for ACMS runs.

Usage:
    python acms_show_run.py [RUN_ID] [OPTIONS]

Examples:
    # Show latest run
    python acms_show_run.py
    
    # Show specific run
    python acms_show_run.py 20251207001431_2E134BDB6F61
    
    # JSON output
    python acms_show_run.py --json
    
    # Show ledger entries
    python acms_show_run.py --ledger
    
    # Show all details
    python acms_show_run.py --all
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class RunViewer:
    """View ACMS run status and details"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.runs_dir = repo_root / ".acms_runs"

    def find_latest_run(self) -> Optional[str]:
        """Find the most recent run ID"""
        if not self.runs_dir.exists():
            return None

        runs = sorted(
            self.runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
        )

        return runs[0].name if runs else None

    def load_run_status(self, run_id: str) -> Optional[Dict]:
        """Load run_status.json for a run"""
        run_dir = self.runs_dir / run_id
        status_file = run_dir / "run_status.json"

        if not status_file.exists():
            return None

        try:
            with open(status_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading run status: {e}", file=sys.stderr)
            return None

    def load_ledger(self, run_id: str) -> List[Dict]:
        """Load ledger entries for a run"""
        run_dir = self.runs_dir / run_id
        ledger_file = run_dir / "run.ledger.jsonl"

        if not ledger_file.exists():
            return []

        entries = []
        try:
            with open(ledger_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))
        except Exception as e:
            print(f"Error loading ledger: {e}", file=sys.stderr)

        return entries

    def display_summary(self, status: Dict) -> None:
        """Display run summary in human-readable format"""
        print()
        print("=" * 70)
        print(f"ACMS RUN STATUS - {status['run_id']}")
        print("=" * 70)
        print()

        # Basic info
        print("📋 Basic Information")
        print(f"  Run ID:       {status['run_id']}")
        print(f"  Repository:   {status['repo_root']}")
        print(f"  Status:       {self._format_status(status['final_status'])}")
        print(f"  Started:      {self._format_time(status['started_at'])}")
        if status.get("completed_at"):
            print(f"  Completed:    {self._format_time(status['completed_at'])}")
            duration = self._calculate_duration(
                status["started_at"], status["completed_at"]
            )
            print(f"  Duration:     {duration}")
        print()

        # Metrics
        metrics = status.get("metrics", {})
        print("📊 Metrics")
        print(f"  Gaps Discovered:      {metrics.get('gaps_discovered', 0)}")
        print(f"  Gaps Resolved:        {metrics.get('gaps_resolved', 0)}")
        print(f"  Workstreams Created:  {metrics.get('workstreams_created', 0)}")
        print(f"  Tasks Executed:       {metrics.get('tasks_executed', 0)}")
        print(f"  Tasks Failed:         {metrics.get('tasks_failed', 0)}")
        if metrics.get("patches_applied"):
            print(f"  Patches Applied:      {metrics.get('patches_applied', 0)}")
        print()

        # State transitions
        transitions = status.get("state_transitions", [])
        if transitions:
            print("🔄 State Transitions")
            for i, trans in enumerate(transitions):
                state = trans["state"]
                time = self._format_time(trans["timestamp"])
                prev = trans.get("previous", "")

                if i == 0:
                    print(f"  {state.upper()}")
                else:
                    print(f"  {prev} → {state.upper()}")
                print(f"    {time}")
            print()

        # Configuration
        config = status.get("config", {})
        if config:
            print("⚙️  Configuration")
            print(
                f"  Triggers:        {'enabled' if config.get('triggers_enabled') else 'disabled'}"
            )
            print(
                f"  Resilience:      {'enabled' if config.get('enable_resilience') else 'disabled'}"
            )
            print(
                f"  Patch Ledger:    {'enabled' if config.get('enable_patch_ledger') else 'disabled'}"
            )
            print(f"  Max Concurrent:  {config.get('max_concurrent_tasks', 'N/A')}")
            print(f"  Timeout:         {config.get('timeout_seconds', 'N/A')}s")
            print()

        # Artifacts
        artifacts = status.get("artifacts", {})
        if artifacts:
            print("📄 Artifacts")
            for name, path in artifacts.items():
                if path:
                    exists = (Path(status["repo_root"]) / path).exists()
                    indicator = "✓" if exists else "✗"
                    print(f"  {indicator} {name}: {path}")
            print()

        # Error if failed
        if status.get("error"):
            print("❌ Error")
            print(f"  {status['error']}")
            print()

        print("=" * 70)
        print()

    def display_ledger(self, entries: List[Dict]) -> None:
        """Display ledger entries"""
        print()
        print("=" * 70)
        print(f"LEDGER ENTRIES ({len(entries)} total)")
        print("=" * 70)
        print()

        for entry in entries:
            state = entry.get("state", "unknown").ljust(15)
            event = entry.get("event", "unknown").ljust(30)
            time = self._format_time(entry.get("ts", ""))

            print(f"  {state} {event} {time}")

            # Show metadata if interesting
            meta = entry.get("meta", {})
            if meta and any(k not in ["message"] for k in meta.keys()):
                for key, value in meta.items():
                    if key != "message":
                        print(f"    {key}: {value}")

        print()
        print("=" * 70)
        print()

    def display_json(self, status: Dict) -> None:
        """Display run status as JSON"""
        print(json.dumps(status, indent=2))

    def _format_status(self, status: str) -> str:
        """Format status with color indicators"""
        indicators = {
            "success": "✅ SUCCESS",
            "failed": "❌ FAILED",
            "partial": "⚠️  PARTIAL",
            "cancelled": "🚫 CANCELLED",
        }
        return indicators.get(status, status.upper())

    def _format_time(self, timestamp: str) -> str:
        """Format ISO timestamp to readable string"""
        if not timestamp:
            return "N/A"

        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return timestamp

    def _calculate_duration(self, start: str, end: str) -> str:
        """Calculate duration between timestamps"""
        try:
            dt_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
            dt_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
            delta = dt_end - dt_start

            if delta.total_seconds() < 60:
                return f"{delta.total_seconds():.1f}s"
            elif delta.total_seconds() < 3600:
                return f"{delta.total_seconds() / 60:.1f}m"
            else:
                hours = delta.total_seconds() / 3600
                return f"{hours:.1f}h"
        except:
            return "N/A"


def main():
    parser = argparse.ArgumentParser(
        description="View ACMS run status and details",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  acms_show_run.py                              # Show latest run
  acms_show_run.py 20251207001431_2E134BDB6F61  # Show specific run
  acms_show_run.py --json                       # JSON output
  acms_show_run.py --ledger                     # Show ledger
  acms_show_run.py --all                        # Show everything
        """,
    )

    parser.add_argument("run_id", nargs="?", help="Run ID to display (default: latest)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--ledger", action="store_true", help="Show ledger entries")
    parser.add_argument(
        "--all", action="store_true", help="Show all details (summary + ledger)"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current directory)",
    )

    args = parser.parse_args()

    viewer = RunViewer(args.repo_root)

    # Find run ID
    run_id = args.run_id
    if not run_id:
        run_id = viewer.find_latest_run()
        if not run_id:
            print("❌ No runs found", file=sys.stderr)
            sys.exit(1)
        print(f"Using latest run: {run_id}\n")

    # Load status
    status = viewer.load_run_status(run_id)
    if not status:
        print(f"❌ Run status not found for: {run_id}", file=sys.stderr)
        sys.exit(1)

    # Display based on options
    if args.json:
        viewer.display_json(status)
    elif args.ledger or args.all:
        if not args.ledger:
            viewer.display_summary(status)

        ledger = viewer.load_ledger(run_id)
        viewer.display_ledger(ledger)
    else:
        viewer.display_summary(status)


if __name__ == "__main__":
    main()
