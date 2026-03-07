#!/usr/bin/env python3
"""
Auto-start Monitoring
Implements WS1-005: Auto-start Monitoring on RUN_CREATED event

Watches orchestration.db for new runs and auto-launches monitoring UI.
"""

# DOC_ID: DOC-CORE-AUTOMATION-MONITORING-TRIGGER-001

import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Set


def get_latest_run(db_path: Path) -> Optional[str]:
    """Get the most recent run_id from orchestration.db"""
    if not db_path.exists():
        return None

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            """
            SELECT run_id FROM runs
            ORDER BY created_at DESC
            LIMIT 1
        """
        )
        row = cursor.fetchone()
        conn.close()

        return row[0] if row else None
    except Exception as e:
        print(f"[ERROR] Failed to query database: {e}", file=sys.stderr)
        return None


def trigger_monitoring(run_id: str, db_path: Path, auto_mode: bool = True) -> int:
    """Trigger monitoring UI"""
    print(f"[AUTO-TRIGGER] Launching monitoring UI for run: {run_id}")

    cmd = [sys.executable, "-m", "core.monitoring.dashboard"]

    if auto_mode:
        cmd.append("--auto")

    cmd.extend(["--run-id", run_id])
    cmd.extend(["--db", str(db_path)])

    try:
        # Launch in background/detached mode
        if sys.platform == "win32":
            # Windows: use CREATE_NEW_CONSOLE
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        else:
            # Unix: use nohup
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        print(f"[OK] Monitoring UI launched")
        log_execution(run_id, "launched")
        return 0

    except Exception as e:
        print(f"[ERROR] Failed to launch monitoring UI: {e}", file=sys.stderr)
        log_execution(run_id, "error", str(e))
        return 1


def log_execution(run_id: str, status: str, error: Optional[str] = None):
    """Log auto-trigger execution to JSONL"""
    log_file = Path("logs/monitoring_trigger.jsonl")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": time.time(),
        "run_id": run_id,
        "status": status,
        "error": error,
        "trigger": "auto",
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[WARN] Failed to log execution: {e}", file=sys.stderr)


def watch_mode(db_path: Path, interval: int = 3):
    """Watch for new runs in continuous mode"""
    print(f"[WATCH] Monitoring {db_path} for new runs (interval: {interval}s)")
    print("[WATCH] Press Ctrl+C to stop")

    seen_runs: Set[str] = set()

    # Get existing runs
    latest = get_latest_run(db_path)
    if latest:
        seen_runs.add(latest)
        print(f"[INFO] Existing run detected: {latest}")

    try:
        while True:
            latest = get_latest_run(db_path)

            if latest and latest not in seen_runs:
                print(f"\n[DETECTED] New run created: {latest}")

                result = trigger_monitoring(latest, db_path)

                if result == 0:
                    seen_runs.add(latest)
                else:
                    print(f"[ERROR] Auto-trigger failed, will retry on next check")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n[STOP] Watch mode stopped")
        return 0


def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Auto-start monitoring UI on new run creation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Watch mode (continuous)
  python -m core.automation.monitoring_trigger --watch

  # Custom database path
  python -m core.automation.monitoring_trigger --watch --db .state/custom.db

  # Custom interval
  python -m core.automation.monitoring_trigger --watch --interval 5
        """,
    )

    parser.add_argument(
        "--watch", action="store_true", help="Run in watch mode (continuous monitoring)"
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=Path(".state/orchestration.db"),
        help="Path to orchestration database (default: .state/orchestration.db)",
    )

    parser.add_argument(
        "--interval", type=int, default=3, help="Watch interval in seconds (default: 3)"
    )

    args = parser.parse_args()

    if args.watch:
        return watch_mode(args.db, args.interval)
    else:
        # One-shot mode
        latest = get_latest_run(args.db)
        if latest:
            print(f"[DETECTED] Latest run: {latest}")
            return trigger_monitoring(latest, args.db)
        else:
            print(f"[INFO] No runs found in database")
            return 0


if __name__ == "__main__":
    sys.exit(main())
