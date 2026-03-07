#!/usr/bin/env python3
# DOC_LINK: DOC-GUIDE-DOC-ID-DOC-ID-COVERAGE-TREND-450
"""
DOC_ID Coverage Trend Tracker

Tracks doc_id coverage over time for monitoring and trend analysis.

Usage:
    python scripts/doc_id_coverage_trend.py snapshot
    python scripts/doc_id_coverage_trend.py report

DOC_ID: DOC-GUIDE-DOC-ID-DOC-ID-COVERAGE-TREND-450
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, REPORTS_DIR

HISTORY_FILE = REPORTS_DIR / "coverage_history.jsonl"


def save_snapshot():
    """Save current coverage snapshot"""
    # Import scan function
    from validate_doc_id_coverage import scan_repository

    results = scan_repository()

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_files": results["total_eligible"],
        "files_with_docid": results["with_doc_id"],
        "coverage_percent": results["coverage_percent"],
    }

    # Append to history
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        json.dump(snapshot, f)
        f.write("\n")

    print(f"==> Snapshot saved: {snapshot['coverage_percent']}% coverage")
    print(f"   Files: {snapshot['files_with_docid']}/{snapshot['total_files']}")
    return snapshot


def load_history():
    """Load coverage history"""
    if not HISTORY_FILE.exists():
        return []

    history = []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                history.append(json.loads(line))

    return history


def generate_report():
    """Generate trend report"""
    history = load_history()

    if not history:
        print("No history data available. Run 'snapshot' first.")
        return

    print("=" * 60)
    print("DOC_ID Coverage Trend Report")
    print("=" * 60)

    print(f"\nSnapshots recorded: {len(history)}")
    print(f"Period: {history[0]['timestamp'][:10]} to {history[-1]['timestamp'][:10]}")

    # Current state
    latest = history[-1]
    print(f"\n==> Current Coverage:")
    print(f"   {latest['coverage_percent']}%")
    print(f"   {latest['files_with_docid']}/{latest['total_files']} files")

    # Trend analysis
    if len(history) > 1:
        first = history[0]
        delta_pct = latest["coverage_percent"] - first["coverage_percent"]
        delta_files = latest["files_with_docid"] - first["files_with_docid"]

        print(f"\n==> Change Since First Snapshot:")
        print(f"   Coverage: {delta_pct:+.2f}%")
        print(f"   Files:    {delta_files:+d}")

        # Recent trend (last 5 snapshots)
        if len(history) >= 5:
            recent = history[-5:]
            recent_delta = latest["coverage_percent"] - recent[0]["coverage_percent"]
            print(f"\n==> Recent Trend (last 5 snapshots):")
            print(f"   {recent_delta:+.2f}%")

    # Milestones
    milestones = [90, 95, 100]
    achieved = [m for m in milestones if latest["coverage_percent"] >= m]

    if achieved:
        print(f"\n==> Milestones Achieved:")
        for m in achieved:
            print(f"   ✓ {m}% coverage")

    remaining = [m for m in milestones if m not in achieved]
    if remaining:
        next_milestone = remaining[0]
        files_needed = int(
            (next_milestone - latest["coverage_percent"]) / 100 * latest["total_files"]
        )
        print(f"\n==> Next Milestone:")
        print(f"   {next_milestone}% coverage")
        print(f"   ~{files_needed} more files needed")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Track doc_id coverage trends")
    parser.add_argument(
        "action", choices=["snapshot", "report"], help="Action to perform"
    )

    args = parser.parse_args()

    if args.action == "snapshot":
        save_snapshot()
    elif args.action == "report":
        generate_report()


if __name__ == "__main__":
    main()
