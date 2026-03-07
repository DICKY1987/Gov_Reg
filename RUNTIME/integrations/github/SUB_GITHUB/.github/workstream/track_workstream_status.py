# DOC_LINK: DOC-SCRIPT-SCRIPTS-TRACK-WORKSTREAM-STATUS-758
# DOC_LINK: DOC-SCRIPT-STATUS-TRACKER-2025-12-02
"""
Workstream Status Tracker - Automated Status Monitoring

Monitors and reports on workstream execution status.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Ensure imports work when executed as a script from repo root or other directories
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    )


class WorkstreamStatusTracker:
    def __init__(self, status_file="state/workstream_status.json"):
        self.status_file = Path(status_file)
        self.status = self.load_status()

    def load_status(self) -> Dict:
        """Load current status from file."""
        if self.status_file.exists():
            with open(self.status_file) as f:
                return json.load(f)
        return {}

    def save_status(self):
        """Save status to file."""
        self.status_file.parent.mkdir(exist_ok=True)
        with open(self.status_file, "w") as f:
            json.dump(self.status, f, indent=2)

    def update_status(self, ws_id: str, status: str, message: str = ""):
        """Update status for a workstream."""
        self.status[ws_id] = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.save_status()

    def get_status(self, ws_id: str) -> Dict:
        """Get status for a workstream."""
        return self.status.get(ws_id, {"status": "not_started"})

    def get_all_status(self) -> Dict:
        """Get status for all workstreams."""
        return self.status

    def generate_report(self, workstreams: List[Dict]) -> str:
        """Generate status report."""
        report = []
        report.append("=" * 80)
        report.append("📊 WORKSTREAM STATUS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        status_counts = {
            "not_started": 0,
            "in_progress": 0,
            "completed": 0,
            "blocked": 0,
            "failed": 0,
            "manual": 0,
        }

        for ws in workstreams:
            ws_status = self.get_status(ws["id"])
            status = ws_status.get("status", "not_started")
            status_counts[status] = status_counts.get(status, 0) + 1

            emoji = {
                "not_started": "⚪",
                "in_progress": "🔵",
                "completed": "✅",
                "blocked": "🔒",
                "failed": "❌",
                "manual": "⚠️",
            }.get(status, "❓")

            report.append(f"{emoji} {ws['name']}")
            report.append(f"   ID: {ws['id']}")
            report.append(f"   Status: {status}")
            if ws_status.get("message"):
                report.append(f"   Message: {ws_status['message']}")
            if ws_status.get("timestamp"):
                report.append(f"   Last updated: {ws_status['timestamp']}")
            report.append("")

        report.append("=" * 80)
        report.append("📈 SUMMARY")
        report.append("=" * 80)
        for status, count in status_counts.items():
            if count > 0:
                report.append(f"  {status.replace('_', ' ').title()}: {count}")
        report.append("=" * 80)

        return "\n".join(report)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Track workstream status")
    parser.add_argument(
        "--update",
        nargs=3,
        metavar=("WS_ID", "STATUS", "MESSAGE"),
        help="Update workstream status",
    )
    parser.add_argument("--report", action="store_true", help="Generate status report")
    parser.add_argument("--output", help="Output file for report")
    args = parser.parse_args()

    tracker = WorkstreamStatusTracker()

    if args.update:
        ws_id, status, message = args.update
        tracker.update_status(ws_id, status, message)
        print(f"✅ Updated {ws_id} to {status}")

    if args.report or args.output:
        # Load workstreams
        from scripts.execute_next_workstreams import WORKSTREAMS

        report = tracker.generate_report(WORKSTREAMS)

        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"✅ Report saved to {args.output}")
        else:
            print(report)


if __name__ == "__main__":
    main()
