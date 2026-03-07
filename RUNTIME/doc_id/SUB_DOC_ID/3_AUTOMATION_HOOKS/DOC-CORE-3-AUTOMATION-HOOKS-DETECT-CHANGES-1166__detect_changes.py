#!/usr/bin/env python3
# TRIGGER_ID: TRIGGER-HOOK-DETECT-CHANGES-001
"""
AUTO-001: Repo Change Detector
Detects files added/modified/deleted since last run
"""
DOC_ID: DOC-CORE-3-AUTOMATION-HOOKS-DETECT-CHANGES-1166

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def detect_changes(since: str, output: str):
    """Detect repository changes using git."""
    results = {
        "task_id": "AUTO-001",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "SUCCESS",
        "changes": {
            "added": [],
            "modified": [],
            "deleted": []
        },
        "summary": {}
    }

    try:
        # Get git diff
        if since:
            cmd = ["git", "diff", "--name-status", since, "HEAD"]
        else:
            cmd = ["git", "status", "--porcelain"]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')

            for line in lines:
                if not line:
                    continue

                parts = line.split(None, 1)
                if len(parts) >= 2:
                    status, filepath = parts[0], parts[1]

                    if status in ('A', '??'):
                        results["changes"]["added"].append(filepath)
                    elif status == 'M':
                        results["changes"]["modified"].append(filepath)
                    elif status == 'D':
                        results["changes"]["deleted"].append(filepath)

            results["summary"] = {
                "added": len(results["changes"]["added"]),
                "modified": len(results["changes"]["modified"]),
                "deleted": len(results["changes"]["deleted"]),
                "total": len(results["changes"]["added"]) + len(results["changes"]["modified"]) + len(results["changes"]["deleted"])
            }

        else:
            results["status"] = "FAILED"
            results["error"] = result.stderr

    except Exception as e:
        results["status"] = "FAILED"
        results["error"] = str(e)

    # Write output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    return 0 if results["status"] == "SUCCESS" else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect repository changes")
    parser.add_argument("--since", help="Git ref to compare against (commit SHA, branch, tag)")
    parser.add_argument("--output", required=True, help="Output JSON file path")

    args = parser.parse_args()
    sys.exit(detect_changes(args.since, args.output))
